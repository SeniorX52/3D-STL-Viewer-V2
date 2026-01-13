; Inno Setup Script for 3D Insole Adapter
; ========================================
; This script creates a professional Windows installer.
; 
; Prerequisites:
;   1. Build the executable first using: pyinstaller build.spec --clean
;   2. Install Inno Setup from: https://jrsoftware.org/isinfo.php
;   3. Run this script with Inno Setup Compiler
;
; Build with: "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss

#define MyAppName "3D Insole Adapter"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Mostafa Abdelaziz"
#define MyAppURL ""
#define MyAppExeName "InsoleAdapter.exe"

[Setup]
; Application info
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Installation settings
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=
OutputDir=installer_output
OutputBaseFilename=InsoleAdapter_Setup_{#MyAppVersion}
SetupIconFile=logo.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

; Upgrade settings - automatically handle previous versions
UsePreviousAppDir=yes
UsePreviousGroup=yes
UsePreviousTasks=yes
CloseApplications=yes
CloseApplicationsFilter=*.exe
RestartApplications=yes
UninstallDisplayName={#MyAppName}
Uninstallable=yes
CreateUninstallRegKey=yes

; Privileges (per-user installation doesn't require admin)
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; Windows version requirements
MinVersion=10.0

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Main executable
Source: "dist\InsoleAdapter.exe"; DestDir: "{app}"; Flags: ignoreversion

; Documentation
Source: "docs\USER_GUIDE.md"; DestDir: "{app}\docs"; Flags: ignoreversion
Source: "docs\TECHNICAL.md"; DestDir: "{app}\docs"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion

; Sample models - organized in subfolders
Source: "models\foot\*"; DestDir: "{app}\models\foot"; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist
Source: "models\insole\*"; DestDir: "{app}\models\insole"; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist

[Icons]
; Start Menu
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\User Guide"; Filename: "{app}\docs\USER_GUIDE.md"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"

; Desktop icon (optional)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

; Quick Launch (legacy)
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
; Option to run app after installation
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Registry]
; File associations for STL files (optional)
Root: HKA; Subkey: "Software\Classes\.stl\OpenWithProgids"; ValueType: string; ValueName: "InsoleAdapter.stl"; ValueData: ""; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\InsoleAdapter.stl"; ValueType: string; ValueName: ""; ValueData: "STL 3D Model File"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\InsoleAdapter.stl\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName},0"
Root: HKA; Subkey: "Software\Classes\InsoleAdapter.stl\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""

[Code]
// Global variable to store uninstall string
var
  UninstallString: String;
  PreviousVersion: String;

// Get the uninstall string for a previous installation
function GetUninstallString(): String;
var
  UninstPath: String;
  UninstallStr: String;
begin
  Result := '';
  // Check current user installation first
  UninstPath := 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{#emit SetupSetting("AppId")}_is1';
  if RegQueryStringValue(HKCU, UninstPath, 'UninstallString', UninstallStr) then
    Result := UninstallStr
  else if RegQueryStringValue(HKLM, UninstPath, 'UninstallString', UninstallStr) then
    Result := UninstallStr;
end;

// Get the version of a previous installation
function GetPreviousVersion(): String;
var
  UninstPath: String;
  VersionStr: String;
begin
  Result := '';
  UninstPath := 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{#emit SetupSetting("AppId")}_is1';
  if RegQueryStringValue(HKCU, UninstPath, 'DisplayVersion', VersionStr) then
    Result := VersionStr
  else if RegQueryStringValue(HKLM, UninstPath, 'DisplayVersion', VersionStr) then
    Result := VersionStr;
end;

// Check if app is currently running
function IsAppRunning(): Boolean;
var
  ResultCode: Integer;
begin
  // Use tasklist to check if the app is running
  Result := Exec('cmd.exe', '/c tasklist /FI "IMAGENAME eq {#MyAppExeName}" | find /i "{#MyAppExeName}"', 
                 '', SW_HIDE, ewWaitUntilTerminated, ResultCode) and (ResultCode = 0);
end;

// Uninstall the previous version
function UninstallPrevious(): Boolean;
var
  ResultCode: Integer;
  UninstallCmd: String;
begin
  Result := True;
  UninstallCmd := RemoveQuotes(UninstallString);
  
  if UninstallCmd <> '' then
  begin
    // Run the uninstaller silently
    if not Exec(UninstallCmd, '/SILENT /NORESTART /SUPPRESSMSGBOXES', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
    begin
      Result := False;
    end;
  end;
end;

// Check if .NET or Visual C++ redistributable might be needed
function InitializeSetup(): Boolean;
var
  MsgResult: Integer;
begin
  Result := True;
  
  // Get the uninstall string for any previous installation
  UninstallString := GetUninstallString();
  PreviousVersion := GetPreviousVersion();
  
  // If a previous version is installed, ask the user what to do
  if UninstallString <> '' then
  begin
    if PreviousVersion <> '' then
      MsgResult := MsgBox(
        '{#MyAppName} version ' + PreviousVersion + ' is already installed.' + #13#10 + #13#10 +
        'Do you want to uninstall the previous version and install version {#MyAppVersion}?' + #13#10 + #13#10 +
        'Click Yes to uninstall the old version first (recommended).' + #13#10 +
        'Click No to install over the existing version.' + #13#10 +
        'Click Cancel to abort the installation.',
        mbConfirmation, MB_YESNOCANCEL)
    else
      MsgResult := MsgBox(
        'A previous version of {#MyAppName} is already installed.' + #13#10 + #13#10 +
        'Do you want to uninstall it before installing version {#MyAppVersion}?' + #13#10 + #13#10 +
        'Click Yes to uninstall the old version first (recommended).' + #13#10 +
        'Click No to install over the existing version.' + #13#10 +
        'Click Cancel to abort the installation.',
        mbConfirmation, MB_YESNOCANCEL);
    
    case MsgResult of
      IDYES:
        begin
          // Check if app is running
          if IsAppRunning() then
          begin
            MsgBox('{#MyAppName} is currently running.' + #13#10 + #13#10 +
                   'Please close the application and try again.',
                   mbError, MB_OK);
            Result := False;
            Exit;
          end;
          
          // Uninstall previous version
          WizardForm.StatusLabel.Caption := 'Removing previous version...';
          if not UninstallPrevious() then
          begin
            MsgBox('Failed to uninstall the previous version.' + #13#10 +
                   'Please uninstall it manually from Control Panel and try again.',
                   mbError, MB_OK);
            Result := False;
          end;
        end;
      IDNO:
        begin
          // Continue with installation over existing version
          Result := True;
        end;
      IDCANCEL:
        begin
          // User cancelled
          Result := False;
        end;
    end;
  end;
end;

// Custom messages
procedure InitializeWizard();
begin
  WizardForm.WelcomeLabel2.Caption := 
    'This will install {#MyAppName} on your computer.' + #13#10 + #13#10 +
    '{#MyAppName} is a professional tool for adapting orthotic insoles to 3D foot scans.' + #13#10 + #13#10 +
    'Features:' + #13#10 +
    '• Load and view 3D foot scans (STL files)' + #13#10 +
    '• Automatically scale insoles to match foot dimensions' + #13#10 +
    '• Add text labels (embossed or engraved)' + #13#10 +
    '• Export customized insoles for 3D printing' + #13#10 + #13#10 +
    'No additional software required - everything is included!';
end;
