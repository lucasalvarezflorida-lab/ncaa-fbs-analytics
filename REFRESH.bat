@echo off
rem One-click refresh for NCAA_FBS_Teams: rosters + portal + FPI.
rem Launched by the REFRESH button in the workbook (which closes the workbook
rem first), or run directly with the workbook closed.
cd /d "%~dp0"
title NCAA FBS refresh
echo Refreshing rosters, portal feed, and FPI sheet...
python refresh_all.py --wait-for-unlock
if errorlevel 1 (
    echo.
    echo REFRESH FAILED - see messages above.
    pause
    exit /b 1
)
echo Reopening workbook...
if exist "NCAA_FBS_Teams.xlsm" (start "" "NCAA_FBS_Teams.xlsm") else (start "" "NCAA_FBS_Teams.xlsx")
exit /b 0
