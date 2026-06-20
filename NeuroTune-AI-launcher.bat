@echo off
title NeuroTune AI
color 0A

echo ============================================
echo         NeuroTune AI - Starting...
echo ============================================

:: Vérifier Node.js
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Node.js manquant - Installation requise
    pause
    exit
)

:: Installer dépendances (première fois seulement)
if not exist "node_modules" (
    echo Installation des dependances...
    call pnpm install
)

:: Démarrer tout
start "NeuroTune API" cmd /c "cd apps\api && pnpm dev"
timeout /t 3 /nobreak >nul
start "NeuroTune Frontend" cmd /c "cd apps\web && pnpm dev"
timeout /t 5 /nobreak >nul
start http://localhost:3000

echo.
echo NeuroTune AI est lance !
echo Frontend : http://localhost:3000
echo.
pause