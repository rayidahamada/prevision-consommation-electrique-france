"""Audit ponctuel et borné de l'API officielle ; aucune agrégation ni prévision.

Bibliothèque standard uniquement. Les sorties restent séparées des données du projet.
"""

import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
import socket
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener
from uuid import uuid4
from zoneinfo import ZoneInfo

API = "https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/eco2mix-national-tr"
FIELDS = ("date_heure", "date", "heure", "consommation", "nature", "perimetre")
MAX_BYTES = 1_048_576


def parse_utc(value):
    """Exiger un offset explicite ; ne jamais localiser une heure naïve."""
    if not isinstance(value, str):
        raise ValueError("Horodatage non textuel.")
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        raise ValueError("Horodatage sans fuseau.")
    return stamp.astimezone(timezone.utc)


def observation_age(observed, consulted):
    """Âge signé en secondes ; ce n'est pas un délai de publication."""
    return (parse_utc(consulted) - parse_utc(observed)).total_seconds()


def local_day_hours(day):
    """Énumérer les vrais instants UTC entre deux minuits de Paris."""
    date = datetime.strptime(day, "%Y-%m-%d").date()
    zone = ZoneInfo("Europe/Paris")
    start = datetime.combine(date, datetime.min.time(), zone).astimezone(timezone.utc)
    end = datetime.combine(date + timedelta(days=1), datetime.min.time(), zone).astimezone(timezone.utc)
    return [start + timedelta(hours=i) for i in range(int((end - start).total_seconds() / 3600))]


def metadata_summary(payload):
    """Valider le dataset et conserver uniquement les métadonnées utiles."""
    if not isinstance(payload, dict) or payload.get("dataset_id") != "eco2mix-national-tr":
        raise ValueError("Identifiant ou objet de métadonnées inattendu.")
    fields = payload.get("fields")
    if not isinstance(fields, list) or any(not isinstance(f, dict) for f in fields):
        raise ValueError("Liste de champs invalide.")
    names = {f.get("name") for f in fields}
    if not set(FIELDS) <= names:
        raise ValueError("Changement de schéma : champs requis absents.")
    metas = payload.get("metas", {})
    if not isinstance(metas, dict) or not isinstance(metas.get("default", {}), dict):
        raise ValueError("Métadonnées descriptives invalides.")
    default = metas.get("default", {})
    custom = metas.get("custom", {})
    if not isinstance(custom, dict):
        raise ValueError("Métadonnées complémentaires invalides.")
    return {
        "dataset_id": payload["dataset_id"], "dataset_uid": payload.get("dataset_uid"),
        "fields": [{k: f.get(k) for k in ("name", "type", "label")} for f in fields],
        "default": {k: default.get(k) for k in ("title", "publisher", "license", "license_url",
                    "timezone", "records_count", "data_processed", "modified")},
        "custom": {k: custom.get(k) for k in ("maille-geographique", "pas-temporel",
                    "profondeur-dhistorique", "version")},
    }


def parse_records(payload, limit):
    """Distinguer réponse vide, nulls et changement structurel de schéma."""
    if not isinstance(payload, dict) or type(payload.get("total_count")) is not int:
        raise ValueError("Objet results/total_count attendu.")
    rows = payload.get("results")
    if payload["total_count"] < 0 or not isinstance(rows, list) or len(rows) > limit:
        raise ValueError("Nombre de résultats invalide.")
    if len(rows) > payload["total_count"]:
        raise ValueError("Résultats incompatibles avec total_count.")
    for row in rows:
        if not isinstance(row, dict) or not set(FIELDS) <= row.keys():
            raise ValueError("Changement de schéma : observation incomplète.")
        if any(row[k] is not None and not isinstance(row[k], str) for k in FIELDS if k != "consommation"):
            raise ValueError("Type de champ textuel inattendu.")
    return [{k: row[k] for k in FIELDS} for row in rows]


def analyse_records(rows, consulted):
    """Décrire l'échantillon sans imputation, sélection de doublon ou moyenne."""
    consultation = parse_utc(consulted)
    times, usable, missing, invalid_power = [], [], 0, 0
    invalid_time = negative = future = off_grid = calendar_mismatch = 0
    for row in rows:
        value = row["consommation"]
        finite = type(value) in (int, float) and math.isfinite(value)
        missing += value is None
        invalid_power += value is not None and not finite
        negative += finite and value < 0
        try:
            stamp = parse_utc(row["date_heure"])
        except (ValueError, TypeError, OverflowError):
            invalid_time += 1
            continue
        times.append(stamp)
        future += stamp > consultation
        off_grid += bool(stamp.minute % 15 or stamp.second or stamp.microsecond)
        local = stamp.astimezone(ZoneInfo("Europe/Paris"))
        # Comparaison descriptive avec la convention ISO de date, sans réparation.
        calendar_mismatch += (row["date"], row["heure"]) != (local.date().isoformat(), local.strftime("%H:%M"))
        if finite and value > 0 and stamp <= consultation:
            usable.append((stamp, row))
    unique = sorted(set(times))
    counts = Counter((b - a).total_seconds() for a, b in zip(unique, unique[1:]))
    multiplicity = Counter(times)
    unique_usable = [pair for pair in usable if multiplicity[pair[0]] == 1]
    latest = max(unique_usable, key=lambda pair: pair[0]) if unique_usable else None
    latest_time = max(times).isoformat() if times else None
    return {
        "rows": len(rows), "unique_timestamps": len(unique),
        "duplicate_timestamp_excess": len(times) - len(unique),
        "first_timestamp_utc": min(times).isoformat() if times else None,
        "last_timestamp_utc": latest_time,
        "last_timestamp_age_seconds": observation_age(latest_time, consulted) if latest_time else None,
        "latest_usable": latest[1] if latest else None,
        "latest_usable_age_seconds": observation_age(latest[0].isoformat(), consulted) if latest else None,
        "finite_positive_past_rows": len(usable), "null_consumption": missing,
        "nature_counts": dict(Counter(str(row["nature"]) for row in rows)),
        "perimetre_counts": dict(Counter(str(row["perimetre"]) for row in rows)),
        "invalid_consumption": invalid_power, "negative_consumption": negative,
        "zero_consumption": sum(type(r["consommation"]) in (int, float) and r["consommation"] == 0 for r in rows),
        "invalid_timestamps": invalid_time, "future_timestamps": future,
        "off_quarterhour_grid": off_grid, "source_calendar_mismatch_iso": calendar_mismatch,
        "step_seconds_counts": {str(int(k)): v for k, v in sorted(counts.items())},
        "missing_quarterhours_between_sample_bounds": (
            int((unique[-1] - unique[0]).total_seconds() / 900) + 1 - len(unique)
            if unique and not off_grid else None),
        "publication_delay_proven": False,
        "limits": ["Échantillon borné, pas un audit exhaustif.",
                   "Valeur positive finie : critère exploratoire, pas certification physique.",
                   "Âge du timestamp, pas durée depuis la première publication.",
                   "Aucun champ nature n'est converti en statut_rte."],
    }


class NoRedirect(HTTPRedirectHandler):
    """Ne pas suivre automatiquement une redirection hors du point d'accès choisi."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request_json(url, params, timeout=15, opener=None):
    """GET public sans identifiant, taille plafonnée et erreurs consignées sans corps HTTP."""
    full_url = url + ("?" + urlencode(params) if params else "")
    event = {"url": url, "params": params, "called_url": full_url,
             "requested_at_utc": datetime.now(timezone.utc).isoformat(),
             "http_status": None, "rows": None, "error": None}
    payload = None
    try:
        client = opener or build_opener(NoRedirect())
        request = Request(full_url, headers={"Accept": "application/json", "User-Agent": "MIASHS-feasibility-audit/1.0"})
        started = time.monotonic()
        with client.open(request, timeout=timeout) as response:
            event["http_status"] = response.status
            event["http_date"] = response.headers.get("Date")
            event["http_age"] = response.headers.get("Age")
            event["content_type"] = response.headers.get("Content-Type")
            if response.status != 200:
                raise ValueError("HTTP non réussi.")
            if response.headers.get_content_type() != "application/json":
                raise ValueError("Type de contenu non JSON.")
            parts, size = [], 0
            while True:
                if time.monotonic() - started > timeout:
                    raise TimeoutError("Budget de lecture dépassé.")
                part = response.read(min(65536, MAX_BYTES + 1 - size))
                if not part:
                    break
                parts.append(part)
                size += len(part)
                if size > MAX_BYTES:
                    raise ValueError("Réponse dépassant 1 Mio.")
            body = b"".join(parts)
            event["bytes"] = len(body)
            event["body_sha256"] = hashlib.sha256(body).hexdigest()
            payload = json.loads(body)
            # Rejeter aussi les constantes NaN/Infinity acceptées par défaut par Python.
            json.dumps(payload, allow_nan=False)
    except HTTPError as exc:
        event["http_status"] = exc.code
        event["error"] = f"HTTPError: HTTP {exc.code}"
        # Ne conserver ni corps d'erreur, ni en-têtes d'authentification/cookies.
        exc.close()
    except (URLError, OSError, ValueError, TimeoutError, socket.timeout) as exc:
        if isinstance(exc, URLError):
            event["error"] = f"URLError: {exc.reason}"
        else:
            event["error"] = f"{type(exc).__name__}: {exc}"
        payload = None
    event["received_at_utc"] = datetime.now(timezone.utc).isoformat()
    return payload, event


def run(output_dir, pages=2, page_size=96, timeout=15):
    """Au plus quatre appels ; nouvelle exécution isolée, aucune relance automatique."""
    if not 1 <= pages <= 2 or not 1 <= page_size <= 100 or not 1 <= timeout <= 30:
        raise ValueError("Bornes : 1–2 pages, 1–100 lignes/page, délai 1–30 s.")
    root = Path(output_dir).resolve()
    project = Path(__file__).resolve().parents[2]
    if root == project / "data" or project / "data" in root.parents:
        raise ValueError("Les données du projet ne sont pas un dossier de sortie autorisé.")
    run_dir = root / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "_" + uuid4().hex[:8])
    run_dir.mkdir(parents=True, exist_ok=False)
    result = {"started_at_utc": datetime.now(timezone.utc).isoformat(),
              "status": "incomplete", "api": API,
              "parameters": {"pages": pages, "page_size": page_size, "timeout_seconds": timeout,
                             "max_response_bytes": MAX_BYTES, "authentication": "none"},
              "requests": [], "metadata": None, "pages": [], "oldest_visible": None}
    payload, event = request_json(API, {}, timeout)
    result["requests"].append(event)
    if payload is not None:
        try:
            result["metadata"] = metadata_summary(payload)
        except (ValueError, TypeError) as exc:
            event["error"] = f"SchemaError: {exc}"
    if result["metadata"] is not None:
        base = {"select": ",".join(FIELDS), "timezone": "UTC"}
        for page in range(pages):
            params = {**base, "where": "date_heure <= date'" + result["started_at_utc"] + "'",
                      "order_by": "date_heure desc", "limit": page_size, "offset": page * page_size}
            payload, event = request_json(API + "/records", params, timeout)
            result["requests"].append(event)
            if payload is None:
                break
            try:
                rows = parse_records(payload, page_size)
                event["rows"] = len(rows)
                event["total_count"] = payload["total_count"]
                result["pages"].append({"request_index": len(result["requests"]) - 1,
                                        "records": rows,
                                        "audit": analyse_records(rows, event["received_at_utc"])})
            except (ValueError, TypeError, OverflowError) as exc:
                event["error"] = f"SchemaError: {exc}"
                break
            if len(rows) < page_size or (page + 1) * page_size >= payload["total_count"]:
                break
        payload, event = request_json(API + "/records", {**base, "order_by": "date_heure asc", "limit": 1}, timeout)
        result["requests"].append(event)
        if payload is not None:
            try:
                rows = parse_records(payload, 1)
                event["rows"] = len(rows)
                event["total_count"] = payload["total_count"]
                result["oldest_visible"] = rows
            except (ValueError, TypeError) as exc:
                event["error"] = f"SchemaError: {exc}"
    if result["metadata"] is not None and result["pages"] and not any(e["error"] for e in result["requests"]):
        result["status"] = "complete_sample"
    all_rows = [row for page in result["pages"] for row in page["records"]]
    if result["status"] == "complete_sample" and not all_rows:
        result["status"] = "empty_sample"
    if all_rows:
        result["combined_sample_audit"] = analyse_records(all_rows, result["requests"][-1]["received_at_utc"])
    result["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
    path = run_dir / "audit.json"
    with path.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    return path, result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent / "runs")
    parser.add_argument("--pages", type=int, default=2)
    parser.add_argument("--page-size", type=int, default=96)
    parser.add_argument("--timeout", type=float, default=15)
    args = parser.parse_args(argv)
    try:
        path, result = run(args.output_dir, args.pages, args.page_size, args.timeout)
    except (OSError, ValueError) as exc:
        print(f"Audit non lancé : {exc}")
        return 2
    print("Audit :", path.relative_to(Path.cwd()) if path.is_relative_to(Path.cwd()) else path.name)
    print("État :", result["status"])
    for event in result["requests"]:
        print(event["requested_at_utc"], "HTTP", event["http_status"], "lignes", event["rows"], event["error"] or "OK")
    return 0 if result["status"] == "complete_sample" else 1


if __name__ == "__main__":
    raise SystemExit(main())
