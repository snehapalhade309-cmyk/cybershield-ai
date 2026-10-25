@echo off
title CyberShield AI - GitHub Upload Assistant
cd /d "%~dp0"

echo ========================================================
echo        CyberShield AI - GitHub Repository Uploader
echo ========================================================
echo.
echo Current Directory: %CD%
echo.

git status >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Initializing Git repository...
    git init
    git branch -M main
)

echo Checking git status...
git add .
git commit -m "CyberShield AI full-stack platform" >nul 2>&1

echo.
echo Please paste your GitHub Repository URL below:
echo (Example: https://github.com/your-username/cybershield-ai.git)
echo.
set /p REPO_URL="Repository URL: "

if "%REPO_URL%"=="" (
    echo.
    echo [ERROR] No URL entered. Please run the script again and paste your GitHub repository URL.
    pause
    exit /b
)

echo.
echo Configuring remote repository...
git remote remove origin >nul 2>&1
git remote add origin %REPO_URL%

echo.
echo Uploading files to GitHub branch 'main'...
git push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================
    echo   SUCCESS! All files have been uploaded to GitHub!
    echo ========================================================
) else (
    echo.
    echo [NOTE] If GitHub asked you to sign in, complete the login in your browser window.
    echo If the repository already has conflicting files, trying forced push...
    git push -u origin main --force
)

echo.
pause
