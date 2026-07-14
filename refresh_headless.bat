@echo off
rem Headless weekly refresh - run by Windows Task Scheduler (Tuesdays in-season).
rem Same pipeline as the REFRESH button, but logs to refresh_log.txt and does
rem not reopen the workbook. Waits if the workbook is open in Excel.
cd /d "%~dp0"
echo. >> refresh_log.txt
echo ==== scheduled refresh %date% %time% ==== >> refresh_log.txt
python refresh_all.py --wait-for-unlock >> refresh_log.txt 2>&1
echo ==== done %date% %time% (exit %errorlevel%) ==== >> refresh_log.txt
