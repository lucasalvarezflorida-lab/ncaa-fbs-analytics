@echo off
rem Friday publish-time pull (pipeline review item A5): re-pull CFBD lines,
rem append the line ledger (lines_history.jsonl), write card_data_week{N}.json
rem for the first unplayed week. Deck regeneration stays manual
rem (make_episode_deck.py is authored per episode).
cd /d "%~dp0"
echo. >> refresh_log.txt
echo ==== publish pull %date% %time% ==== >> refresh_log.txt
rem Full python path: LibreOffice's dir on PATH can shadow python.exe.
"C:\Users\lucas\AppData\Local\Python\pythoncore-3.14-64\python.exe" edge_report.py --week auto --view ml --publish >> refresh_log.txt 2>&1
echo ==== publish done %date% %time% (exit %errorlevel%) ==== >> refresh_log.txt
