"""Guarda sugerencias ("hint") del JSON español heredado en db/. No traduce ni cambia status.

El JSON heredado tiene pares cruzados en ambos lados (en->ru y ru->es), por eso nada de
lo rescatado se da por bueno: queda como referencia para quien traduce.
Por cada fila TODO busca la línea rusa equivalente y, con ella, el español:
  aligned   el passage tiene la misma cantidad de líneas en inglés y ruso -> misma posición
  verified  el ruso que el mapping asigna a la frase inglesa aparece en ese passage
  choice    choices: se emparejan por link
  direct    búsqueda directa inglés->español en el JSON (la menos fiable)
hint_origin indica los caminos que dieron sugerencia; hint_alt guarda alternativas distintas.
Nunca toca filas locked ni con status distinto de TODO.

Uso: python tools/rescue.py [ruta_json_es]
"""
import collections
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nc.common import DB_DIALOGS, norm, read_jsonl, write_jsonl
from nc.russian import load_bridge, load_passages

DEFAULT_ES = os.path.expanduser(r"~\Downloads\full_translation_mapping_es.json")
CYR = re.compile(r"[Ѐ-ӿ]")


def rescue_file(path, ru_pass, ru_to_es, en_to_ru, en_to_es, stats):
    rows = read_jsonl(path)
    by_passage = collections.defaultdict(list)
    for r in rows:
        if r["type"] != "CHOICE":
            by_passage[r["passage"]].append(r)

    for r in rows:
        if r.get("locked") or r["status"] != "TODO" or r.get("hint"):
            continue
        rp = ru_pass.get(r["passage"]) or {"lines": [], "choices": {}}
        cands = {}
        if r["type"] == "CHOICE":
            ru = rp["choices"].get(r["link"])
            if ru:
                cands["choice"] = ru_to_es.get(norm(ru))
        else:
            lines = by_passage[r["passage"]]
            if len(lines) == len(rp["lines"]):
                cands["aligned"] = ru_to_es.get(norm(rp["lines"][lines.index(r)]))
            ru = en_to_ru.get(norm(r["en"]))
            if ru and ru in {norm(x) for x in rp["lines"]}:
                cands["verified"] = ru_to_es.get(ru)
        cands = {k: v for k, v in cands.items() if v}
        if not cands:
            direct = en_to_es.get(norm(r["en"]))
            if direct:
                cands["direct"] = direct
        if not cands:
            stats["sin sugerencia"] += 1
            continue
        best = cands.get("verified") or cands.get("aligned") or cands.get("choice") or cands["direct"]
        r["hint"] = best
        r["hint_origin"] = "+".join(sorted(cands))
        if len(set(cands.values())) > 1:
            r["hint_alt"] = sorted(set(cands.values()) - {best})
        if CYR.search(best):
            r["hint_origin"] += ",cirilico"
        stats[r["hint_origin"]] += 1
    write_jsonl(path, rows)


if __name__ == "__main__":
    es_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_ES
    ru_pass = load_passages()
    ru_to_es, en_to_ru, en_to_es = load_bridge(es_path)
    print(f"puente ru->es: {len(ru_to_es)} | passages rusos: {len(ru_pass)}")
    stats = collections.Counter()
    for f in sorted(glob.glob(os.path.join(DB_DIALOGS, "*.jsonl"))):
        rescue_file(f, ru_pass, ru_to_es, en_to_ru, en_to_es, stats)
    for k, v in sorted(stats.items(), key=lambda x: -x[1]):
        print(f"  {v:6d}  {k}")
