"""Arma los instaladores distribuibles de la traducción al español.

  python tools/build_release.py [ruta_juego_con_bepinex]

Junta en tools/installer/payload/: BepInEx (core, winhttp.dll, doorstop_config.ini)
+ el mod compilado (build/data). Los toma de una instalación local que ya tenga
BepInEx (por defecto la ruta de tools/install.py). Con eso arma dos instaladores:

- dist/NightCallEspanol_Setup.exe: asistente normal de Windows (Siguiente/Siguiente/
  Elegir carpeta/Instalar/Finalizar), compilado con Inno Setup. Este es el que se
  reparte por defecto.
- dist/NightCallEspanol_Instalador_Consola.exe: instalador por consola (PyInstaller),
  alternativa para quien prefiera texto o tenga problemas con el asistente.

Requiere: pip install pyinstaller, e Inno Setup 6 instalado (ISCC.exe se busca en las
rutas habituales; si no está, se salta ese instalador con un aviso).
"""
import glob
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__)).rsplit(os.sep, 1)[0]
GAME_DEFAULT = r"D:\SteamLibrary\steamapps\common\Night Call"
BUILD_DATA = os.path.join(ROOT, "build", "data")
INSTALLER_DIR = os.path.join(ROOT, "tools", "installer")
PAYLOAD = os.path.join(INSTALLER_DIR, "payload")
DIST = os.path.join(ROOT, "dist")


def check_validation():
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    out = subprocess.run([sys.executable, "tools/validate.py"], cwd=ROOT, capture_output=True,
                         text=True, encoding="utf-8", env=env)
    print(out.stdout.strip().splitlines()[-1] if out.stdout.strip() else out.stderr[-300:])
    if out.returncode != 0:
        sys.exit("validate.py encontró errores: no empaqueto un instalador con datos rotos")


def stage_payload(game):
    if os.path.isdir(PAYLOAD):
        shutil.rmtree(PAYLOAD)
    os.makedirs(PAYLOAD)

    winhttp = os.path.join(game, "winhttp.dll")
    doorstop = os.path.join(game, "doorstop_config.ini")
    core = os.path.join(game, "BepInEx", "core")
    for p in (winhttp, doorstop, core):
        if not os.path.exists(p):
            sys.exit(f"falta {p} - necesito una instalación local de BepInEx para tomarlo de ahí")
    shutil.copy(winhttp, PAYLOAD)
    shutil.copy(doorstop, PAYLOAD)
    shutil.copytree(core, os.path.join(PAYLOAD, "BepInEx", "core"))

    dll = os.path.join(ROOT, "src", "Mod", "bin", "Release", "net46", "NightCallSpanish.dll")
    if not os.path.exists(dll):
        sys.exit(f"falta {dll} - compilá el plugin (src/Mod) en Release antes de empaquetar")
    mod_dir = os.path.join(PAYLOAD, "mod")
    os.makedirs(mod_dir)
    shutil.copy(dll, mod_dir)
    for folder in ("Spanish_UI", "Spanish_Texts"):
        src = os.path.join(BUILD_DATA, folder)
        if not os.path.isdir(src):
            sys.exit(f"falta {src} - corré tools/generate.py antes de empaquetar")
        shutil.copytree(src, os.path.join(mod_dir, folder))

    n_texts = len(os.listdir(os.path.join(mod_dir, "Spanish_Texts")))
    print(f"payload armado: BepInEx/core + DLL + Spanish_UI + {n_texts} archivos en Spanish_Texts")


def run_pyinstaller():
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile", "--console",
        "--name", "NightCallEspanol_Instalador_Consola",
        "--distpath", DIST,
        "--workpath", os.path.join(ROOT, "build", "pyinstaller"),
        "--specpath", os.path.join(ROOT, "build", "pyinstaller"),
        "--add-data", f"{PAYLOAD}{os.pathsep}payload",
        os.path.join(INSTALLER_DIR, "install.py"),
    ]
    subprocess.run(cmd, cwd=ROOT, check=True)
    return os.path.join(DIST, "NightCallEspanol_Instalador_Consola.exe")


def find_iscc():
    candidates = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    found = glob.glob(os.path.expandvars(r"%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"))
    return found[0] if found else None


def run_innosetup():
    iscc = find_iscc()
    if not iscc:
        print("AVISO: no encontré ISCC.exe (Inno Setup) - salteo el instalador tipo asistente")
        return None
    cmd = [iscc, os.path.join(INSTALLER_DIR, "setup.iss")]
    subprocess.run(cmd, cwd=INSTALLER_DIR, check=True)
    return os.path.join(DIST, "NightCallEspanol_Setup.exe")


if __name__ == "__main__":
    game = sys.argv[1] if len(sys.argv) > 1 else GAME_DEFAULT
    # BepInEx original de referencia si el juego local no lo tiene (p. ej. tras reinstalarlo)
    ref = os.path.join(ROOT, "ref-russian", "data")
    if not os.path.exists(os.path.join(game, "winhttp.dll")) and os.path.exists(os.path.join(ref, "winhttp.dll")):
        print(f"el juego no tiene BepInEx: lo tomo de {ref}")
        game = ref
    check_validation()
    stage_payload(game)
    if os.path.isdir(DIST):
        shutil.rmtree(DIST)
    exes = [run_innosetup(), run_pyinstaller()]
    print()
    for exe in exes:
        if exe and os.path.exists(exe):
            print(f"listo: {exe} ({os.path.getsize(exe) / 1024 / 1024:.1f} MB)")
