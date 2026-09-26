; Instalador tipo asistente de Windows (Siguiente/Siguiente/Elegir carpeta/Instalar/Finalizar)
; para la traducción al español de Night Call. Se compila con Inno Setup (ISCC.exe) a partir
; del payload armado por tools/build_release.py (BepInEx + plugin + Spanish_UI/Spanish_Texts).
;
; No se versiona el .exe resultante: se genera en dist/.

#define MyAppName "Night Call - Traducción al español"
#define MyAppVersion "1.0.1"
#define MyAppPublisher "Traducción fan (no oficial)"
#define Payload "payload"

[Setup]
AppId={{6E3F0B7C-6C6A-4B7B-9F0C-9A6E1F5B3A11}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={code:GetDefaultDir}
DefaultGroupName=Night Call - Traducción al español
DisableProgramGroupPage=yes
DisableWelcomePage=no
DirExistsWarning=no
UsePreviousAppDir=no
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\..\dist
OutputBaseFilename=NightCallEspanol_Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayName={#MyAppName}
SetupLogging=yes

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Files]
; BepInEx: solo si el juego elegido todavía no lo tiene (NeedsBepInEx chequea en runtime)
Source: "{#Payload}\winhttp.dll"; DestDir: "{app}"; Flags: ignoreversion; Check: NeedsBepInEx
Source: "{#Payload}\doorstop_config.ini"; DestDir: "{app}"; Flags: ignoreversion; Check: NeedsBepInEx
Source: "{#Payload}\BepInEx\core\*"; DestDir: "{app}\BepInEx\core"; Flags: ignoreversion recursesubdirs createallsubdirs; Check: NeedsBepInEx
; El plugin de traducción y los textos, siempre
Source: "{#Payload}\mod\NightCallSpanish.dll"; DestDir: "{app}\BepInEx\plugins"; Flags: ignoreversion
Source: "{#Payload}\mod\Spanish_UI\*"; DestDir: "{app}\Spanish_UI"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#Payload}\mod\Spanish_Texts\*"; DestDir: "{app}\Spanish_Texts"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Desinstalar traducción al español"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\Night Call.exe"; Description: "Abrir Night Call ahora"; Flags: nowait postinstall skipifsilent unchecked

[Code]
function FileExists2(FileName: String): Boolean;
begin
  Result := FileExists(FileName);
end;

function IsValidGameDir(Dir: String): Boolean;
begin
  Result := FileExists2(Dir + '\Night Call.exe');
end;

// BepInEx solo está completo si están las tres piezas: el loader (winhttp.dll), su config
// y el preloader. Un winhttp.dll suelto (resto de una desinstalación) NO cuenta.
function NeedsBepInEx: Boolean;
var
  App: String;
begin
  App := ExpandConstant('{app}');
  Result := not (FileExists2(App + '\winhttp.dll')
             and FileExists2(App + '\doorstop_config.ini')
             and FileExists2(App + '\BepInEx\core\BepInEx.Preloader.dll'));
end;

// Busca "Night Call.exe" en las bibliotecas de Steam leyendo el registro y
// libraryfolders.vdf, igual que el instalador de consola (tools/installer/install.py).
function FindSteamGameDir(): String;
var
  SteamPath, Vdf, Line, Rest: String;
  Lines: TArrayOfString;
  I, P1, P2: Integer;
  Candidate: String;
begin
  Result := '';
  if not RegQueryStringValue(HKCU, 'Software\Valve\Steam', 'SteamPath', SteamPath) then
    exit;
  StringChangeEx(SteamPath, '/', '\', True);

  Candidate := SteamPath + '\steamapps\common\Night Call';
  if IsValidGameDir(Candidate) then
  begin
    Result := Candidate;
    exit;
  end;

  Vdf := SteamPath + '\steamapps\libraryfolders.vdf';
  if not FileExists2(Vdf) then
    exit;
  if not LoadStringsFromFile(Vdf, Lines) then
    exit;

  for I := 0 to GetArrayLength(Lines) - 1 do
  begin
    Line := Lines[I];
    P1 := Pos('"path"', Line);
    if P1 > 0 then
    begin
      // todo lo que sigue a `"path"` (puede haber tabs o espacios antes del valor)
      Rest := Copy(Line, P1 + 6, Length(Line) - P1 - 5);
      P1 := Pos('"', Rest);          // comilla de apertura del valor
      if P1 > 0 then
      begin
        Rest := Copy(Rest, P1 + 1, Length(Rest) - P1);
        P2 := Pos('"', Rest);        // comilla de cierre del valor
      end
      else
        P2 := 0;
      if (P1 > 0) and (P2 > 0) then
      begin
        Candidate := Copy(Rest, 1, P2 - 1);
        StringChangeEx(Candidate, '\\', '\', True);
        Candidate := Candidate + '\steamapps\common\Night Call';
        if IsValidGameDir(Candidate) then
        begin
          Result := Candidate;
          exit;
        end;
      end;
    end;
  end;
end;

// Respaldo si el registro/vdf no lo encontraron: prueba las rutas típicas de
// biblioteca de Steam en cada letra de unidad presente en la máquina.
function ScanDrivesForGame(): String;
var
  DriveCode: Integer;
  Root, Candidate: String;
  Suffixes: array[0..3] of String;
  I: Integer;
begin
  Result := '';
  Suffixes[0] := '\SteamLibrary\steamapps\common\Night Call';
  Suffixes[1] := '\Steam\steamapps\common\Night Call';
  Suffixes[2] := '\Program Files (x86)\Steam\steamapps\common\Night Call';
  Suffixes[3] := '\Program Files\Steam\steamapps\common\Night Call';
  for DriveCode := Ord('C') to Ord('Z') do
  begin
    Root := Chr(DriveCode) + ':';
    if not DirExists(Root + '\') then
      continue;
    for I := 0 to 3 do
    begin
      Candidate := Root + Suffixes[I];
      if IsValidGameDir(Candidate) then
      begin
        Result := Candidate;
        exit;
      end;
    end;
  end;
end;

function GetDefaultDir(Param: String): String;
var
  Found: String;
begin
  Found := FindSteamGameDir();
  if Found = '' then
    Found := ScanDrivesForGame();
  if Found <> '' then
    Result := Found
  else
    Result := ExpandConstant('{autopf}') + '\Steam\steamapps\common\Night Call';
end;

// Avisa (sin bloquear) si la carpeta elegida no parece ser la de Night Call.
function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if CurPageID = wpSelectDir then
  begin
    if not IsValidGameDir(WizardDirValue()) then
    begin
      Result := (MsgBox('No encuentro "Night Call.exe" en esa carpeta.' + #13#10 +
        '¿Instalar ahí de todas formas?', mbConfirmation, MB_YESNO) = IDYES);
    end;
  end;
end;
