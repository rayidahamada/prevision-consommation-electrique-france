"""Acquisition officielle et audit descriptif sans agrégation (bibliothèque standard).

Exécution depuis la racine : python -m src.odre_data --help
"""

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import tempfile
from urllib.error import URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
DATASET = "consommation-quotidienne-brute"
PAGE = f"https://odre.opendatasoft.com/explore/dataset/{DATASET}/"
API = f"https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/{DATASET}"
EXPORT = API + "/exports/json"
ELECTRICITY = "consommation_brute_electricite_rte"
REQUIRED = {"date_heure", ELECTRICITY, "statut_rte"}
LICENSE = "https://github.com/etalab/licence-ouverte/blob/master/LO.md"


def write_json(path, value):
    """Refuser tout remplacement, y compris des rapports existants."""
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def read_records(path):
    with Path(path).open(encoding="utf-8-sig") as stream:
        records = json.load(stream)
    if not isinstance(records, list) or not records:
        raise ValueError("Export attendu : tableau JSON non vide.")
    if not all(isinstance(row, dict) for row in records):
        raise ValueError("Chaque observation doit être un objet JSON.")
    if not REQUIRED <= set(records[0]):
        raise ValueError("Colonnes électriques obligatoires absentes de la première ligne.")
    return records


def parse_time(value):
    if not isinstance(value, str):
        raise ValueError("Horodatage absent ou non textuel.")
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("Horodatage sans fuseau : aucune localisation implicite.")
    return result.astimezone(timezone.utc)


def audit(records):
    """Calculer des diagnostics ; ne corriger ni exclure aucune observation."""
    if not records or not all(isinstance(row, dict) for row in records):
        raise ValueError("Observations non vides requises.")
    columns = sorted(set().union(*(row.keys() for row in records)))
    if not REQUIRED <= set(columns):
        raise ValueError("Schéma électrique incomplet.")
    times, electric_times, values = [], [], []
    invalid_times = invalid_numbers = nonfinite = off_grid = 0
    missing = {key: sum(row.get(key) in (None, "") for row in records) for key in columns}
    statuses = Counter()
    for row in records:
        statuses[str(row.get("statut_rte"))] += 1
        try:
            stamp = parse_time(row.get("date_heure"))
            times.append(stamp)
            off_grid += int(stamp.minute not in (0, 30) or stamp.second != 0 or stamp.microsecond != 0)
        except (ValueError, TypeError, OverflowError):
            invalid_times += 1
            stamp = None
        raw = row.get(ELECTRICITY)
        if raw in (None, ""):
            continue
        try:
            if isinstance(raw, bool):
                raise ValueError("Booléen interdit comme puissance.")
            number = float(raw)
        except (ValueError, TypeError, OverflowError):
            invalid_numbers += 1
            continue
        if not math.isfinite(number):
            nonfinite += 1
            continue
        values.append(number)
        if stamp is not None:
            electric_times.append(stamp)

    def temporal_summary(stamps):
        unique = sorted(set(stamps))
        gaps = Counter((b - a).total_seconds() for a, b in zip(unique, unique[1:]))
        grid = [s for s in unique if s.minute in (0, 30) and s.second == s.microsecond == 0]
        expected = int((grid[-1] - grid[0]).total_seconds() / 1800) + 1 if grid else 0
        return {
            "valid_timestamps": len(stamps), "unique_timestamps": len(unique),
            "duplicate_timestamp_excess": len(stamps) - len(unique),
            "start_utc": unique[0].isoformat() if unique else None,
            "end_utc": unique[-1].isoformat() if unique else None,
            "interval_seconds_counts": {str(int(k)): v for k, v in sorted(gaps.items())},
            "missing_halfhour_slots_between_grid_bounds": expected - len(grid),
        }

    return {
        "rows": len(records), "column_count": len(columns), "columns": columns,
        "rows_missing_required_keys": sum(not REQUIRED <= row.keys() for row in records),
        "missing_by_column": missing, "invalid_timestamps": invalid_times,
        "timestamps_off_utc_halfhour_grid": off_grid,
        "timestamps_descend_in_file": any(b < a for a, b in zip(times, times[1:])),
        "all_rows_time": temporal_summary(times),
        "finite_electricity_time": temporal_summary(electric_times),
        "electricity": {
            "field": ELECTRICITY, "documented_unit": "MW (métadonnées, non inféré des valeurs)",
            "finite_count": len(values), "invalid_numeric_count": invalid_numbers,
            "nonfinite_count": nonfinite, "negative_count": sum(v < 0 for v in values),
            "zero_count": values.count(0), "min": min(values) if values else None,
            "max": max(values) if values else None, "status_counts": dict(statuses),
        },
        "gas_columns": [key for key in columns if "gaz" in key],
        "limits": ["Pas de seuil haut physique validé ; min/max sont descriptifs.",
                   "Aucune agrégation, imputation ou suppression.",
                   "Fréquence décrite sur dates uniques triées ; ordre original contrôlé séparément.",
                   "Début/fin d'intervalle et puissance moyenne/instantanée non déterminés."],
    }


def download(raw_dir=ROOT / "data" / "raw"):
    """Nouvel instantané à chaque appel ; aucun fichier antérieur remplacé.

    La métadonnée est récupérée avant l'export et conservée. Une erreur laisse
    l'instantané incomplet et son manifeste explicite ; il ne doit pas être audité.
    """
    raw_dir = Path(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    folder = Path(tempfile.mkdtemp(prefix="odre_", dir=raw_dir))
    manifest = {
        "dataset": DATASET, "source_page": PAGE, "metadata_url": API,
        "export_url": EXPORT, "requested_at_utc": datetime.now(timezone.utc).isoformat(),
        "producer_attribution": "NaTran, RTE, Teréga — ODRÉ ; électricité : RTE",
        "license": "Licence Ouverte 2.0", "license_text": LICENSE,
        "license_checked_on": "2026-11-04", "status": "incomplete",
    }
    try:
        with urlopen(API, timeout=30) as response:
            metadata = json.load(response)
        write_json(folder / "metadata.json", metadata)
        fields = {field["name"] for field in metadata.get("fields", [])}
        if not REQUIRED <= fields:
            raise ValueError("Schéma officiel courant incompatible : export annulé.")
        default = metadata.get("metas", {}).get("default", {})
        manifest["source_modified"] = default.get("modified")
        manifest["metadata_license"] = default.get("license")
        declared = str(default.get("license", "")).lower()
        if not (any(label in declared for label in ("licence ouverte", "open licence", "etalab", "licence-ouverte"))
                and any(version in declared for version in ("2.0", "v2", "/2"))):
            raise ValueError("Licence courante non reconnue : vérifier avant acquisition.")
        partial = folder / "observations.json.part"
        digest = hashlib.sha256()
        with urlopen(EXPORT, timeout=60) as response, partial.open("xb") as stream:
            manifest["http_last_modified"] = response.headers.get("Last-Modified")
            while chunk := response.read(1024 * 1024):
                digest.update(chunk)
                stream.write(chunk)
        records = read_records(partial)
        # Un répertoire nouvellement créé est réservé à cette acquisition.
        partial.rename(folder / "observations.json")
        manifest.update(status="complete", sha256=digest.hexdigest(), rows=len(records),
                        bytes=(folder / "observations.json").stat().st_size,
                        completed_at_utc=datetime.now(timezone.utc).isoformat())
    except (OSError, ValueError, KeyError, TypeError, URLError) as error:
        manifest["failure_type"] = type(error).__name__
        write_json(folder / "manifest.json", manifest)
        raise RuntimeError(f"Acquisition interrompue ({type(error).__name__}) ; manifeste : {folder / 'manifest.json'}") from error
    write_json(folder / "manifest.json", manifest)
    return folder


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("download", help="Nouvel instantané officiel dans data/raw/.")
    check = commands.add_parser("audit", help="Audit local JSON, sans accès réseau.")
    check.add_argument("input", type=Path)
    check.add_argument("--output", type=Path, help="Rapport JSON nouveau uniquement.")
    args = parser.parse_args()
    try:
        if args.command == "download":
            print(download())
        else:
            records = read_records(args.input)
            result = audit(records)
            result["input_sha256"] = hashlib.sha256(args.input.read_bytes()).hexdigest()
            result["computed_at_utc"] = datetime.now(timezone.utc).isoformat()
            if args.output:
                write_json(args.output, result)
            else:
                print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    except (OSError, ValueError, RuntimeError) as error:
        parser.exit(1, f"Erreur : {error}\n")


if __name__ == "__main__":
    main()
