@echo off
chcp 65001 >nul
title Tunnel Adminer LexHub (Confidentiel) - NE PAS FERMER

echo =====================================================================
echo   Lancement du Tunnel SSH Sécurisé - Base de Données LexHub (Adminer)
echo =====================================================================
echo.

REM 1. Détection du script Python
set SCRIPT_PATH=""
if exist "%~dp0open_adminer_tunnel.py" (
    set SCRIPT_PATH="%~dp0open_adminer_tunnel.py"
) else if exist "%~dp0scripts\open_adminer_tunnel.py" (
    set SCRIPT_PATH="%~dp0scripts\open_adminer_tunnel.py"
) else (
    echo [ERREUR] open_adminer_tunnel.py introuvable !
    echo Veuillez vous assurer que le fichier open_adminer_tunnel.py se trouve
    echo dans le même dossier que ce fichier Ouvrir_Adminer.bat.
    echo.
    pause
    exit /b 1
)

REM 2. Vérification de Python
where python >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas détecté sur votre ordinateur.
    echo Veuillez installer Python depuis https://www.python.org/
    echo en cochant la case "Add Python to PATH".
    echo.
    pause
    exit /b 1
)

REM 3. Vérification de la bibliothèque paramiko (installation automatique si absente)
python -c "import paramiko" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Préparation de la bibliothèque SSH (paramiko)...
    python -m pip install paramiko
    echo.
)

REM 4. Lancement du tunnel
echo Connexion au serveur distant et activation de la passerelle...
python %SCRIPT_PATH%

echo.
echo Tunnel arrêté. Port 8088 libéré.
pause
