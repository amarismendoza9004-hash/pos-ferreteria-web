@echo off
cd /d "%~dp0"
title Mostrador - Punto de venta

set PY=python
where python >nul 2>nul
if errorlevel 1 (
  where py >nul 2>nul
  if errorlevel 1 (
    echo.
    echo  No se encontro Python en esta computadora.
    echo  Instalalo desde https://www.python.org/downloads/
    echo  y durante la instalacion marca la casilla "Add Python to PATH".
    echo.
    pause
    exit /b
  )
  set PY=py
)

if not exist ".venv\Scripts\activate.bat" (
  echo.
  echo  Preparando el programa por primera vez. Esto tarda un minuto...
  echo.
  %PY% -m venv .venv
  call .venv\Scripts\activate.bat
) else (
  call .venv\Scripts\activate.bat
)

rem Instala lo que falte (si ya esta todo instalado, no tarda nada)
pip install -q --disable-pip-version-check -r requirements.txt

if not exist "instance\mostrador.sqlite" (
  flask --app mostrador seed-db
)

echo.
echo  ==========================================================
echo   El punto de venta se abrira en tu navegador.
echo   Direccion: http://127.0.0.1:5000
echo.
echo   NO cierres esta ventana mientras uses el programa.
echo   Para apagarlo, cierra esta ventana.
echo  ==========================================================
echo.

start "" cmd /c "timeout /t 3 >nul & start http://127.0.0.1:5000"
flask --app mostrador run
pause
