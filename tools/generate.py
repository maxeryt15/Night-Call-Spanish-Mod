"""db/ + source/ -> archivos que consume el mod (build/data/).

  Spanish_Texts/<objeto>_spa.txt   diálogos compilados: passages con al menos una fila traducida. Cada passage
                                   copia TODAS las líneas del original (comandos incluidos,
                                   misma cantidad) y solo reemplaza el cuerpo visible.
                                   guiones TextAsset: archivo completo (el mod lo reemplaza entero).
  Spanish_UI/key_based_translations.json    clave de UI -> español
  Spanish_UI/full_translation_mapping.json  inglés -> español (fallback TMP) + nombres de translation/names.json

Solo usa filas TRANSLATED/REVIEW/TESTED con 'es'. Termina ejecutando validate.
Uso: python tools/generate.py
"""
import glob
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nc.common import DB, DB_DIALOGS, ROOT, SOURCE, read_json, read_jsonl, read_textasset, write_json

OUT = os.path.join(ROOT, "build", "data")
USABLE = ("TRANSLATED", "REVIEW", "TESTED")


def usable(r):
    return r["status"] in USABLE and r.get("es")


def replace_body(original, body_en, es):
    """Cambia el cuerpo al final de la línea conservando hablante/emote/sangría."""
    stripped = original.strip()
    if not stripped.endswith(body_en):
        raise ValueError(f"cuerpo no encontrado en la línea: {original!r}")
    return stripped[: len(stripped) - len(body_en)] + es


def gen_dialog(src_path, mapping):
    d = read_json(src_path)
    obj = d["object"]
    rows = {r["id"]: r for r in read_jsonl(os.path.join(DB_DIALOGS, obj + ".jsonl"))}
    for r in rows.values():  # peticiones del mapa (passengercall): se muestran en TMP
        if r["type"] == "CALL" and usable(r):
            mapping.setdefault(r["en"], r["es"])
    out, n_pass = [], 0
    for p in d["passages"]:
        title = p["title"]
        lines, choices, translated = [], [], 0
        for i, line in enumerate(p["lines"]):
            r = rows.get(f"{obj}|{title}|L{i}")
            if r and usable(r):
                lines.append(replace_body(line, r["en"], r["es"]))
                mapping.setdefault(r["en"], r["es"])
                translated += 1
            else:
                lines.append(line.strip())
        for i, c in enumerate(p["choices"]):
            r = rows.get(f"{obj}|{title}|C{i}")
            text = c["text"].strip()
            if r and usable(r):
                text = replace_body(text, r["en"], r["es"])
                mapping.setdefault(r["en"], r["es"])
                translated += 1
            choices.append(f"*{text} -> {c['link']}")
        if not translated:
            continue
        n_pass += 1
        out.append(f"=== {title}")
        out.extend(lines)
        out.extend(choices)
        out.append("")
    if out:
        path = os.path.join(OUT, "Spanish_Texts", obj + "_spa.txt")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(out))
    return n_pass


def gen_textasset(src_path, mapping):
    """Guiones TextAsset: el mod reemplaza el archivo entero, así que se escribe completo
    (líneas sin traducir quedan en inglés). Solo si hay al menos una fila traducida."""
    obj = os.path.basename(src_path)[: -len("_eng.txt")]
    rows = {r["id"]: r for r in read_jsonl(os.path.join(DB_DIALOGS, obj + ".jsonl"))}
    lines, translated = read_textasset(src_path), 0
    passage = None
    for n, line in enumerate(lines):
        if line.strip().startswith("==="):
            passage = line.strip()[3:].strip()
            continue
        r = rows.get(f"{obj}|{passage}|T{n}")
        if not (r and usable(r)):
            continue
        head, sep, link = line.rpartition("->") if r["type"] == "CHOICE" else (line, "", "")
        i = head.rfind(r["en"])
        if i < 0:
            raise ValueError(f"cuerpo no encontrado: {obj} línea {n}")
        lines[n] = head[:i] + r["es"] + head[i + len(r["en"]):] + sep + link
        mapping.setdefault(r["en"], r["es"])
        translated += 1
    if translated:
        path = os.path.join(OUT, "Spanish_Texts", obj + "_spa.txt")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(lines))
    return translated


if __name__ == "__main__":
    shutil.rmtree(os.path.join(OUT, "Spanish_Texts"), ignore_errors=True)
    mapping = {}
    files = sorted(glob.glob(os.path.join(SOURCE, "dialogs", "eng", "*.json")))
    n_pass = sum(gen_dialog(f, mapping) for f in files)
    tas = sorted(glob.glob(os.path.join(SOURCE, "textassets", "*_eng.txt")))
    n_ta = sum(1 for f in tas if gen_textasset(f, mapping))
    ui = {r["id"]: r["es"] for r in read_jsonl(os.path.join(DB, "ui.jsonl")) if usable(r)}
    for r in read_jsonl(os.path.join(DB, "ui.jsonl")):
        if usable(r):
            mapping.setdefault(r["en"], r["es"])
    write_json(os.path.join(OUT, "Spanish_UI", "key_based_translations.json"), ui)
    # Passidex y pistas: se muestran en TextMeshPro -> van al mapping TMP
    extra = [os.path.join(DB, n + ".jsonl") for n in ("reveals", "assets")]
    for r in (x for f in extra if os.path.exists(f) for x in read_jsonl(f)):
        if usable(r):
            mapping.setdefault(r["en"], r["es"])
    # nombres de hablante que se muestran en pantalla (cargos/roles): translation/names.json
    names = read_json(os.path.join(ROOT, "translation", "names.json"))
    for en, es in names.items():
        if not en.startswith("_") and en != es:
            mapping[en] = es
    write_json(os.path.join(OUT, "Spanish_UI", "full_translation_mapping.json"), mapping)
    print(f"passages generados: {n_pass} | guiones textasset: {n_ta} | claves UI: {len(ui)} | mapping TMP: {len(mapping)}")

    import validate
    sys.exit(validate.main())
