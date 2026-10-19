#define AppName "Clinic Reception"
#define AppVersion "1.0.0"
#define AppPublisher "Clinic Reception"
#define AppExeName "ClinicReception.exe"

[Setup]
AppId={{E2A2D2E5-FA5A-4E32-A584-69A4CF8F0A8C}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\ClinicReception
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=..\dist\installer
OutputBaseFilename=ClinicReception-Setup
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#AppExeName}

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Files]
Source: "..\dist\ClinicReception\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
; Keep clinic data and backups even when the application is uninstalled.
Name: "{commonappdata}\ClinicReception"; Flags: uninsneveruninstall
Name: "{commonappdata}\ClinicReception\data"; Flags: uninsneveruninstall
Name: "{commonappdata}\ClinicReception\backup"; Flags: uninsneveruninstall

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
; The packaged launcher performs the backup when invoked with --backup.
Filename: "schtasks.exe"; Parameters: "/Create /F /SC DAILY /ST 20:00 /TN ""ClinicReception Daily Backup"" /TR """"{app}\{#AppExeName}"" --backup"""; Flags: runhidden

[UninstallRun]
Filename: "schtasks.exe"; Parameters: "/Delete /F /TN ""ClinicReception Daily Backup"""; Flags: runhidden

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;
