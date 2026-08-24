"""Push the episode deck to the shared Google Slides file — no browser.

Replaces the CONTENTS of the stable Slides file in place via the Drive API
(files.update with pptx->Slides conversion). The file ID — and therefore the
URL Corey has — never changes; sharing is untouched. This retires the manual
upload -> Import slides -> delete-old-slides recipe.

Usage:
    python push_deck.py                     # push the default episode pptx
    python push_deck.py --pptx decks\\X.pptx  [--file-id <driveFileId>]

One-time setup (needs Lucas, ~10 min):
    1. console.cloud.google.com -> create project (e.g. "ncaa-deck-push").
    2. APIs & Services -> Library -> enable "Google Drive API".
    3. OAuth consent screen -> External -> add yourself as a test user.
    4. Credentials -> Create credentials -> OAuth client ID -> Desktop app;
       download the JSON as drive_oauth_client.json into this folder.
    5. Run this script once: a browser opens for consent (the "unverified
       app" warning is expected for a personal script - Advanced -> continue).
       The token is cached in drive_token.json; later runs are headless.

drive_oauth_client.json and drive_token.json are gitignored - NEVER commit.

Caveats: replacing content re-renders every slide, so comment ANCHORS on old
slides can detach (comments stay on the file) - identical behavior to the old
import-and-delete method. Fonts/layout convert the same way Import slides did.
"""

import argparse
import json
import os
import ssl
import sys
import urllib.request

import certifi

HERE = os.path.dirname(os.path.abspath(__file__))
CLIENT_FILE = os.path.join(HERE, "drive_oauth_client.json")
TOKEN_FILE = os.path.join(HERE, "drive_token.json")
SCOPES = ["https://www.googleapis.com/auth/drive"]

# The stable Ep deck Slides file (shared with Corey as commenter).
STABLE_FILE_ID = "14G1HYYFIyKVG3JDPdtflzUU-3FGYulhbPsr7iThMJNg"
DEFAULT_PPTX = os.path.join(HERE, "decks", "2026_Week0_Episode1.pptx")

PPTX_MIME = ("application/vnd.openxmlformats-officedocument"
             ".presentationml.presentation")
SLIDES_MIME = "application/vnd.google-apps.presentation"


def get_credentials():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if creds and creds.valid:
        return creds
    refreshed = False
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            refreshed = True
        except Exception:
            # Testing-status refresh tokens die after ~7 days - fall through
            # to a fresh browser consent instead of crashing.
            pass
    if not refreshed:
        if not os.path.exists(CLIENT_FILE):
            sys.exit(
                "drive_oauth_client.json not found.\n"
                "Do the one-time setup in this file's docstring (Google "
                "Cloud console -> OAuth Desktop client -> download JSON "
                f"to {CLIENT_FILE}), then rerun."
            )
        from google_auth_oauthlib.flow import InstalledAppFlow
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        f.write(creds.to_json())
    return creds


def push(pptx_path, file_id, creds):
    with open(pptx_path, "rb") as f:
        pptx = f.read()
    meta = json.dumps({"mimeType": SLIDES_MIME}).encode("utf-8")
    boundary = b"deckpush_boundary_7f3a91"
    body = (
        b"--" + boundary + b"\r\n"
        b"Content-Type: application/json; charset=UTF-8\r\n\r\n"
        + meta + b"\r\n"
        b"--" + boundary + b"\r\n"
        b"Content-Type: " + PPTX_MIME.encode() + b"\r\n\r\n"
        + pptx + b"\r\n"
        b"--" + boundary + b"--"
    )
    url = (f"https://www.googleapis.com/upload/drive/v3/files/{file_id}"
           "?uploadType=multipart&fields=id,name,modifiedTime,webViewLink")
    req = urllib.request.Request(url, data=body, method="PATCH", headers={
        "Authorization": f"Bearer {creds.token}",
        "Content-Type": f"multipart/related; boundary="
                        f"{boundary.decode()}",
    })
    ctx = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(req, context=ctx) as resp:
        return json.load(resp)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pptx", default=DEFAULT_PPTX)
    ap.add_argument("--file-id", default=STABLE_FILE_ID)
    args = ap.parse_args()
    if not os.path.exists(args.pptx):
        sys.exit(f"pptx not found: {args.pptx}")
    creds = get_credentials()
    size_kb = os.path.getsize(args.pptx) / 1024
    print(f"pushing {os.path.basename(args.pptx)} ({size_kb:.0f} KB) "
          f"-> Slides file {args.file_id} (contents replaced in place)")
    try:
        info = push(args.pptx, args.file_id, creds)
    except urllib.error.HTTPError as e:
        sys.exit(f"Drive API error {e.code}: {e.read().decode()[:500]}")
    print(f"done: '{info.get('name')}' updated {info.get('modifiedTime')}")
    print(info.get("webViewLink", ""))


if __name__ == "__main__":
    main()
