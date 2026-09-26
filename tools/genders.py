"""Estima el género de cada hablante con los pronombres del texto original.

Para cada hablante mira la narración de los passages donde es el ÚNICO que habla
(así los she/he son suyos) y cuenta pronombres. Escribe translation/characters.json
conservando las entradas marcadas "source": "wiki" o "manual" (no las pisa).

  python tools/genders.py            recalcula y muestra los dudosos
Umbral: >= 80% de un pronombre y al menos 4 apariciones = seguro; si no, "?".
"""
import collections
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nc.common import DB_DIALOGS, ROOT, read_jsonl

OUT = os.path.join(ROOT, "translation", "characters.json")
SHE = re.compile(r"\b(she|her|hers|herself)\b", re.I)
HE = re.compile(r"\b(he|him|his|himself)\b", re.I)


def estimate():
    she, he, lines = collections.Counter(), collections.Counter(), collections.Counter()
    for f in glob.glob(os.path.join(DB_DIALOGS, "*.jsonl")):
        by_passage = collections.defaultdict(list)
        for r in read_jsonl(f):
            by_passage[r["passage"]].append(r)
        for rows in by_passage.values():
            speakers = {r["speaker"] for r in rows if r.get("speaker")}
            for sp in speakers:
                lines[sp] += sum(1 for r in rows if r.get("speaker") == sp)
            if len(speakers) != 1:
                continue
            sp = next(iter(speakers))
            for r in rows:
                if r["type"] == "NARRATION":
                    she[sp] += len(SHE.findall(r["en"]))
                    he[sp] += len(HE.findall(r["en"]))
    return she, he, lines


if __name__ == "__main__":
    she, he, lines = estimate()
    old = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    out = {}
    for sp in sorted(lines):
        s, h = she[sp], he[sp]
        total = s + h
        if total >= 4 and s / total >= 0.8:
            g = "F"
        elif total >= 4 and h / total >= 0.8:
            g = "M"
        else:
            g = "?"
        entry = {"gender": g, "she": s, "he": h, "lines": lines[sp], "source": "pronouns"}
        prev = old.get(sp)
        if prev and prev.get("source") in ("wiki", "manual"):
            entry = prev
        out[sp] = entry
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    c = collections.Counter(e["gender"] for e in out.values())
    print(f"hablantes: {len(out)} | M={c['M']} F={c['F']} dudosos={c['?']}")
    for sp, e in out.items():
        if e["gender"] == "?":
            print(f"  ? {sp:20s} she={e['she']} he={e['he']} lineas={e['lines']}")
