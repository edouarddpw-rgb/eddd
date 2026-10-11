@echo off
rem FOLLOW - lance la page en local (Windows). Double-clique sur ce fichier.
cd /d "%~dp0"
set PORT=8765
set URL=http://localhost:%PORT%/index.html

where py >nul 2>nul
if %errorlevel%==0 (
  start "FOLLOW - serveur local" py -m http.server %PORT%
  timeout /t 2 >nul
  start "" %URL%
  goto :eof
)
where npx >nul 2>nul
if %errorlevel%==0 (
  start "FOLLOW - serveur local" cmd /c npx --yes http-server -p %PORT% -c-1 .
  timeout /t 4 >nul
  start "" %URL%
  goto :eof
)
echo Ni Python ni Node trouves : ouverture directe du fichier.
start "" index.html
