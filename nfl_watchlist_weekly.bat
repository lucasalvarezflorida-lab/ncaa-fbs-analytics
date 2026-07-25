@echo off
rem Weekly NFL watch-list run - Windows Task Scheduler, Tuesdays 8:00 AM
rem in season (all games incl. MNF are final and nflverse has updated).
rem Grades the four pre-registered rules (NFL_WATCHLIST_2026_PREREG.md)
rem vs closing lines and refreshes the Watch List 2026 tab in
rem NFL_Postmortem.xlsx. Logs to market-postmortem\nfl_watchlist_run.log.
rem Full python path: LibreOffice's dir on PATH can shadow python.exe.
cd /d "%~dp0market-postmortem"
echo. >> nfl_watchlist_run.log
echo ==== scheduled run %date% %time% ==== >> nfl_watchlist_run.log
"C:\Users\lucas\AppData\Local\Python\pythoncore-3.14-64\python.exe" nfl_watchlist.py >> nfl_watchlist_run.log 2>&1
echo ==== done %date% %time% (exit %errorlevel%) ==== >> nfl_watchlist_run.log
