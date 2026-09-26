"""Lectura de los datos del mod ruso (solo como puente para rescatar el JSON español)."""
import glob
import os
import re

from .common import REF_RU, is_structural, norm, read_json, split_line


def load_passages():
    """{titulo: {"lines": [cuerpo...], "choices": {link: cuerpo}}} desde Russian_Texts."""
    out = {}
    for path in glob.glob(os.path.join(REF_RU, "Russian_Texts", "*_rus.txt")):
        cur = None
        with open(path, encoding="utf-8-sig") as f:
            for line in f:
                m = re.match(r"^===\s*(\S+)", line)
                if m:
                    cur = out.setdefault(m.group(1), {"lines": [], "choices": {}})
                    continue
                if cur is None or is_structural(line):
                    continue
                t = line.strip()
                if t.startswith("*"):
                    text, _, link = t[1:].rpartition("->")
                    if link:
                        cur["choices"][link.strip()] = split_line(text)[2]
                else:
                    cur["lines"].append(split_line(t)[2])
    return out


def load_bridge(es_mapping_path):
    """Une mapping ruso (en->ru) y español (en->es), que comparten claves.

    El español se tradujo desde el valor ruso de cada clave, así que ru[k] <-> es[k]
    es un par fiable aunque la clave inglesa esté desalineada.
    Devuelve (ru_to_es, en_to_ru, en_to_es) con claves normalizadas.
    en_to_es es la búsqueda directa: ~40% desalineada, solo sirve como sugerencia.
    """
    ru_map = read_json(os.path.join(REF_RU, "Russian_UI", "full_translation_mapping.json"))
    es_map = read_json(es_mapping_path)
    ru_to_es, en_to_ru, en_to_es = {}, {}, {}
    for k, ru in ru_map.items():
        es = es_map.get(k)
        if not ru or not es:
            continue
        ru_body, es_body = norm(split_line(ru)[2]), split_line(es)[2]
        ru_to_es.setdefault(ru_body, es_body)
        en_to_ru.setdefault(norm(split_line(k)[2]), ru_body)
    for k, es in es_map.items():
        if es and es != k:
            en_to_es.setdefault(norm(split_line(k)[2]), split_line(es)[2])
    return ru_to_es, en_to_ru, en_to_es
