"""Instala el build en el juego: DLL del mod + Spanish_UI + Spanish_Texts.

  python tools/install.py [ruta_juego] [--with-dumper]
Por defecto quita NightCallDumper.dll de plugins (solo se necesita para re-volcar).
Antes de instalar copia las partidas guardadas a backups/saves/<fecha>/ (se guardan las 10 últimas).
Requiere BepInEx ya instalado en el juego (winhttp.dll + BepInEx/core).
"""
import datetime
import glob
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = r"D:\SteamLibrary\steamapps\common\Night Call"
DLL = os.path.join(ROOT, "src", "Mod", "bin", "Release", "net46", "NightCallSpanish.dll")
DUMPER = os.path.join(ROOT, "src", "Dumper", "bin", "Release", "net46", "NightCallDumper.dll")
DATA = os.path.join(ROOT, "build", "data")
SAVES = os.path.join(os.path.expanduser("~"), "AppData", "LocalLow", "Raw Fury", "Night Call")
BACKUPS = os.path.join(ROOT, "backups", "saves")
KEEP_BACKUPS = 10


def backup_saves():
    files = glob.glob(os.path.join(SAVES, "*.sav"))
    if not files:
        return 0
    dst = os.path.join(BACKUPS, datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
    os.makedirs(dst, exist_ok=True)
    for f in files:
        shutil.copy2(f, dst)
    for old in sorted(os.listdir(BACKUPS))[:-KEEP_BACKUPS]:
        shutil.rmtree(os.path.join(BACKUPS, old), ignore_errors=True)
    return len(files)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    game = args[0] if args else GAME
    plugins = os.path.join(game, "BepInEx", "plugins")
    if not os.path.exists(os.path.join(game, "winhttp.dll")) or not os.path.isdir(plugins):
        sys.exit(f"BepInEx no está instalado en {game}")
    print(f"partidas respaldadas: {backup_saves()} -> backups/saves/")
    shutil.copy(DLL, plugins)
    dumper_dst = os.path.join(plugins, "NightCallDumper.dll")
    if "--with-dumper" in sys.argv:
        shutil.copy(DUMPER, plugins)
    elif os.path.exists(dumper_dst):
        os.remove(dumper_dst)
    for folder in ("Spanish_UI", "Spanish_Texts"):
        dst = os.path.join(game, folder)
        shutil.rmtree(dst, ignore_errors=True)
        shutil.copytree(os.path.join(DATA, folder), dst)
    n = len(os.listdir(os.path.join(game, "Spanish_Texts")))
    print(f"instalado en {game}: DLL + Spanish_UI + {n} archivos en Spanish_Texts")
