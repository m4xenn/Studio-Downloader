[Setup]
AppName=Studio Downloader
AppVersion=1.0.0
AppPublisher=Salih
DefaultDirName={autopf}\Studio Downloader
DefaultGroupName=Studio Downloader
OutputDir=.\Installer
OutputBaseFilename=StudioDownloader_Setup
Compression=lzma
SolidCompression=yes
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\icon.ico

[Files]
Source: "dist\StudioDownloader\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Studio Downloader"; Filename: "{app}\StudioDownloader.exe"; IconFilename: "{app}\icon.ico"
Name: "{group}\Kaldır Studio Downloader"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Studio Downloader"; Filename: "{app}\StudioDownloader.exe"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Masaüstüne kısayol oluştur"; GroupDescription: "Ek Kısayollar:"
