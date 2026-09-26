"""Detecta posibles errores de género en la traducción usando translation/characters.json.

En passages con UN solo hablante (sin contar al jugador), revisa la narración en español:
si el hablante es hombre y aparece "tu pasajera"/"tu clienta", o es mujer y aparece
"tu pasajero"/"tu cliente" (masc.), lo reporta. Solo informa; no modifica nada.

  python tools/check_gender.py [--all]
"""
import collections
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nc.common import DB_DIALOGS, ROOT, read_jsonl

FEM = re.compile(r"\btu (pasajera|clienta)\b", re.I)
MASC = re.compile(r"\btu pasajero\b", re.I)

if __name__ == "__main__":
    chars = json.load(open(os.path.join(ROOT, "translation", "characters.json"), encoding="utf-8"))
    issues = []
    for f in sorted(glob.glob(os.path.join(DB_DIALOGS, "*.jsonl"))):
        by_p = collections.defaultdict(list)
        for r in read_jsonl(f):
            by_p[r["passage"]].append(r)
        for p, rows in by_p.items():
            sps = {r["speaker"] for r in rows if r.get("speaker")}
            if len(sps) != 1:
                continue
            g = chars.get(next(iter(sps)), {}).get("gender")
            for r in rows:
                es = r.get("es") or ""
                if r["type"] != "NARRATION" or not es:
                    continue
                if (g == "M" and FEM.search(es)) or (g == "F" and MASC.search(es)):
                    issues.append((r["id"], g, r["en"], es))
    print(f"posibles errores de género: {len(issues)}")
    for i, g, en, es in issues[: None if "--all" in sys.argv else 15]:
        print(f"  [{g}] {i}\n      EN: {en[:90]}\n      ES: {es[:90]}")
