"""Une una rama de traducción (p. ej. de una sesión en la nube) a main, resolviendo
conflictos de db/ fila por fila en vez de línea por línea de git.

  python tools/merge_lote.py traduccion/lote-02

Prioridad por fila (id): locked/TESTED > traducción humana/modelo > memoria (origin=tm) > TODO.
Si ambas ramas tradujeron la misma fila, gana la rama entrante (más nueva).
Después corre tm.py y generate.py (con validación) y comitea su resultado. No hace push.
"""
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nc.common import ROOT

# En Windows, escrituras seguidas a db/*.jsonl a veces chocan con el
# antivirus/OneDrive y tiran OSError(22, 'Invalid argument') de forma
# transitoria. Reintentamos antes de darlo por error real.
WRITE_RETRIES = 8
WRITE_RETRY_DELAY = 0.4


def git(*args, check=True):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", check=check).stdout


def rank(r):
    if r is None:
        return -1
    if r.get("locked") or r["status"] == "TESTED":
        return 4
    if r["status"] == "TODO":
        return 0
    return 1 if r.get("origin") == "tm" else 2


def rows_at(ref, path):
    out = subprocess.run(["git", "show", f"{ref}:{path}"], cwd=ROOT, capture_output=True,
                         text=True, encoding="utf-8")
    return [json.loads(l) for l in out.stdout.splitlines() if l.strip()] if out.returncode == 0 else []


def resolve(path):
    ours = rows_at("HEAD", path)
    theirs = {r["id"]: r for r in rows_at("MERGE_HEAD", path)}
    merged, seen = [], set()
    for r in ours:
        t = theirs.get(r["id"])
        merged.append(t if rank(t) >= rank(r) else r)
        seen.add(r["id"])
    merged += [r for i, r in theirs.items() if i not in seen]
    text = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in merged)
    last_e = None
    for attempt in range(WRITE_RETRIES):
        try:
            with open(os.path.join(ROOT, path), "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
            break
        except OSError as e:
            last_e = e
            time.sleep(WRITE_RETRY_DELAY)
    else:
        raise last_e
    git("add", path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    branch = sys.argv[1]

    dirty = git("status", "--porcelain", "--", "db/").strip()
    if dirty:
        sys.exit("ABORTADO (main sin cambios): hay cambios sin comitear en db/; "
                  "comiteá o descartá antes de unir otra rama:\n" + dirty)

    head_before = git("rev-parse", "HEAD").strip()
    git("fetch", "-q", "origin")
    res = subprocess.run(["git", "merge", "--no-commit", "--no-ff", f"origin/{branch}"], cwd=ROOT,
                         capture_output=True, text=True, encoding="utf-8")
    conflicts = [p for p in git("diff", "--name-only", "--diff-filter=U").split() if p]
    bad = [p for p in conflicts if not p.startswith("db/")]

    def abort(msg):
        subprocess.run(["git", "merge", "--abort"], cwd=ROOT, capture_output=True)
        sys.exit(f"ABORTADO (main sin cambios): {msg}")

    if res.returncode != 0 and not conflicts:
        # git merge falló por algo que no es un conflicto de contenido resoluble
        # (rama inexistente, merge ya en curso, cambios locales en el camino, etc.)
        abort(f"git merge falló sin conflictos resolubles: {(res.stderr or res.stdout).strip()}")
    if bad:
        abort(f"conflictos fuera de db/ (resolver a mano): {bad}")
    try:
        for p in conflicts:
            resolve(p)
    except Exception as e:  # nunca dejar una unión a medias
        abort(f"error resolviendo conflictos: {e!r}")
    leftover = subprocess.run(["git", "grep", "-lE", "^(<<<<<<<|>>>>>>>)", "--cached", "--", "db/"],
                              cwd=ROOT, capture_output=True, text=True).stdout.split()
    if leftover:
        abort(f"quedaron marcas de conflicto en: {leftover}")
    commit_res = subprocess.run(["git", "commit", "-q", "--no-edit", "-m",
        f"Merge {branch} (conflictos de db resueltos por fila: {len(conflicts)})"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    head_after = git("rev-parse", "HEAD").strip()
    if head_after == head_before:
        # el commit no se creó de verdad: no seguir como si la unión hubiera pasado
        abort(f"el commit de la unión no se creó: {(commit_res.stderr or commit_res.stdout).strip()}")
    print(f"unida {branch}: {len(conflicts)} archivos con conflictos resueltos por fila")
    post_failed = False
    for cmd in (["tools/tm.py"], ["tools/generate.py"], ["tools/report.py"]):
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        out = subprocess.run([sys.executable, *cmd], cwd=ROOT, capture_output=True, text=True,
                             encoding="utf-8", env=env)
        print(out.stdout.strip().splitlines()[-1] if out.stdout.strip() else out.stderr[-300:])
        if out.returncode != 0:
            post_failed = True
            print(f"AVISO: {cmd[0]} terminó con errores (código {out.returncode}) - revisar antes de seguir uniendo ramas")

    # comitear lo que haya dejado tm.py/generate.py para no arrancar la próxima
    # unión con el árbol sucio (esa era la causa de que el merge siguiente
    # fallara en silencio).
    if git("status", "--porcelain", "--", "db/").strip():
        git("add", "db/")
        subprocess.run(["git", "commit", "-q", "-m", f"TM fill tras {branch.rsplit('/', 1)[-1]}"],
                       cwd=ROOT, capture_output=True)
        print(f"TM fill tras {branch} comiteado")

    if post_failed:
        sys.exit(1)
