"""Compara la cobertura de db/ contra las claves inglesas del mapping del mod ruso
(ref-russian/data/Russian_UI/full_translation_mapping.json, ~31k claves) para encontrar
texto del juego que nunca volcamos. Solo informa.

  python tools/coverage_ru.py [--dump faltantes.txt]
"""
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nc.common import all_db_files, DB, DB_DIALOGS, REF_RU, ROOT, norm, read_json, read_jsonl, split_line


def known_texts():
    known = set()
    for f in all_db_files():
        for r in read_jsonl(f):
            known.add(norm(r["en"]))
    names = read_json(os.path.join(ROOT, "translation", "characters.json"))
    known.update(norm(n) for n in names)
    return known


FRENCH = re.compile(r"\b(je|vous|tu|le|la|les|des|est|pas|une|un|et|ça|c'est|qu'|mais|oui|non|ce|moi)\b", re.I)


def clean(k):
    """Quita envoltorios típicos del mapping ruso: comillas externas, << >>, choices '* x -> link'."""
    t = k.strip().replace("<<", "«").replace(">>", "»").rstrip("[#")
    if t.startswith("*") and "->" in t:
        t = t[1:].rpartition("->")[0]
    t = t.strip()
    if len(t) >= 2 and t[0] == t[-1] == '"':
        t = t[1:-1]
    return norm(split_line(t)[2])


if __name__ == "__main__":
    import bisect
    ru = read_json(os.path.join(REF_RU, "Russian_UI", "full_translation_mapping.json"))
    known = known_texts()
    ordered = sorted(known)
    missing, junk, french, partial = [], 0, 0, 0
    for k in ru:
        if not k.strip() or re.search(r"[\x00-\x08]", k) or len(k) > 2000:
            junk += 1
            continue
        body = clean(k)
        if not body or body in known or norm(k) in known:
            continue
        if len(FRENCH.findall(body)) >= 2 and not re.search(r"\b(the|you|and|is|to)\b", body):
            french += 1
            continue
        i = bisect.bisect_left(ordered, body)  # fragmento cortado de un texto conocido
        if i < len(ordered) and ordered[i].startswith(body):
            partial += 1
            continue
        if re.fullmatch(r"[a-z0-9_.\-]+", body) or len(body) < 3:  # ids/claves internas
            junk += 1
            continue
        # claves multilínea: cubiertas si todas sus líneas lo están
        parts = [norm(split_line(p)[2]) for p in k.split("\n") if p.strip()]
        if len(parts) > 1 and all(p in known for p in parts):
            continue
        if re.fullmatch(r"[\d\s.,:%€$+\-/]+", k.strip()):
            continue
        missing.append(k)
    print(f"claves rusas: {len(ru)} | basura/ids: {junk} | francés: {french} | fragmentos: {partial} | NO cubiertas: {len(missing)}")
    if "--dump" in sys.argv:
        out = sys.argv[sys.argv.index("--dump") + 1]
        with open(out, "w", encoding="utf-8") as f:
            f.write("\n".join(m.replace("\n", "\\n") for m in missing))
        print("lista completa ->", out)
