# Build assets

`app-icon.svg` is the application icon placeholder. Convert it to a Windows
`.ico` file named `app.ico` in this directory before a release build; the
PyInstaller spec automatically uses it when present.

Prerequisites on the build PC:

- the project virtual environment, including PyInstaller;
- Inno Setup 6 installed at its default path.

Run `build\build.bat` from PowerShell or Command Prompt. The installer is
written to `dist\installer\ClinicReception-Setup.exe`.
