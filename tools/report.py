"""Resumen del estado de db/: filas por status, sugerencias y avance por archivo.

Uso: python tools/report.py [--files]   (--files agrega tabla por archivo)
"""
import collections
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nc.common import all_db_files, DB, DB_DIALOGS, read_jsonl

if __name__ == "__main__":
    total = collections.Counter()
    per_file = []
    for f in all_db_files():
        rows = read_jsonl(f)
        c = collections.Counter(r["status"] for r in rows)
        c["hint"] = sum(1 for r in rows if r.get("hint"))
        c["locked"] = sum(1 for r in rows if r.get("locked"))
        c["filas"] = len(rows)
        total.update(c)
        per_file.append((os.path.basename(f)[:-6], c))
    print("TOTAL:", ", ".join(f"{k}={v}" for k, v in sorted(total.items())))
    if "--files" in sys.argv:
        for name, c in per_file:
            done = c["TRANSLATED"] + c["TESTED"]
            print(f"  {name:32s} {done:5d}/{c['filas']:<5d} review={c['REVIEW']:<4d} hint={c['hint']}")
