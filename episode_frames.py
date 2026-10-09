"""episode_frames.py - Corey's score slides straight off the published episode (Lucas 10/9).

Corey's worst case for his score calls is "re-watch the video". This does that without watching: pull the
episode from the Man vs Machine channel (yt-dlp, video only, 720p - about 80 MB for two hours), read its
chapters (one per game), and for every game chapter tile the LAST SIX MINUTES at one frame every 30 s into
a contact sheet. Corey's score slide (two team halves, his winner's score in green) sits about two minutes
before the chapter ends, right before the machine's number slide. The sheets are READ (by eye / by Claude);
then --cut takes full-resolution receipt frames at the slide times and the reads go in corey_calls.json
next to them. Nothing here reads numbers off pixels.

    python episode_frames.py --video 8QfQpPEUDAM                       # download + one sheet per game chapter
    python episode_frames.py --latest                                   # newest full episode on the channel
    python episode_frames.py --video 8QfQpPEUDAM --cut 50:55,67:18,...  # full-res frames at those times (keeps the mp4 only if --keep)
    python episode_frames.py --video 8QfQpPEUDAM --sheet-minutes 8 --sheet-step 20

Output: decks/video/frames/<id>/sheet_NN.jpg (+ corey_NN_mmm-ss.jpg from --cut) + index.json. The mp4 is
deleted after the cut unless --keep (re-downloadable). decks/video/ is gitignored. Downloads only the show's
own channel (Lucas's and Corey's videos). Proven 10/9 on the Week 5 episode: all five calls matched the tracker.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIDEO_DIR = HERE / "decks" / "video"
CHANNEL = "https://www.youtube.com/@manvsmachinecollegefootball/videos"
GAME = re.compile(r"\b(at|vs\.?|versus)\b", re.I)
TIMESTAMP = r"drawtext=text='%{pts\:hms}':x=8:y=8:fontsize=22:fontcolor=yellow:box=1:boxcolor=black@0.6"


def ffmpeg() -> str:
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def video_path(video_id: str) -> Path | None:
    hits = sorted(VIDEO_DIR.glob(f"{video_id}.*"))
    hits = [h for h in hits if h.suffix not in (".json",)]
    return hits[0] if hits else None


def download(video_id: str) -> tuple[Path, dict]:
    import yt_dlp
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    info_file = VIDEO_DIR / f"{video_id}.info.json"
    existing = video_path(video_id)
    if existing and info_file.exists():
        return existing, json.loads(info_file.read_text(encoding="utf-8"))
    opts = dict(format="bv*[height<=720][ext=mp4]/bv*[height<=720]/b[height<=720]/bv*/b",
                outtmpl=str(VIDEO_DIR / "%(id)s.%(ext)s"), quiet=True, no_warnings=True, noprogress=True,
                ffmpeg_location=str(Path(ffmpeg()).parent), noplaylist=True)
    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=True)
        path = Path(y.prepare_filename(info))
    meta = dict(id=info["id"], title=info.get("title"), duration=info.get("duration"), upload_date=info.get("upload_date"),
                chapters=[dict(title=c.get("title"), start=c.get("start_time"), end=c.get("end_time")) for c in (info.get("chapters") or [])])
    info_file.write_text(json.dumps(meta, indent=1), encoding="utf-8")
    return path, meta


def latest_video_id() -> str:
    import yt_dlp
    with yt_dlp.YoutubeDL(dict(quiet=True, extract_flat=True, playlistend=6, no_warnings=True)) as y:
        info = y.extract_info(CHANNEL, download=False)
    vids = [e for e in info.get("entries", []) if (e.get("duration") or 0) > 3600]   # a full episode, not a recap short
    if not vids:
        raise SystemExit("no full-length episode found on the channel")
    return vids[0]["id"]


def game_chapters(meta: dict) -> list[dict]:
    games = [c for c in meta["chapters"] if GAME.search(c["title"] or "")]
    return games or meta["chapters"]


def sheets(path: Path, meta: dict, minutes: int = 6, step: int = 30) -> list[dict]:
    out_dir = VIDEO_DIR / "frames" / meta["id"]; out_dir.mkdir(parents=True, exist_ok=True)
    n_frames = minutes * 60 // step
    cols = 4; rows = -(-n_frames // cols)
    index = []
    for n, c in enumerate(game_chapters(meta), 1):
        end = c["end"] or meta["duration"]; start = max(c["start"], end - minutes * 60)
        f = out_dir / f"sheet_{n:02d}.jpg"
        vf = f"fps=1/{step},scale=400:-1,{TIMESTAMP},tile={cols}x{rows}"
        subprocess.run([ffmpeg(), "-y", "-loglevel", "error", "-ss", f"{start:.2f}", "-t", str(end - start), "-i", str(path), "-vf", vf, "-frames:v", "1", str(f)],
                       check=True, capture_output=True)
        mm, ss = divmod(int(start), 60)
        index.append(dict(n=n, game=c["title"], sheet=f.name, sheet_starts_at=f"{mm}:{ss:02d}", step=step,
                          note="tile timestamps are offsets from sheet_starts_at; Corey's score slide is usually ~2 min before the chapter end"))
        print(f"  {n:02d} {c['title']:40s} sheet from {mm:3d}:{ss:02d}  -> {f.name}")
    (out_dir / "index.json").write_text(json.dumps(dict(video=meta["id"], title=meta["title"], sheets=index), indent=1), encoding="utf-8")
    return index


def cut(path: Path, meta: dict, times: list[str]) -> list[str]:
    out_dir = VIDEO_DIR / "frames" / meta["id"]; out_dir.mkdir(parents=True, exist_ok=True)
    files = []
    for n, ts in enumerate(times, 1):
        parts = [int(x) for x in ts.split(":")]
        t = parts[0] * 60 + parts[1] if len(parts) == 2 else parts[0] * 3600 + parts[1] * 60 + parts[2]
        f = out_dir / f"corey_{n:02d}_{t // 60:03d}-{t % 60:02d}.jpg"
        subprocess.run([ffmpeg(), "-y", "-loglevel", "error", "-ss", str(t), "-i", str(path), "-frames:v", "1", "-q:v", "2", str(f)], check=True, capture_output=True)
        files.append(f.name); print(f"  frame at {t // 60}:{t % 60:02d} -> {f.name}")
    calls = out_dir / "corey_calls.json"
    if not calls.exists():
        calls.write_text(json.dumps(dict(video=meta["id"], title=meta["title"], week=None, read_on=None,
                                         calls=[dict(game=None, mmss=ts, away=None, away_pts=None, home=None, home_pts=None, corey_winner=None, frame=fn) for ts, fn in zip(times, files)]), indent=1), encoding="utf-8")
        print(f"  template -> {calls.name} (fill the reads; score_tracker.py takes them as the man calls)")
    return files


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", help="YouTube video id")
    ap.add_argument("--latest", action="store_true")
    ap.add_argument("--sheet-minutes", type=int, default=6)
    ap.add_argument("--sheet-step", type=int, default=30)
    ap.add_argument("--cut", help="comma list of mm:ss (or h:mm:ss) times for full-res frames")
    ap.add_argument("--keep", action="store_true", help="keep the downloaded video")
    a = ap.parse_args()
    vid = a.video or (latest_video_id() if a.latest else None)
    if not vid:
        raise SystemExit("--video <id> or --latest")
    path, meta = download(vid)
    print(f"{meta['title']} ({meta['duration']}s, {len(meta['chapters'])} chapters) -> {path.name} {path.stat().st_size // 1048576} MB")
    if a.cut:
        cut(path, meta, [x.strip() for x in a.cut.split(",") if x.strip()])
    else:
        sheets(path, meta, a.sheet_minutes, a.sheet_step)
    if not a.keep:
        path.unlink(missing_ok=True); print("video deleted (frames kept); --keep to retain it")
