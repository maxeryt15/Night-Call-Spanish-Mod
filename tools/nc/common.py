"""Utilidades compartidas: rutas, E/S JSON/JSONL y análisis de líneas Prompter."""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SOURCE = os.path.join(ROOT, "source")            # volcado del juego (no se publica)
DB = os.path.join(ROOT, "db")                    # base de traducción (fuente de verdad)
DB_DIALOGS = os.path.join(DB, "dialogs")
REF_RU = os.path.join(ROOT, "ref-russian", "data")

STATUSES = ("TODO", "TRANSLATED", "REVIEW", "TESTED")
EXTRA_DBS = ("ui", "reveals", "assets")  # db/<nombre>.jsonl fuera de dialogs/ (UI, Passidex, pistas)


def all_db_files():
    """Todos los archivos de la base: db/dialogs/*.jsonl + db/ui.jsonl + db/reveals.jsonl."""
    import glob
    files = sorted(glob.glob(os.path.join(DB_DIALOGS, "*.jsonl")))
    return files + [p for p in (os.path.join(DB, n + ".jsonl") for n in EXTRA_DBS) if os.path.exists(p)]

# Línea de diálogo: "NOMBRE: texto" / "NOMBRE : texto" (mayúsculas latinas o cirílicas)
_SPEAKER = re.compile(r"^([^\W\da-zа-яё][^:\"“«]{0,40}?)\s*:\s+(.+)$", re.S)
_EMOTE = re.compile(r"^(:[a-z0-9_\-]+:)\s*")


def read_json(path):
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")


def read_jsonl(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def write_jsonl(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def is_structural(line):
    """Líneas que nunca se traducen: comandos, comentarios, variables, links, vacías."""
    t = line.strip()
    return not t or t.startswith(("$$", "%%", "===", "{", "->", "VAR ")) or t.isdigit()


def parse_choice(line):
    """'* texto -> link' -> (texto, link) o None si la línea no es choice."""
    t = line.strip()
    if not t.startswith("*"):
        return None
    text, sep, link = t[1:].rpartition("->")
    if not sep:
        return None
    return text.strip(), link.strip()


def read_textasset(path):
    """Guion fuente Prompter (TextAsset *_eng) como lista de líneas, sin CR."""
    with open(path, encoding="utf-8-sig") as f:
        return f.read().replace("\r", "").split("\n")


def split_line(line):
    """Separa una línea visible en (speaker, emote, cuerpo). speaker/emote pueden ser None."""
    t = line.strip()
    speaker = None
    m = _SPEAKER.match(t)
    if m and m.group(1).strip() == m.group(1).strip().upper() and any(c.isalpha() for c in m.group(1)):
        speaker, t = m.group(1).strip(), m.group(2).strip()
    emote = None
    m = _EMOTE.match(t)
    if m:
        emote, t = m.group(1), t[m.end():].strip()
    return speaker, emote, t


_QUOTES = str.maketrans({"“": '"', "”": '"', "«": '"', "»": '"', "„": '"',
                         "‘": "'", "’": "'", " ": " ", " ": " "})


def norm(text):
    """Normaliza para comparar: comillas, puntos suspensivos, espacios, mayúsculas."""
    t = text.translate(_QUOTES).replace("…", "...")
    t = re.sub(r"\s+", " ", t).strip()
    return t.lower()
