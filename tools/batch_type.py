"""Lote de traducción por TIPO de fila a través de toda la base (p. ej. las peticiones
del mapa, type=CALL, que están repartidas en ~145 diálogos con 1 fila cada uno).

  python tools/batch_type.py export CALL      -> work/type_CALL.in.txt + .map.tsv
  python tools/batch_type.py import CALL      <- work/type_CALL.out.tsv ("n<TAB>traducción")

Mismo formato que batch.py. Solo filas TODO; nunca toca locked/TESTED.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nc.common import ROOT, all_db_files, read_jsonl, write_jsonl

WORK = os.path.join(ROOT, "work")


def export(typ):
    out, mp, n = [f"# filas tipo {typ}"], [], 0
    for f in all_db_files():
        for r in read_jsonl(f):
            if r["type"] != typ or r["status"] != "TODO":
                continue
            n += 1
            speaker = os.path.basename(f)[:-6]
            out.append(f"{n} {speaker} | {r['en']}")
            mp.append(f"{n}\t{f}\t{r['id']}")
    if not n:
        print(f"nada pendiente de tipo {typ}")
        return
    os.makedirs(WORK, exist_ok=True)
    with open(os.path.join(WORK, f"type_{typ}.in.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out) + "\n")
    with open(os.path.join(WORK, f"type_{typ}.map.tsv"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(mp) + "\n")
    print(f"exportadas {n} filas tipo {typ} -> work/type_{typ}.in.txt")


def do_import(typ):
    mp = {}
    with open(os.path.join(WORK, f"type_{typ}.map.tsv"), encoding="utf-8") as fh:
        for line in fh:
            n, f, i = line.rstrip("\n").split("\t")
            mp[n] = (f, i)
    tr = {}
    with open(os.path.join(WORK, f"type_{typ}.out.tsv"), encoding="utf-8-sig") as fh:
        for line in fh:
            if "\t" in line:
                n, t = line.rstrip("\n").split("\t", 1)
                if t.strip():
                    tr[n.strip()] = t.strip()
    by_file = {}
    for n, t in tr.items():
        if n in mp:
            f, i = mp[n]
            by_file.setdefault(f, {})[i] = t
    done = 0
    for f, ids in by_file.items():
        rows = read_jsonl(f)
        for r in rows:
            t = ids.get(r["id"])
            if t and not r.get("locked") and r["status"] != "TESTED":
                r["es"], r["status"] = t, "TRANSLATED"
                done += 1
        write_jsonl(f, rows)
    print(f"importadas {done} de {len(mp)} filas tipo {typ}")


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] not in ("export", "import"):
        sys.exit(__doc__)
    (export if sys.argv[1] == "export" else do_import)(sys.argv[2])
