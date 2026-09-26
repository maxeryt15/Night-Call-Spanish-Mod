"""Memoria de traducción: reutiliza traducciones de frases idénticas en inglés.

  python tools/tm.py            completa filas TODO cuyo inglés ya tiene UNA traducción aprobada
  python tools/tm.py --review   igual, pero las deja en REVIEW en vez de TRANSLATED
  python tools/tm.py --report   solo informa inconsistencias (misma frase, varias traducciones)

Fuente de la memoria: filas TRANSLATED/TESTED (y locked). Si una frase tiene varias
traducciones distintas no se autocompleta: queda listada para decidir a mano.
Nunca toca filas locked ni con status distinto de TODO.
"""
import collections
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nc.common import DB, DB_DIALOGS, read_jsonl, write_jsonl

APPROVED = ("TRANSLATED", "TESTED")


def db_files():
    return sorted(glob.glob(os.path.join(DB_DIALOGS, "*.jsonl"))) + [os.path.join(DB, "ui.jsonl")]


def build_memory():
    mem = collections.defaultdict(collections.Counter)
    for f in db_files():
        for r in read_jsonl(f):
            if r.get("es") and (r["status"] in APPROVED or r.get("locked")):
                mem[r["en"]][r["es"]] += 1
    return mem


if __name__ == "__main__":
    mem = build_memory()
    conflicts = {en: c for en, c in mem.items() if len(c) > 1}
    if "--report" not in sys.argv:
        status = "REVIEW" if "--review" in sys.argv else "TRANSLATED"
        filled = collections.Counter()
        for f in db_files():
            rows, changed = read_jsonl(f), False
            for r in rows:
                if r.get("locked") or r["status"] != "TODO":
                    continue
                c = mem.get(r["en"])
                if c and len(c) == 1:
                    r["es"], r["status"], r["origin"] = next(iter(c)), status, "tm"
                    filled[r["en"]] += 1
                    changed = True
            if changed:
                write_jsonl(f, rows)
        print(f"memoria: {len(mem)} frases | completadas: {sum(filled.values())} filas ({len(filled)} frases) -> {status}")
        for en, n in filled.most_common(5):
            print(f"  {n:4d}x {en[:60]}")
    print(f"inconsistencias: {len(conflicts)}")
    for en, c in list(conflicts.items())[:15]:
        print(f"  {en[:50]!r}: " + " | ".join(f"{es[:40]!r} x{n}" for es, n in c.most_common()))
