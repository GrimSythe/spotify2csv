@echo off
setlocal
cd /d "%~dp0"

set "SPOTIFY2CSV_PYTHON=.venv\Scripts\python.exe"

if not exist "%SPOTIFY2CSV_PYTHON%" (
    echo Setting up Spotify2CSV for the first time...
    where py >nul 2>nul
    if errorlevel 1 (
        echo.
        echo Python 3.9 or newer was not found. Install Python from python.org first.
        goto :failed
    )
    py -m venv .venv
    if errorlevel 1 goto :failed
)

"%SPOTIFY2CSV_PYTHON%" -c "import spotify2csv" >nul 2>nul
if errorlevel 1 (
    echo Installing Spotify2CSV and its dependencies...
    "%SPOTIFY2CSV_PYTHON%" -m pip install --disable-pip-version-check -e .
    if errorlevel 1 goto :failed
)

"%SPOTIFY2CSV_PYTHON%" -m spotify2csv %*
if errorlevel 1 goto :failed

if not "%~1"=="" exit /b 0

echo.
pause
exit /b 0

:failed
echo.
echo Spotify2CSV could not start. Review the message above for details.
pause
exit /b 1
