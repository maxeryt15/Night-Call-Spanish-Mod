# -*- coding: utf-8 -*-
"""Instalador de la traducción al español de Night Call para el usuario final.

Se distribuye compilado como .exe (ver tools/build_release.py). Instala BepInEx
(si no está) + el plugin de traducción, y deja un desinstalador nativo (.bat) en
la carpeta del juego.
"""
import ctypes
import json
import os
import shutil
import sys
import winreg

APP_NAME = "Night Call - Traducción al español"
MARKER_NAME = "night_call_es_install.json"
UNINSTALL_NAME = "Desinstalar traduccion al espanol.bat"


def fix_console_encoding():
    try:
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        ctypes.windll.kernel32.SetConsoleCP(65001)
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def payload_dir():
    # Cuando PyInstaller empaqueta con --add-data, los archivos quedan en
    # sys._MEIPASS (onefile) bajo la misma estructura relativa.
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "payload")


def safe_input(prompt, default=""):
    try:
        return input(prompt)
    except EOFError:
        return default


def pause_exit(code):
    try:
        input("\nPresiona Enter para salir...")
    except EOFError:
        pass
    sys.exit(code)


def find_steam_path():
    for hive, key in ((winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam"),
                       (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam"),
                       (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam")):
        try:
            with winreg.OpenKey(hive, key) as k:
                path, _ = winreg.QueryValueEx(k, "SteamPath" if hive == winreg.HKEY_CURRENT_USER else "InstallPath")
                if os.path.isdir(path):
                    return path
        except OSError:
            continue
    return None


def steam_library_paths(steam_path):
    libs = [steam_path]
    vdf = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
    if os.path.isfile(vdf):
        try:
            with open(vdf, encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except OSError:
            text = ""
        import re
        for m in re.finditer(r'"path"\s*"([^"]+)"', text):
            p = m.group(1).replace("\\\\", "\\")
            if p not in libs:
                libs.append(p)
    return libs


def find_game_folder():
    steam_path = find_steam_path()
    if not steam_path:
        return None
    for lib in steam_library_paths(steam_path):
        candidate = os.path.join(lib, "steamapps", "common", "Night Call")
        if os.path.isfile(os.path.join(candidate, "Night Call.exe")):
            return candidate
    return None


def ask_game_folder():
    print("No pude encontrar la carpeta de Night Call automáticamente.")
    print("Busca la carpeta donde está 'Night Call.exe' (normalmente en")
    print(r"...\SteamLibrary\steamapps\common\Night Call) y pega la ruta aquí.")
    while True:
        path = safe_input("Ruta de la carpeta de Night Call: ").strip(' "')
        if path and os.path.isfile(os.path.join(path, "Night Call.exe")):
            return path
        if not path:
            print("No se pudo leer una ruta (sin consola interactiva). Cancelo.")
            pause_exit(1)
        print("Esa carpeta no tiene 'Night Call.exe'. Prueba de nuevo.\n")


def copytree_force(src, dst):
    shutil.copytree(src, dst, dirs_exist_ok=True)


def write_uninstaller(game, installed_bepinex):
    lines = [
        "@echo off",
        "chcp 65001 >nul",
        "echo Desinstalando la traduccion al espanol de Night Call...",
        f'del /f /q "{game}\\BepInEx\\plugins\\NightCallSpanish.dll" 2>nul',
        f'rmdir /s /q "{game}\\Spanish_UI" 2>nul',
        f'rmdir /s /q "{game}\\Spanish_Texts" 2>nul',
        f'del /f /q "{game}\\{MARKER_NAME}" 2>nul',
        f'del /f /q "{game}\\BepInEx\\config\\com.nightcall.spanish.cfg" 2>nul',
    ]
    if installed_bepinex:
        # Igual que el asistente (Inno): solo se quita lo que instaló esta traducción.
        # Los plugins de otros mods en BepInEx\plugins no se tocan; las carpetas vacías sí se van.
        lines += [
            "echo Tambien se instalo BepInEx junto con la traduccion: se va a quitar.",
            f'del /f /q "{game}\\winhttp.dll" 2>nul',
            f'del /f /q "{game}\\doorstop_config.ini" 2>nul',
            f'rmdir /s /q "{game}\\BepInEx\\core" 2>nul',
            f'rmdir /s /q "{game}\\BepInEx\\cache" 2>nul',
            f'del /f /q "{game}\\BepInEx\\LogOutput.log" 2>nul',
            f'del /f /q "{game}\\BepInEx\\config\\BepInEx.cfg" 2>nul',
            f'rmdir "{game}\\BepInEx\\config" 2>nul',
            f'rmdir "{game}\\BepInEx\\plugins" 2>nul',
            f'rmdir "{game}\\BepInEx" 2>nul',
        ]
    else:
        lines.append("echo BepInEx no se toca (ya estaba instalado antes de esta traduccion).")
    lines += [
        "echo Listo. El juego quedo sin la traduccion.",
        "pause",
        # autoborrarse va al final (si no, cmd pierde la referencia al
        # archivo y no llega a las lineas siguientes) y con "(goto) 2>nul &"
        # para que cmd suelte el archivo antes del delete: sin eso, tira
        # "No se ha encontrado el archivo por lotes" (cosmetico, pero feo).
        f'(goto) 2>nul & del /f /q "{game}\\{UNINSTALL_NAME}"',
    ]
    path = os.path.join(game, UNINSTALL_NAME)
    with open(path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write("\n".join(lines) + "\n")


def main():
    fix_console_encoding()
    print(f"=== {APP_NAME} ===\n")
    payload = payload_dir()
    if not os.path.isdir(payload):
        print("ERROR: no se encontró el contenido del instalador (payload/). Build corrupto.")
        pause_exit(1)

    game = find_game_folder()
    if game:
        print(f"Encontré Night Call en:\n  {game}\n")
        resp = safe_input("¿Instalar ahí? [S/n]: ").strip().lower()
        if resp == "n":
            game = ask_game_folder()
    else:
        game = ask_game_folder()

    plugins = os.path.join(game, "BepInEx", "plugins")
    # BepInEx completo = loader + config + preloader; un winhttp.dll suelto o core/ vacío no cuenta
    had_bepinex = all(os.path.isfile(os.path.join(game, *p)) for p in (
        ("winhttp.dll",), ("doorstop_config.ini",), ("BepInEx", "core", "BepInEx.Preloader.dll")))

    if not had_bepinex:
        print("\nBepInEx no está instalado: lo instalo junto con la traducción...")
        shutil.copy(os.path.join(payload, "winhttp.dll"), game)
        shutil.copy(os.path.join(payload, "doorstop_config.ini"), game)
        copytree_force(os.path.join(payload, "BepInEx"), os.path.join(game, "BepInEx"))
        os.makedirs(plugins, exist_ok=True)
    else:
        print("\nBepInEx ya está instalado, no lo toco.")
        os.makedirs(plugins, exist_ok=True)

    print("Instalando la traducción...")
    shutil.copy(os.path.join(payload, "mod", "NightCallSpanish.dll"), plugins)
    for folder in ("Spanish_UI", "Spanish_Texts"):
        dst = os.path.join(game, folder)
        shutil.rmtree(dst, ignore_errors=True)
        copytree_force(os.path.join(payload, "mod", folder), dst)

    # Si una instalación anterior de esta traducción ya había puesto BepInEx, se conserva
    # esa marca: al actualizar, BepInEx aparece "completo", pero sigue siendo nuestro.
    installed_bepinex = not had_bepinex
    marker = os.path.join(game, MARKER_NAME)
    try:
        with open(marker, encoding="utf-8") as f:
            installed_bepinex = installed_bepinex or bool(json.load(f).get("installed_bepinex"))
    except (OSError, ValueError):
        pass
    with open(marker, "w", encoding="utf-8") as f:
        json.dump({"installed_bepinex": installed_bepinex}, f)
    write_uninstaller(game, installed_bepinex)

    print("\n¡Listo! La traducción quedó instalada.")
    print("Abre el juego. La traducción reemplaza al inglés: deja el idioma del juego en English (el que viene por defecto).")
    print(f'Para desinstalarla, ejecuta "{UNINSTALL_NAME}" en la carpeta del juego.')
    pause_exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nERROR inesperado: {e!r}")
        pause_exit(1)
