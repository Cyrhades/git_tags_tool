@echo off
title Git Tag Manager
setlocal enabledelayedexpansion

:: Positionnement dans le dossier du script
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo ===================================================
echo           Lancement de Git Tag Manager
echo ===================================================

:: Détection de l'environnement virtuel s'il existe
if exist "%SCRIPT_DIR%.venv\Scripts\python.exe" (
    echo [INFO] Utilisation de l'environnement virtuel .venv...
    set "PYTHON_EXE=%SCRIPT_DIR%.venv\Scripts\python.exe"
) else (
    echo [INFO] Utilisation du Python du systeme...
    set "PYTHON_EXE=python"
)

:: Lancement de l'application avec passage des arguments éventuels
"%PYTHON_EXE%" "%SCRIPT_DIR%main.py" %*

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERREUR] Une erreur s'est produite lors du lancement de l'application.
    pause
)
