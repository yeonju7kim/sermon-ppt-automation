; Inno Setup script — SermonPPT Windows installer
; 사전 요구: dist\SermonPPT.exe (build_windows.bat 실행 후 생성됨)
; 빌드:    Inno Setup Compiler 로 이 파일 열고 Build > Compile
;          또는 명령줄: "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
; 결과:    dist\SermonPPT-Setup.exe

#define MyAppName "Sermon PPT"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Sermon PPT"
#define MyAppExeName "SermonPPT.exe"

[Setup]
AppId={{C9F0B7D2-2A1E-4F4D-9E1B-PPT-AUTOMATION}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\SermonPPT
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=dist
OutputBaseFilename=SermonPPT-Setup
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin
WizardStyle=modern

[Languages]
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\SermonPPT.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
