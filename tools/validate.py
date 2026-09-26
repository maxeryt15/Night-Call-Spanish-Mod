"""Validaciones. Devuelve código 1 si hay errores (no se debe instalar/publicar).

Nivel fila (db/):   placeholders {x} [x] <tag> %x% \\n iguales; mismas comillas que el
                    original; sin cirílico; sin hablante duplicado al inicio.
Nivel archivo:      cada passage de Spanish_Texts existe en el original, tiene la misma
                    cantidad de líneas, las líneas estructurales ($$, ->, {..}) son
                    idénticas, hablante/emote iguales y los links de choices iguales.
Avisos:             choices/UI con español > 1.4x el largo del inglés.
Uso: python tools/validate.py
"""
import collections
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nc.common import (all_db_files, DB, DB_DIALOGS, ROOT, SOURCE, is_structural, parse_choice, read_json,
                       read_jsonl, read_textasset, split_line)

OUT = os.path.join(ROOT, "build", "data")
TOKENS = re.compile(r"\{[^}]*\}|\[[^\]]*\]|<[^>]+>|%[A-Za-z0-9_]+%|\\n")
QUOTES = "“”«»\"‘’"
CYR = re.compile(r"[Ѐ-ӿ]")


def quote_sig(s):
    return collections.Counter(c for c in s if c in "“”«»\"")


def check_row(r, errors, warns, where):
    en, es = r["en"], r.get("es") or ""
    if not es:
        return
    if sorted(TOKENS.findall(en)) != sorted(TOKENS.findall(es)):
        errors.append(f"{where}: placeholders distintos | {en!r} -> {es!r}")
    if quote_sig(en) != quote_sig(es):
        errors.append(f"{where}: comillas distintas al original | {en[:50]!r} -> {es[:50]!r}")
    if re.match(r"^:[a-z0-9_\-]+:", es):
        errors.append(f"{where}: el español incluye el emote (debe ir solo en el original)")
    if CYR.search(es):
        errors.append(f"{where}: contiene cirílico")
    if r["type"] == "DIALOGUE" and split_line(es)[0]:
        errors.append(f"{where}: el español repite un hablante al inicio")
    if r["type"] in ("CHOICE", "UI") and len(en) >= 6 and len(es) > 1.4 * len(en):
        warns.append(f"{where}: largo {len(es)} vs {len(en)} (posible desborde)")


def parse_spa(path):
    passages, cur = {}, None
    with open(path, encoding="utf-8") as f:
        for line in f.read().split("\n"):
            if line.startswith("=== "):
                cur = passages.setdefault(line[4:].strip(), {"lines": [], "choices": []})
            elif cur is not None and line.startswith("*"):
                text, _, link = line[1:].rpartition(" -> ")
                cur["choices"].append((text, link))
            elif cur is not None and line.strip():
                cur["lines"].append(line)
    return passages


def check_textasset(obj, path, src, errors):
    """Guion completo: mismo número de líneas; solo pueden cambiar los cuerpos visibles."""
    orig = read_textasset(src)
    with open(path, encoding="utf-8") as f:
        spa = f.read().split("\n")
    if len(orig) != len(spa):
        errors.append(f"{obj}: {len(spa)} líneas vs {len(orig)} originales")
        return
    for n, (o, s) in enumerate(zip(orig, spa)):
        w = f"{obj}:{n + 1}"
        if is_structural(o) or o.strip().startswith("==="):
            if o != s:
                errors.append(f"{w}: línea estructural alterada {o.strip()!r} -> {s.strip()!r}")
            continue
        oc, sc = parse_choice(o), parse_choice(s)
        if bool(oc) != bool(sc) or (oc and oc[1] != sc[1]):
            errors.append(f"{w}: choice/link alterado")
            continue
        a, b = split_line(oc[0] if oc else o), split_line(sc[0] if sc else s)
        if a[:2] != b[:2]:
            errors.append(f"{w}: hablante/emote alterado {a[:2]} -> {b[:2]}")
        if o[: len(o) - len(o.lstrip())] != s[: len(s) - len(s.lstrip())]:
            errors.append(f"{w}: sangría alterada")


def check_file(path, errors):
    obj = os.path.basename(path)[: -len("_spa.txt")]
    src = os.path.join(SOURCE, "dialogs", "eng", obj + ".json")
    ta = os.path.join(SOURCE, "textassets", obj + "_eng.txt")
    if os.path.exists(ta):
        check_textasset(obj, path, ta, errors)
        return
    if not os.path.exists(src):
        errors.append(f"{obj}: no existe el original")
        return
    orig = {p["title"]: p for p in read_json(src)["passages"]}
    for title, sp in parse_spa(path).items():
        w = f"{obj}|{title}"
        o = orig.get(title)
        if not o:
            errors.append(f"{w}: passage que no existe en el original")
            continue
        o_lines = [l.strip() for l in o["lines"] if l.strip()]
        if len(o_lines) != len(sp["lines"]):
            errors.append(f"{w}: {len(sp['lines'])} líneas vs {len(o_lines)} originales")
            continue
        for ol, sl in zip(o_lines, sp["lines"]):
            if is_structural(ol):
                if ol != sl:
                    errors.append(f"{w}: línea estructural alterada {ol!r} -> {sl!r}")
            else:
                a, b = split_line(ol), split_line(sl)
                if a[:2] != b[:2]:
                    errors.append(f"{w}: hablante/emote alterado {a[:2]} -> {b[:2]}")
        if [c["link"] for c in o["choices"]] != [l for _, l in sp["choices"]]:
            errors.append(f"{w}: links de choices distintos")
        for oc, (st, _) in zip(o["choices"], sp["choices"]):
            if split_line(oc["text"])[1] != split_line(st)[1]:
                errors.append(f"{w}: emote de choice alterado")


def main():
    errors, warns = [], []
    for f in all_db_files():
        for r in read_jsonl(f):
            check_row(r, errors, warns, r["id"])
    # sin source/ (p. ej. sesión en la nube) solo se validan filas de db/
    files = sorted(glob.glob(os.path.join(OUT, "Spanish_Texts", "*_spa.txt"))) if os.path.isdir(SOURCE) else []
    for f in files:
        check_file(f, errors)
    for e in errors[:30]:
        print("ERROR", e)
    for w in warns[:15]:
        print("aviso", w)
    print(f"validación: {len(files)} archivos, {len(errors)} errores, {len(warns)} avisos")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
