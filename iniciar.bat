@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Falta el entorno virtual. Consulta README.md.
  goto error
)
if not exist ".env" (
  echo Falta .env. Consulta README.md.
  goto error
)
if exist ".local\pgdata\PG_VERSION" (
  ".local\pgsql\bin\pg_ctl.exe" -D ".local\pgdata" status >nul 2>&1
  if errorlevel 1 (
    ".local\pgsql\bin\pg_ctl.exe" -D ".local\pgdata" -l ".local\postgres.log" -w start
    if errorlevel 1 goto error
  )
)
".venv\Scripts\python.exe" scripts\download_model.py
if errorlevel 1 goto error
".venv\Scripts\python.exe" manage.py check --database default
if errorlevel 1 goto error
".venv\Scripts\python.exe" manage.py migrate --noinput
if errorlevel 1 goto error
start "" "http://127.0.0.1:8000/"
".venv\Scripts\python.exe" manage.py runserver 127.0.0.1:8000 --noreload
exit /b
:error
echo No se pudo iniciar ManoVision. Revisa el error anterior.
pause
exit /b 1
