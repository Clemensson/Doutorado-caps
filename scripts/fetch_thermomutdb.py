"""Baixa todos os registros do ThermoMutDB 2.0 pela API /api/v1/records.

Uso:
    python -I scripts/fetch_thermomutdb.py <base_url> <out_dir>

Grava em <out_dir>:
    thermomutdb_records.jsonl  um registro por linha, exatamente como a API devolve
    thermomutdb_records.csv    tabela achatada (foldx_energy_terms vira foldx_<termo>)
    manifest.json              URL, data, total declarado, contagem, SHA-256

Só usa a biblioteca padrão. A API pagina com page/per_page e limita
per_page a 500.
"""
import csv
import datetime as dt
import hashlib
import json
import sys
import time
import urllib.request
from pathlib import Path

PER_PAGE = 500  # o servidor ignora valores maiores


def get_json(url, tries=4):
    for k in range(tries):
        try:
            req = urllib.request.Request(
                url, headers={"accept": "application/json", "User-Agent": "research-fetch/1.0"}
            )
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)
        except Exception as e:  # rede instável no túnel: tenta de novo
            if k == tries - 1:
                raise
            print(f"  falhou ({e}); nova tentativa", file=sys.stderr)
            time.sleep(2 ** (k + 1))


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main(base, out_dir):
    base = base.rstrip("/")
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    started = dt.datetime.now(dt.timezone.utc).isoformat()

    rows, total, page = [], None, 1
    while True:
        url = f"{base}/api/v1/records?page={page}&per_page={PER_PAGE}"
        d = get_json(url)
        total = d["total"] if total is None else total
        rows.extend(d["rows"])
        print(f"página {page}: +{len(d['rows'])} (acumulado {len(rows)}/{total})")
        if not d["rows"] or len(rows) >= total:
            break
        page += 1
        time.sleep(0.5)

    ids = [r["id"] for r in rows]
    if len(set(ids)) != len(ids):
        sys.exit(f"ids duplicados entre páginas: {len(ids) - len(set(ids))}")
    if len(rows) != total:
        sys.exit(f"contagem {len(rows)} difere do total declarado {total}")
    rows.sort(key=lambda r: r["id"])

    jsonl = out / "thermomutdb_records.jsonl"
    with open(jsonl, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    def flat(r):
        r = dict(r)
        terms = r.pop("foldx_energy_terms", None) or {}
        for k, v in terms.items():
            r["foldx_" + k.replace(" ", "_")] = v
        return r

    flats = [flat(r) for r in rows]
    cols = list(dict.fromkeys(k for r in flats for k in r))
    csv_path = out / "thermomutdb_records.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(flats)

    manifest = {
        "source": f"{base}/api/v1/records",
        "api_doc": f"{base}/api/v1/swagger.json",
        "per_page": PER_PAGE,
        "pages": page,
        "started_utc": started,
        "finished_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "total_declared": total,
        "n_records": len(rows),
        "max_update_date": max((r.get("update_date") or "") for r in rows),
        "files": {
            p.name: {"bytes": p.stat().st_size, "sha256": sha256(p)} for p in (jsonl, csv_path)
        },
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
