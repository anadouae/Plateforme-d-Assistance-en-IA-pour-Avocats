@echo off
title Tunnel Adminer LexHub (Confidentiel) - NE PAS FERMER

echo =====================================================================
echo   Lancement du Tunnel SSH Securise - Base de Donnees LexHub (Adminer)
echo =====================================================================
echo.

set SCRIPT_PATH=
if exist "%~dp0open_adminer_tunnel.py" set SCRIPT_PATH="%~dp0open_adminer_tunnel.py"
if "%SCRIPT_PATH%"=="" if exist "%~dp0scripts\open_adminer_tunnel.py" set SCRIPT_PATH="%~dp0scripts\open_adminer_tunnel.py"
if "%SCRIPT_PATH%"=="" if exist "C:\Users\daurinia\Desktop\Avocat-AI-Assistance\scripts\open_adminer_tunnel.py" set SCRIPT_PATH="C:\Users\daurinia\Desktop\Avocat-AI-Assistance\scripts\open_adminer_tunnel.py"
if "%SCRIPT_PATH%"=="" if exist "C:\Users\daurinia\Desktop\Pack_Acces_Base_Adminer_LexHub\open_adminer_tunnel.py" set SCRIPT_PATH="C:\Users\daurinia\Desktop\Pack_Acces_Base_Adminer_LexHub\open_adminer_tunnel.py"
if "%SCRIPT_PATH%"=="" if exist "C:\Users\daurinia\Desktop\open_adminer_tunnel.py" set SCRIPT_PATH="C:\Users\daurinia\Desktop\open_adminer_tunnel.py"

if "%SCRIPT_PATH%"=="" (
    echo [ERREUR] Le script open_adminer_tunnel.py est introuvable.
    echo Assurez-vous que open_adminer_tunnel.py est dans le meme dossier.
    pause
    exit /b 1
)

python -u %SCRIPT_PATH%

echo.
echo Tunnel arrete. Port 8088 libere.
pause
