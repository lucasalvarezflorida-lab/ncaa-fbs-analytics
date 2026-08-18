@echo off
rem One-time pre-Week-0 OurLads depth pass - run by Windows Task Scheduler
rem on Aug 25, 2026 at 6:30 AM (before the 7:30 weekly refresh). Scrapes
rem fresh depth charts, rebuilds the workbook, regenerates the decks, and
rem commits the tracked artifacts. Logs to refresh_log.txt.
cd /d "%~dp0"
set PY="C:\Users\lucas\AppData\Local\Python\pythoncore-3.14-64\python.exe"
echo. >> refresh_log.txt
echo ==== OurLads week0 pass %date% %time% ==== >> refresh_log.txt
%PY% fetch_ourlads_depth.py >> refresh_log.txt 2>&1
if errorlevel 1 (
    echo OURLADS SCRAPE FAILED - aborting pass >> refresh_log.txt
    exit /b 1
)
%PY% refresh_all.py --import-only --wait-for-unlock >> refresh_log.txt 2>&1
%PY% make_sim_decks.py >> refresh_log.txt 2>&1
rem Commit only tracked artifacts; ourlads_depth.json + conference decks are gitignored.
git add NCAA_FBS_Teams.xlsm decks/2026_Season_Sim_Overview.pptx >> refresh_log.txt 2>&1
git commit -m "Final pre-Week-0 OurLads depth pass (scheduled, Aug 25)" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" >> refresh_log.txt 2>&1
git push >> refresh_log.txt 2>&1
echo ==== week0 pass done %date% %time% (exit %errorlevel%) ==== >> refresh_log.txt
