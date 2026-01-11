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
SetupIconFile=
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

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
// Check if .NET or Visual C++ redistributable might be needed
function InitializeSetup(): Boolean;
begin
  Result := True;
  // Add any pre-installation checks here if needed
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
