"""Lotes de traducción con contexto, en formato compacto (ahorra tokens).

  python tools/batch.py export <objeto|ui> [--size 60] [--all] [--hints] [--prefix UI.MENU,UI.PAUSE] [--force]
      Escribe work/<objeto>.in.txt con las próximas filas TODO (o todas con --all),
      agrupadas por passage, con hablante y link de choices. --hints agrega la sugerencia
      heredada (poco fiable: muchas son de otra línea).
      Y work/<objeto>.map.tsv (n -> id) para el import.
      Si ya hay un work/<objeto>.map.tsv de un export anterior sin importar, se
      niega a pisarlo (perdería la correspondencia con un .out.tsv ya escrito
      para esos mismos números de línea) salvo que se pase --force.
  python tools/batch.py import <objeto>
      Lee work/<objeto>.out.tsv ("n<TAB>traducción" por línea) y guarda en db/
      con status TRANSLATED. No toca filas locked ni TESTED. Al terminar borra
      el .map.tsv/.out.tsv usados, para que el próximo export no colisione.

Formato de .in.txt:
  == passage-titulo
  12 N  | narración inglesa            (N=narración, C->link = choice, NOMBRE = diálogo)
     ~ sugerencia heredada (poco fiable)
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nc.common import EXTRA_DBS, DB, DB_DIALOGS, ROOT, read_jsonl, write_jsonl

WORK = os.path.join(ROOT, "work")
EMOTE = re.compile(r"^:[a-z0-9_\-]+:\s*")  # el emote vive en el original; nunca en "es"


def db_path(obj):
    if obj in EXTRA_DBS:
        return os.path.join(DB, obj + ".jsonl")
    return os.path.join(DB_DIALOGS, obj + ".jsonl")


def export(obj, size, include_all, hints, prefix="", force=False):
    map_path = os.path.join(WORK, obj + ".map.tsv")
    if os.path.exists(map_path) and not force:
        # Un export anterior de este objeto todavía no se importó. Si lo
        # pisamos, un work/<obj>.out.tsv ya escrito (o a medio escribir)
        # quedaría con números de línea que ya no corresponden a las mismas
        # filas, y el import aplicaría traducciones a la fila equivocada sin
        # avisar. Importá ese lote primero, o pasá --force para descartarlo.
        sys.exit(f"{obj}: ya existe work/{obj}.map.tsv sin importar; "
                 f"corré 'batch.py import {obj}' primero, o pasá --force para descartarlo")
    rows = read_jsonl(db_path(obj))
    pending = [r for r in rows if (include_all or r["status"] == "TODO") and r["id"].startswith(tuple(prefix.split(",")))]
    chosen = []
    # completa passages enteros para no cortar el contexto
    for r in pending:
        if len(chosen) >= size and (r.get("passage") is None or r.get("passage") != chosen[-1].get("passage")):
            break
        chosen.append(r)
    if not chosen:
        print("nada pendiente en", obj)
        return
    os.makedirs(WORK, exist_ok=True)
    out, mp, last = [f"# {obj}"], [], None
    for n, r in enumerate(chosen, 1):
        if r.get("passage") != last:
            out.append(f"== {r.get('passage', 'UI')}")
            last = r.get("passage")
        tag = {"NARRATION": "N", "CHOICE": f"C->{r.get('link', '')}", "UI": r["id"]}.get(r["type"], r.get("speaker", "?"))
        emote = (r.get("emote") + " ") if r.get("emote") else ""
        out.append(f"{n} {tag} | {emote}{r['en']}")
        if hints and r.get("hint"):
            out.append(f"   ~ {r['hint']}")
        mp.append(f"{n}\t{r['id']}")
    with open(os.path.join(WORK, obj + ".in.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out) + "\n")
    with open(map_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(mp) + "\n")
    out_tsv = os.path.join(WORK, obj + ".out.tsv")
    if force and os.path.exists(out_tsv):
        os.remove(out_tsv)  # el out.tsv viejo ya no corresponde a este map.tsv nuevo
    left = len(pending) - len(chosen)
    print(f"{obj}: exportadas {len(chosen)} filas ({left} pendientes después) -> work/{obj}.in.txt")


def load_tsv(path):
    d = {}
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            line = line.rstrip("\n")
            if "\t" in line:
                k, v = line.split("\t", 1)
                d[k.strip()] = v.strip()
    return d


def do_import(obj):
    map_path = os.path.join(WORK, obj + ".map.tsv")
    out_path = os.path.join(WORK, obj + ".out.tsv")
    ids = load_tsv(map_path)
    tr = load_tsv(out_path)
    by_id = {ids[n]: t for n, t in tr.items() if n in ids and t}
    rows = read_jsonl(db_path(obj))
    done = skipped = 0
    for r in rows:
        t = by_id.get(r["id"])
        if t is None:
            continue
        if r.get("locked") or r["status"] == "TESTED":
            skipped += 1
            continue
        r["es"], r["status"] = EMOTE.sub("", t, count=1).strip(), "TRANSLATED"
        done += 1
    write_jsonl(db_path(obj), rows)
    missing = len(ids) - len(by_id)
    print(f"{obj}: importadas {done}, omitidas (locked/tested) {skipped}, sin traducción en el lote {missing}")
    for p in (map_path, out_path):
        if os.path.exists(p):
            os.remove(p)


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] not in ("export", "import"):
        sys.exit(__doc__)
    cmd, obj = sys.argv[1], sys.argv[2]
    if cmd == "export":
        size = int(sys.argv[sys.argv.index("--size") + 1]) if "--size" in sys.argv else 60
        prefix = sys.argv[sys.argv.index("--prefix") + 1] if "--prefix" in sys.argv else ""
        export(obj, size, "--all" in sys.argv, "--hints" in sys.argv, prefix, "--force" in sys.argv)
    else:
        do_import(obj)
