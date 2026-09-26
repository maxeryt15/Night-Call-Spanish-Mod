"""source/ (volcado del juego) -> db/ (una fila por texto visible).

db/dialogs/<objeto>.jsonl  filas de narración, diálogo y choices
                           (diálogos compilados: id objeto|passage|L<i> / C<i>;
                            guiones TextAsset *_eng: id objeto|passage|T<nº de línea>)
db/ui.jsonl                claves de LocalizationManager
db/reveals.jsonl           descripciones del Passidex (source/reveals.json)

Re-ejecutable: conserva es/status/locked/notes de filas existentes cuyo inglés no cambió.
Uso: python tools/extract.py
"""
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nc.common import (DB, DB_DIALOGS, SOURCE, is_structural, parse_choice, read_json,
                       read_jsonl, read_textasset, split_line, write_jsonl)

KEEP = ("es", "status", "locked", "notes", "hint", "hint_origin", "hint_alt")


def merge(new_rows, path):
    old = {r["id"]: r for r in read_jsonl(path)}
    for r in new_rows:
        o = old.get(r["id"])
        if o and o.get("en") == r["en"]:
            for k in KEEP:
                if k in o:
                    r[k] = o[k]
    return new_rows


def row(id_, type_, en, **extra):
    r = {"id": id_, "type": type_, "en": en}
    r.update({k: v for k, v in extra.items() if v is not None})
    r.update({"es": "", "status": "TODO", "locked": False})
    return r


def extract_dialog(path):
    d = read_json(path)
    obj = d["object"]
    rows = []
    for p in d["passages"]:
        title = p["title"]
        for i, line in enumerate(p["lines"]):
            if is_structural(line):
                continue
            speaker, emote, body = split_line(line)
            rows.append(row(f"{obj}|{title}|L{i}", "DIALOGUE" if speaker else "NARRATION",
                            body, passage=title, speaker=speaker, emote=emote))
        for i, c in enumerate(p["choices"]):
            _, emote, body = split_line(c["text"])
            rows.append(row(f"{obj}|{title}|C{i}", "CHOICE", body,
                            passage=title, emote=emote, link=c["link"]))
    out = os.path.join(DB_DIALOGS, obj + ".jsonl")
    write_jsonl(out, merge(rows, out))
    return len(rows)


def extract_textasset(path):
    obj = os.path.basename(path)[: -len("_eng.txt")]
    rows, passage = [], None
    for n, line in enumerate(read_textasset(path)):
        t = line.strip()
        if t.startswith("==="):
            passage = t[3:].strip()
            continue
        if passage is None or is_structural(line):
            continue
        ch = parse_choice(line)
        if ch:
            _, emote, body = split_line(ch[0])
            rows.append(row(f"{obj}|{passage}|T{n}", "CHOICE", body,
                            passage=passage, emote=emote, link=ch[1], source="textasset"))
            continue
        speaker, emote, body = split_line(line)
        rows.append(row(f"{obj}|{passage}|T{n}", "DIALOGUE" if speaker else "NARRATION", body,
                        passage=passage, speaker=speaker, emote=emote, source="textasset"))
    out = os.path.join(DB_DIALOGS, obj + ".jsonl")
    write_jsonl(out, merge(rows, out))
    return len(rows)


def extract_reveals():
    """Passidex: source/reveals.json (volcado de RevealScript). text[1] es el inglés
    (orden de idiomas del juego: fra, eng, jap, ger). "title" es un indicador interno."""
    path = os.path.join(SOURCE, "reveals.json")
    if not os.path.exists(path):
        return 0
    rows = [row(r["reveal_id"], "REVEAL", r["text"][1].strip(), passenger=r["passenger"])
            for r in read_json(path) if len(r["text"]) > 1 and r["text"][1].strip()]
    out = os.path.join(DB, "reveals.jsonl")
    write_jsonl(out, merge(rows, out))
    return len(rows)


def extract_ui():
    loc = read_json(os.path.join(SOURCE, "localization_eng.json"))
    rows = [row(k, "UI", v) for k, v in loc.items() if v and v.strip()]
    out = os.path.join(DB, "ui.jsonl")
    write_jsonl(out, merge(rows, out))
    return len(rows)


if __name__ == "__main__":
    files = sorted(glob.glob(os.path.join(SOURCE, "dialogs", "eng", "*.json")))
    tas = sorted(glob.glob(os.path.join(SOURCE, "textassets", "*_eng.txt")))
    # extract_dialog y extract_textasset escriben las dos a db/dialogs/<obj>.jsonl;
    # si un objeto tiene ambas fuentes, la segunda pisa a la primera y se pierden
    # filas ya traducidas en silencio. Mejor abortar y que se resuelva a mano.
    dialog_objs = {read_json(f)["object"] for f in files}
    textasset_objs = {os.path.basename(f)[: -len("_eng.txt")] for f in tas}
    collision = dialog_objs & textasset_objs
    if collision:
        sys.exit(f"extract.py: {collision} tiene diálogo y textasset a la vez; "
                 "extract_dialog/extract_textasset se pisarían entre sí, resolver a mano")
    total = sum(extract_dialog(f) for f in files)
    print(f"dialogos: {len(files)} archivos, {total} filas")
    print(f"guiones textasset: {len(tas)} archivos, {sum(extract_textasset(f) for f in tas)} filas")
    print(f"ui: {extract_ui()} filas")
    print(f"passidex (reveals): {extract_reveals()} filas")
