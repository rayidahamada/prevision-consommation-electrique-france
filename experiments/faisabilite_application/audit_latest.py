"""Contrôle ponctuel du dernier timestamp, sans pagination ni agrégation de puissance.

Sans --execute : afficher uniquement le plan, sans réseau ni fichier créé.
"""

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
from uuid import uuid4

from experiments.faisabilite_application.inspect_eco2mix_api import (
    API, FIELDS, observation_age, parse_records, parse_utc, request_json,
)


def build_queries(cutoff):
    """Même filtre et borne UTC immuable pour les deux requêtes indépendantes."""
    cutoff = parse_utc(cutoff).isoformat()
    where = ("consommation is not null and consommation > 0 and date_heure is not null "
             "and date_heure <= date'" + cutoff + "'")
    common = {"where": where, "timezone": "UTC", "limit": 1}
    return [
        {**common, "select": ",".join(FIELDS), "order_by": "date_heure desc"},
        {**common, "select": "max(date_heure) as last_timestamp,count(*) as eligible_count"},
    ]


def compare_responses(first, control, received, cutoff):
    """Comparer maximum agrégé et première ligne ; aucune preuve de publication."""
    rows = parse_records(first, 1)
    if (not isinstance(control, dict) or type(control.get("total_count")) is not int
            or control["total_count"] < 0 or not isinstance(control.get("results"), list)
            or len(control["results"]) != 1 or not isinstance(control["results"][0], dict)):
        raise ValueError("Schéma de contrôle agrégé inattendu.")
    aggregate = control["results"][0]
    if not {"last_timestamp", "eligible_count"} <= aggregate.keys():
        raise ValueError("Colonnes du maximum ou du comptage absentes.")
    count = aggregate["eligible_count"]
    if type(count) is not int or count < 0:
        raise ValueError("Comptage agrégé invalide.")
    if not rows:
        if first["total_count"] != 0 or count != 0 or aggregate["last_timestamp"] is not None:
            raise ValueError("Résultats vides incompatibles avec les compteurs.")
        return {"status": "empty", "publication_delay_proven": False}
    if first["total_count"] < 1 or count < 1:
        raise ValueError("Compteurs incompatibles avec une observation.")
    row = rows[0]
    value = row["consommation"]
    if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
        raise ValueError("Consommation positive finie requise.")
    stamp = parse_utc(row["date_heure"])
    maximum = parse_utc(aggregate["last_timestamp"])
    if stamp > parse_utc(cutoff) or maximum > parse_utc(cutoff) or stamp > parse_utc(received):
        raise ValueError("Horodatage futur ou hors du filtre préparé.")
    same_time = stamp == maximum
    same_count = first["total_count"] == count
    return {
        "status": "consistent_evidence" if same_time and same_count else "inconsistent",
        "returned_observation": row, "aggregate_max_utc": maximum.isoformat(),
        "same_timestamp": same_time, "same_filtered_count": same_count,
        "first_total_count": first["total_count"], "aggregate_eligible_count": count,
        "received_at_utc_for_age": received,
        "observation_age_seconds": observation_age(row["date_heure"], received),
        "publication_delay_proven": False,
        "limits": ["Deux réponses successives, pas une transaction ni une preuve de stabilité.",
                   "Maximum sous filtre et borne de consultation, pas toutes les qualités du dataset.",
                   "Unicité et absence de valeurs contradictoires au maximum non vérifiées.",
                   "Une cohérence locale ne résout pas la convention physique A/B."],
    }


def execute(output_dir, timeout=15):
    """Deux requêtes au maximum, sans relance ; journal distinct même en cas d'échec."""
    if not 1 <= timeout <= 30:
        raise ValueError("Délai requis entre 1 et 30 secondes.")
    root = Path(output_dir).resolve()
    data = Path(__file__).resolve().parents[2] / "data"
    if root == data or data in root.parents:
        raise ValueError("Écriture interdite dans les données du projet.")
    directory = root / ("latest_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "_" + uuid4().hex[:8])
    directory.mkdir(parents=True, exist_ok=False)
    cutoff = datetime.now(timezone.utc).isoformat()
    queries = build_queries(cutoff)
    result = {"cutoff_utc": cutoff, "status": "incomplete", "requests": [], "responses": [],
              "limits": "Audit minimal de cohérence, sans garantie opérationnelle."}
    for params in queries:
        payload, event = request_json(API + "/records", params, timeout)
        result["requests"].append(event)
        result["responses"].append(payload)
        if payload is None:
            break
    if len(result["responses"]) == 2 and all(v is not None for v in result["responses"]):
        try:
            result["comparison"] = compare_responses(*result["responses"], result["requests"][0]["received_at_utc"], cutoff)
            result["status"] = result["comparison"]["status"]
        except (ValueError, TypeError, OverflowError) as exc:
            result["schema_error"] = str(exc)
    path = directory / "audit_latest.json"
    with path.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    return path, result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="Effectuer les requêtes réseau préparées.")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent / "runs")
    parser.add_argument("--timeout", type=float, default=15)
    args = parser.parse_args(argv)
    if not args.execute:
        print(json.dumps({"mode": "plan_only", "endpoint": API + "/records",
                          "queries": build_queries(datetime.now(timezone.utc).isoformat())}, indent=2))
        return 0
    try:
        path, result = execute(args.output_dir, args.timeout)
    except (ValueError, OSError) as exc:
        print(f"Audit non lancé : {exc}")
        return 2
    print("Journal :", path.relative_to(Path.cwd()) if path.is_relative_to(Path.cwd()) else path.name)
    print("État :", result["status"])
    print(json.dumps(result.get("comparison", {}), ensure_ascii=True, indent=2))
    for event in result["requests"]:
        print(event["requested_at_utc"], "HTTP", event["http_status"], event["error"] or "OK")
    return 0 if result["status"] == "consistent_evidence" else 1


if __name__ == "__main__":
    raise SystemExit(main())
