@echo off
echo Starting build process...

REM Kill any running Python processes
taskkill /F /IM python.exe 2>nul
taskkill /F /IM pythonw.exe 2>nul

REM Clean up previous build directories and cache
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__
if exist script\__pycache__ rmdir /s /q script\__pycache__

REM Initialize conda
call "C:\Users\%USERNAME%\anaconda3\Scripts\activate.bat"

REM Remove existing environment if it exists
call conda env remove -n venv_modern -y

REM Create fresh environment
echo Creating conda environment...
call conda create -n venv_modern python=3.11.5 -y
call conda activate venv_modern

REM Upgrade PyQt5 and sip
pip install --upgrade pyqt5 sip

REM Install requirements
pip install -r requirements.txt

REM Verify pyinstaller installation
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller==6.11.0
)

REM Build with PyInstaller
echo Building with PyInstaller...
python -m PyInstaller simple.spec

REM Check if build was successful
if not exist "dist\modern_analytics\modern_analytics.exe" (
    echo Failed to create executable. Check the build logs for errors.
    pause
    exit /b 1
)

REM Restructure dist folder
if exist "dist\modern_analytics\script" (
    echo Restructuring dist folder...
    
    REM Move all files from nested script folder to parent directory
    move "dist\modern_analytics\script\*" "dist\modern_analytics\"
    
    REM Remove the now-empty script folder
    rmdir "dist\modern_analytics\script"
)

REM Copy resources directory with PNG files
if exist "dist\modern_analytics" (
    echo Copying resources...
    xcopy /E /I /Y "resources" "dist\modern_analytics\resources"
)

REM Copy specific resource files
echo Copying resource files...
xcopy /E /I /Y "script\resource_settings\qss" "dist\modern_analytics\resource_settings\qss"
xcopy /E /I /Y "script\resource_login" "dist\modern_analytics\resource_login"
xcopy /E /I /Y "script\config" "dist\modern_analytics\config"

REM Check if NSIS is installed
where makensis >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Installing NSIS...
    winget install NSIS.NSIS
)

REM Create installer using NSIS
echo Creating installer...
"C:\Program Files (x86)\NSIS\makensis.exe" /V4 installer.nsi

echo Build process complete.
if exist "modern_analytics_setup.exe" (
    echo Successfully created installer: modern_analytics_setup.exe
) else (
    echo Failed to create installer. Check the NSIS logs for errors.
)

pause
