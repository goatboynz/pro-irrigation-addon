@echo off
REM Pro-Irrigation v2 - GitHub Setup Script for Windows
REM This script helps you quickly set up your repository on GitHub

setlocal enabledelayedexpansion

echo ============================================================
echo Pro-Irrigation v2 - GitHub Setup Helper
echo ============================================================
echo.

REM Check if git is installed
where git >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Git is not installed. Please install Git first.
    echo Visit: https://git-scm.com/downloads
    pause
    exit /b 1
)

echo Git is installed [OK]
echo.

REM Check if we're in a git repository
if not exist ".git" (
    echo Initializing Git repository...
    git init
    echo Git repository initialized [OK]
) else (
    echo Git repository already exists [OK]
)

echo.
echo ============================================================
echo GitHub Repository Setup
echo ============================================================
echo.
echo Before continuing, please:
echo 1. Create a new repository on GitHub
echo 2. Name it: pro-irrigation-addon
echo 3. Make it PUBLIC (required for Home Assistant^)
echo 4. Do NOT initialize with README
echo.
set /p confirm="Have you created the GitHub repository? (y/n): "

if /i not "%confirm%"=="y" (
    echo Please create the repository first, then run this script again.
    pause
    exit /b 1
)

echo.
set /p github_username="Enter your GitHub username: "

if "%github_username%"=="" (
    echo ERROR: GitHub username cannot be empty
    pause
    exit /b 1
)

echo.
echo Setting up remote repository...

REM Check if remote already exists
git remote | findstr "origin" >nul 2>nul
if %errorlevel% equ 0 (
    echo Remote 'origin' already exists. Updating URL...
    git remote set-url origin "https://github.com/%github_username%/pro-irrigation-addon.git"
) else (
    git remote add origin "https://github.com/%github_username%/pro-irrigation-addon.git"
)

echo Remote repository configured [OK]
echo.

REM Check if there are any commits
git rev-parse HEAD >nul 2>nul
if %errorlevel% neq 0 (
    echo Creating initial commit...
    git add .
    git commit -m "Initial commit - Pro-Irrigation v2.0.0"
    echo Initial commit created [OK]
) else (
    echo Commits already exist [OK]
)

echo.
echo ============================================================
echo Ready to Push
echo ============================================================
echo.
echo Your repository is configured:
echo   Remote: https://github.com/%github_username%/pro-irrigation-addon.git
echo.
set /p push="Push to GitHub now? (y/n): "

if /i "%push%"=="y" (
    echo.
    echo Pushing to GitHub...
    git branch -M main
    git push -u origin main
    echo.
    echo ============================================================
    echo Success!
    echo ============================================================
    echo.
    echo Your add-on is now on GitHub!
    echo.
    echo Next steps:
    echo 1. Add icon.png and logo.png images to your repository
    echo 2. Visit: https://github.com/%github_username%/pro-irrigation-addon
    echo 3. Create a release (optional but recommended^)
    echo 4. Add to Home Assistant:
    echo    https://github.com/%github_username%/pro-irrigation-addon
    echo.
    echo See INSTALL.md for installation instructions
    echo See GITHUB_SETUP.md for detailed GitHub setup guide
    echo.
) else (
    echo.
    echo Skipped push. You can push manually later with:
    echo   git push -u origin main
    echo.
)

echo ============================================================
echo Setup Complete!
echo ============================================================
echo.
pause
