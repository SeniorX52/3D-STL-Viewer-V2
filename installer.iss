; Inno Setup Script for Orthosis Customizer
; ==========================================
; This script creates a professional Windows installer.
; 
; Prerequisites:
;   1. Build the executable first using: pyinstaller build.spec --clean
;   2. Install Inno Setup from: https://jrsoftware.org/isinfo.php
;   3. Run this script with Inno Setup Compiler
;
; Build with: "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss

#define MyAppName "Orthosis Customizer"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Mostafa Abdelaziz"
#define MyAppURL ""
#define MyAppExeName "OrthosisCustomizer.exe"

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
OutputBaseFilename=OrthosisCustomizer_Setup_{#MyAppVersion}
SetupIconFile=icon.ico
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
Source: "dist\OrthosisCustomizer.exe"; DestDir: "{app}"; Flags: ignoreversion

; Documentation
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion

; Logo STL files
Source: "logos\*"; DestDir: "{app}\logos"; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist

; Sample STL models for testing
Source: "V2-stl\*"; DestDir: "{app}\models"; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist

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
Root: HKA; Subkey: "Software\Classes\.stl\OpenWithProgids"; ValueType: string; ValueName: "OrthosisCustomizer.stl"; ValueData: ""; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\OrthosisCustomizer.stl"; ValueType: string; ValueName: ""; ValueData: "STL 3D Model File"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\OrthosisCustomizer.stl\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName},0"
Root: HKA; Subkey: "Software\Classes\OrthosisCustomizer.stl\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""

[Code]
// Custom messages
procedure InitializeWizard();
begin
  WizardForm.WelcomeLabel2.Caption := 
    'This will install {#MyAppName} on your computer.' + #13#10 + #13#10 +
    '{#MyAppName} is a professional tool for customizing orthosis STL files.' + #13#10 + #13#10 +
    'Features:' + #13#10 +
    '• Load orthosis STL files' + #13#10 +
    '• Automatic left/right mirroring' + #13#10 +
    '• PNG logo engraving with adjustable parameters' + #13#10 +
    '• Text engraving (patient name + date)' + #13#10 +
    '• Adjustable depth, scale, rotation' + #13#10 +
    '• Dual STL export (Left and Right versions)' + #13#10 + #13#10 +
    'No additional software required - everything is included!';
end;
