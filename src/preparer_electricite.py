"""Préparation électrique demi-horaire sans imputation ni agrégation.

Les horodatages sont des étiquettes d'observation ; aucune convention de début
ou de fin d'intervalle n'est supposée. Exécution : python -m src.preparer_electricite.
"""

import argparse
from collections import Counter, defaultdict
from contextlib import ExitStack
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
from zoneinfo import ZoneInfo

from src.odre_data import ELECTRICITY, ROOT, audit, parse_time

STEP = timedelta(minutes=30)
STATES = ("unique", "duplicate_same_power", "ambiguous", "absent")
SOURCE_KEYS = ("date_heure", "date", "heure", ELECTRICITY, "statut_rte", "flag_ignore")


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def prepare_grid(records):
    """Émettre une ligne par étiquette UTC ; conserver les positions JSON à base 1.

    Les entrées inattendues sont refusées, jamais corrigées silencieusement.
    Les listes de statuts et flags sont alignées sur les positions sources.
    """
    if not isinstance(records, list) or not records:
        raise ValueError("Un tableau non vide d'observations est requis.")
    local_zone = ZoneInfo("Europe/Paris")
    groups = defaultdict(list)
    for index, source in enumerate(records, 1):
        if not isinstance(source, dict) or not set(SOURCE_KEYS) <= source.keys():
            raise ValueError(f"Clés sources absentes à la position {index}.")
        stamp = parse_time(source["date_heure"])
        if stamp.minute not in (0, 30) or stamp.second or stamp.microsecond:
            raise ValueError(f"Horodatage hors grille à la position {index}.")
        power = source[ELECTRICITY]
        if isinstance(power, bool) or not isinstance(power, (int, float)) or not math.isfinite(power):
            raise ValueError(f"Puissance non numérique finie à la position {index}.")
        groups[stamp].append((index, source))
    stamp, last = min(groups), max(groups)
    while stamp <= last:
        sources = groups.get(stamp, [])
        powers = {source[ELECTRICITY] for _, source in sources}
        if not sources:
            state, power = "absent", None
        elif len(powers) > 1:
            state, power = "ambiguous", None
        else:
            state = "unique" if len(sources) == 1 else "duplicate_same_power"
            power = sources[0][1][ELECTRICITY]
        local = stamp.astimezone(local_zone)
        calendar_mismatches = sum(
            (source["date"], source["heure"]) !=
            (local.strftime("%d/%m/%Y"), local.strftime("%H:%M"))
            for _, source in sources
        )
        yield {
            "timestamp_utc": stamp.isoformat(),
            "timestamp_local": local.isoformat(),
            "local_date": local.date().isoformat(),
            "local_time": local.strftime("%H:%M"),
            "local_year": local.year,
            "local_month": local.month,
            "local_weekday": local.weekday(),
            "utc_offset_minutes": int(local.utcoffset().total_seconds() / 60),
            "local_fold": local.fold,
            "electricity_mw": power,
            "quality_state": state,
            "power_available": power is not None,
            "is_duplicate": len(sources) > 1,
            "is_ambiguous": state == "ambiguous",
            "is_absent": state == "absent",
            "source_count": len(sources),
            "source_positions": [index for index, _ in sources],
            "statut_rte_sources": [source["statut_rte"] for _, source in sources],
            "has_missing_source_status": any(source["statut_rte"] in (None, "") for _, source in sources),
            "flag_ignore_sources": [source["flag_ignore"] for _, source in sources],
            "source_calendar_mismatch_count": calendar_mismatches,
            "source_observations": [dict(source_position=index,
                                         **{key: source[key] for key in SOURCE_KEYS})
                                    for index, source in sources],
        }
        stamp += STEP


def validate_reference(records, source_digest, manifest, reference):
    if manifest.get("status") != "complete" or manifest.get("sha256") != source_digest:
        raise ValueError("Manifeste incomplet ou empreinte du brut différente.")
    if reference.get("input_sha256") != source_digest:
        raise ValueError("L'audit de référence ne correspond pas au brut.")
    if manifest.get("rows") != len(records):
        raise ValueError("Nombre de lignes incompatible avec le manifeste.")
    current = audit(records)
    for key, value in current.items():
        if key not in reference or reference[key] != value:
            raise ValueError(f"Divergence de l'audit de référence : {key}.")
    return current


def markdown_report(summary):
    counts = summary["counts"]
    lines = [
        "# Préparation contrôlée des données électriques — Mission 007, phase 1",
        "", "## Provenance et paramètres", "",
        "```json", json.dumps({k: v for k, v in summary.items() if k not in ("annual", "counts")},
                              ensure_ascii=False, indent=2, allow_nan=False), "```", "",
        "## Méthode et schéma", "",
        "La table JSONL UTF-8 contient un objet par étiquette UTC, dans l'ordre croissant. "
        "`timestamp_utc` est sa clé unique ; le format fichier ne porte pas d'index logiciel implicite. "
        "Le pas est de 30 minutes, bornes observées incluses. Aucune hypothèse de début/fin d'intervalle.", "",
        "`electricity_mw` conserve la puissance observée pour un créneau unique ou des variantes de même puissance. "
        "Elle vaut JSON `null` pour un conflit (`ambiguous`) ou une absence (`absent`). "
        "Aucune moyenne, interpolation ni correction temporelle. Les colonnes gazières ne sont pas fusionnées.", "",
        "`source_positions` référence les objets du tableau brut en base 1. `source_observations` conserve "
        "pour chaque variante son horodatage/calendrier brut, sa puissance, son statut et son flag. "
        "Les listes `statut_rte_sources` et `flag_ignore_sources` suivent ces positions, sans sélection. "
        "La source et son empreinte sont communes à toutes les lignes et consignées ci-dessus.", "",
        "Les colonnes locales sont dérivées avec `Europe/Paris` : date, heure, année, mois, "
        "jour de semaine (lundi = 0), offset et `local_fold` (0/1 pour désambiguïser l'heure répétée). "
        "`source_calendar_mismatch_count` conserve les discordances avec les textes sources.", "",
        "## Comptes vérifiés", "", "```json",
        json.dumps(counts, ensure_ascii=False, indent=2), "```", "",
        "« Exploitable » signifie uniquement puissance présente et non contradictoire selon les règles autorisées. "
        "Cela ne garantit ni la validité physique, ni la disponibilité historique à l'instant de prévision. "
        "Un statut manquant ou une discordance de calendrier ne supprime pas la puissance. "
        "Les indicateurs permettent une sélection scientifique ultérieure, après validation.", "",
        "## Répartition annuelle (année locale Europe/Paris)", "",
        "| Année | Grille | Exploitables | Uniques | Doublons même MW | Ambigus | Absents | Statut source manquant |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for year, counter in sorted(summary["annual"].items()):
        lines.append("| " + " | ".join(str(v) for v in (
            year, counter["expected"], counter["usable"], counter["unique"],
            counter["duplicate_same_power"], counter["ambiguous"], counter["absent"],
            counter["missing_source_status_slots"])) + " |")
    lines += ["", "## Cohérence avec le diagnostic précédent", "",
              "L'audit du brut est recalculé et comparé champ par champ à `reports/audit_observations.json` "
              "(chemin configurable). Les comptes de la table sont ensuite rapprochés du brut : "
              "sources conservées = lignes brutes ; doublons excédentaires = diagnostic ; "
              "absences = trous de grille ; créneaux non absents = instants uniques ; "
              "toutes les positions sources sont représentées exactement une fois. "
              "Le SHA-256 du brut est contrôlé avant et après, la table est relue intégralement.", "",
              "## Limites et décisions différées", "",
              "Les conflits et absences restent sans valeur. Les statuts JSON `null` restent nuls, "
              "sans propagation. Une absence de source produit des listes vides et non un statut inventé. "
              "`flag_ignore` est préservé sans interprétation ni critère de sélection. "
              "La divergence des statuts annuels et les conventions physiques non confirmées décrites dans "
              "`reports/diagnostic_anomalies_temporelles.md` restent ouvertes. "
              "Les extrêmes ou valeurs nulles/négatives éventuelles ne seraient pas corrigés par cette préparation.", "",
              "Les comptes par année sont locaux ; ne pas les confondre avec les comptes par année UTC. "
              "Le rapport contient l'empreinte du code de préparation et les versions Python/base de fuseaux. "
              "La lecture JSON en mémoire reste une limite pour des exports plus volumineux.", "",
              "Sorties créées exclusivement : une relance avec les mêmes chemins est refusée. "
              "En cas d'interruption d'écriture, un fichier partiel peut subsister sans rapport final validé ; "
              "ne pas le considérer comme un résultat complet. Aucun fichier existant n'est écrasé.", "",
              "Aucune donnée brute modifiée, aucune série horaire, aucun modèle, commit ou push. "
              "La phase 2 nécessite une validation distincte.", ""]
    return "\n".join(lines)


def run(input_path, manifest_path, audit_path, output_path, report_path):
    paths = [Path(p).resolve() for p in (input_path, manifest_path, audit_path, output_path, report_path)]
    source, manifest_file, audit_file, output, report = paths
    if len(set(paths)) != len(paths):
        raise ValueError("Les entrées et les sorties doivent avoir des chemins distincts.")
    for target in (output, report):
        if target.exists():
            raise FileExistsError(f"Sortie déjà existante : {target}")
        if target.is_relative_to(ROOT / "data/raw") or target.is_relative_to(source.parent):
            raise ValueError("Une sortie ne peut pas être écrite dans le dossier brut.")
    digest = sha256(source)
    records = json.loads(source.read_text(encoding="utf-8-sig"))
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    reference = json.loads(audit_file.read_text(encoding="utf-8"))
    diagnostic = validate_reference(records, digest, manifest, reference)
    counts, annual, positions = Counter(), defaultdict(Counter), set()
    first = last = None
    for target in (output, report):
        target.parent.mkdir(parents=True, exist_ok=True)
    # Réserver les deux sorties exclusivement avant la première écriture.
    with ExitStack() as stack:
        table_stream = stack.enter_context(output.open("x", encoding="utf-8", newline="\n"))
        report_stream = stack.enter_context(report.open("x", encoding="utf-8", newline="\n"))
        for row in prepare_grid(records):
            stamp = parse_time(row["timestamp_utc"])
            if last is not None and stamp - last != STEP:
                raise ValueError("Grille dérivée non régulière.")
            first = first or stamp
            last = stamp
            state, year = row["quality_state"], row["local_year"]
            for counter in (counts, annual[year]):
                counter["expected"] += 1
                counter[state] += 1
                counter["usable"] += int(row["power_available"])
                counter["missing_source_status_slots"] += int(row["has_missing_source_status"])
            for index in row["source_positions"]:
                if index in positions:
                    raise ValueError("Position source répétée dans la table dérivée.")
                positions.add(index)
            counts["source_rows"] += row["source_count"]
            counts["duplicate_excess"] += max(0, row["source_count"] - 1)
            counts["calendar_mismatch_source_rows"] += row["source_calendar_mismatch_count"]
            table_stream.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")
        if positions != set(range(1, len(records) + 1)):
            raise ValueError("Provenance source incomplète.")
        checks = (
            counts["expected"] == int((last - first) / STEP) + 1,
            counts["usable"] + counts["ambiguous"] + counts["absent"] == counts["expected"],
            counts["unique"] + counts["duplicate_same_power"] == counts["usable"],
            counts["source_rows"] == len(records),
            counts["expected"] - counts["absent"] == diagnostic["all_rows_time"]["unique_timestamps"],
            counts["absent"] == diagnostic["all_rows_time"]["missing_halfhour_slots_between_grid_bounds"],
            counts["duplicate_excess"] == diagnostic["all_rows_time"]["duplicate_timestamp_excess"],
            sha256(source) == digest,
        )
        if not all(checks):
            raise ValueError("Échec d'une cohérence entre brut et dérivé.")
        table_stream.flush()
        # Relire la sortie réelle et vérifier chaque ligne contre sa règle source.
        with output.open(encoding="utf-8") as stream:
            for expected in prepare_grid(records):
                if json.loads(next(stream)) != expected:
                    raise ValueError("Échec de relecture de la table.")
            if stream.read():
                raise ValueError("Lignes dérivées supplémentaires.")
        try:
            from importlib.metadata import version
            tzdata_version = version("tzdata")
        except Exception:
            tzdata_version = "base système (version non identifiée)"
        summary = {
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "source": str(source), "source_sha256": digest,
            "manifest": str(manifest_file), "manifest_sha256": sha256(manifest_file),
            "reference_audit": str(audit_file), "reference_audit_sha256": sha256(audit_file),
            "output": str(output), "output_sha256": sha256(output),
            "report": str(report), "preparation_code_sha256": sha256(Path(__file__)),
            "python": platform.python_version(), "tzdata": tzdata_version,
            "parameters": {"frequency_minutes": 30, "grid_timezone": "UTC", "local_timezone": "Europe/Paris",
                           "bounds": "observed_inclusive", "timestamp_interval_convention": "unknown",
                           "source_positions_base": 1, "power_unit": "MW (documented)",
                           "conflict_policy": "null", "missing_policy": "null", "format": "JSONL UTF-8"},
            "start_utc": first.isoformat(), "end_utc": last.isoformat(),
            "counts": dict(counts), "annual": annual,
        }
        report_stream.write(markdown_report(summary))
    print(json.dumps(summary["counts"], ensure_ascii=False, indent=2))
    print(f"Table : {output}\nRapport : {report}")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    try:
        run(args.input, args.manifest, args.audit, args.output, args.report)
    except (OSError, ValueError, TypeError, KeyError, StopIteration) as error:
        parser.exit(1, f"Préparation interrompue : {error}\n")


if __name__ == "__main__":
    main()
