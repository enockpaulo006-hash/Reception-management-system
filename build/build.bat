@echo off
setlocal

set "PROJECT_ROOT=%~dp0.."
set "PYTHON=%PROJECT_ROOT%\venv\Scripts\python.exe"
set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

if not exist "%PYTHON%" (
  echo Virtual environment Python was not found: %PYTHON%
  exit /b 1
)

if not exist "%ISCC%" (
  echo Inno Setup 6 was not found: %ISCC%
  exit /b 1
)

pushd "%PROJECT_ROOT%"
"%PYTHON%" manage.py collectstatic --noinput || goto :error
"%PYTHON%" -m PyInstaller --noconfirm --clean build\build.spec || goto :error
"%ISCC%" build\installer.iss || goto :error
popd

echo Build complete: dist\installer\ClinicReception-Setup.exe
exit /b 0

:error
set "EXIT_CODE=%ERRORLEVEL%"
popd
exit /b %EXIT_CODE%
