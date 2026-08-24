@echo off
rem Sunday open pull (Ep2 pivot, 2026-08-24): Circa hangs CFB openers Sundays
rem 11am PT / 2pm ET and DraftKings reposts the week's board through the
rem afternoon -- this 6pm ET pull records first-seen DK/Bovada lines as close
rem to the true market open as CFBD allows, so open->close CLV is honest.
rem Same command as publish_friday.bat: --publish implies --refresh, appends
rem lines_history.jsonl, writes card_data_week{N}.json. Deck regen stays manual.
cd /d "%~dp0"
echo. >> refresh_log.txt
echo ==== sunday open pull %date% %time% ==== >> refresh_log.txt
rem Full python path: LibreOffice's dir on PATH can shadow python.exe.
"C:\Users\lucas\AppData\Local\Python\pythoncore-3.14-64\python.exe" edge_report.py --week auto --view ml --publish >> refresh_log.txt 2>&1
echo ==== sunday open pull done %date% %time% (exit %errorlevel%) ==== >> refresh_log.txt
