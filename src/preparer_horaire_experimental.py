"""Deux alignements horaires hypothétiques ; aucun accès réseau, aucune convention certifiée."""

import argparse
from collections import Counter
from contextlib import ExitStack
import csv
from datetime import datetime, timedelta, timezone
import json
import math
from pathlib import Path
from zoneinfo import ZoneInfo

from src.odre_data import ELECTRICITY, parse_time
from src.preparer_electricite import sha256

HALF = timedelta(minutes=30)
HOUR = timedelta(hours=1)
KNOWN_STATUSES = {"Définitif", "Consolidé"}
FIELDS = ["hour_start_utc", "hour_end_utc", "hour_start_local", "electricity_mw",
          "power_computable", "target_eligible_strict", "strict_electricity_mw",
          "quality_reasons", "source_timestamps_utc", "source_positions", "source_statuses",
          "source_flags", "source_quality", "timestamp_convention"]
NESTED = {"quality_reasons", "source_timestamps_utc", "source_positions", "source_statuses",
          "source_flags", "source_quality"}


def validate_slot(row):
    required = {"timestamp_utc", "electricity_mw", "quality_state", "source_positions",
                "statut_rte_sources", "flag_ignore_sources", "source_count", "source_observations",
                "source_calendar_mismatch_count", "power_available", "is_absent", "is_ambiguous",
                "is_duplicate", "has_missing_source_status"}
    if not isinstance(row, dict) or not required <= row.keys():
        raise ValueError("Schéma de grille incomplet.")
    stamp = parse_time(row["timestamp_utc"])
    if stamp.minute not in (0, 30) or stamp.second or stamp.microsecond:
        raise ValueError("Étiquette hors grille de 30 minutes.")
    if stamp.isoformat() != row["timestamp_utc"]:
        raise ValueError("La clé doit être explicitement normalisée en UTC.")
    positions = row["source_positions"]
    if (not isinstance(positions, list) or any(type(i) is not int or i < 1 for i in positions)
            or len(set(positions)) != len(positions)):
        raise ValueError("Positions sources invalides.")
    n = len(positions)
    for key in ("statut_rte_sources", "flag_ignore_sources", "source_observations"):
        if not isinstance(row[key], list) or len(row[key]) != n:
            raise ValueError("Listes de provenance non alignées.")
    if row["source_count"] != n:
        raise ValueError("Compte de provenance incohérent.")
    powers = set()
    local = stamp.astimezone(ZoneInfo("Europe/Paris"))
    mismatches = 0
    for index, source in enumerate(row["source_observations"]):
        if (source["source_position"] != positions[index]
                or parse_time(source["date_heure"]) != stamp
                or source["statut_rte"] != row["statut_rte_sources"][index]
                or source["flag_ignore"] != row["flag_ignore_sources"][index]):
            raise ValueError("Provenance source incohérente.")
        power = source[ELECTRICITY]
        if isinstance(power, bool) or not isinstance(power, (int, float)) or not math.isfinite(power):
            raise ValueError("Puissance source non numérique finie.")
        powers.add(power)
        mismatches += int((source["date"], source["heure"]) !=
                          (local.strftime("%d/%m/%Y"), local.strftime("%H:%M")))
    expected_state = ("absent" if n == 0 else "ambiguous" if len(powers) > 1
                      else "unique" if n == 1 else "duplicate_same_power")
    expected_power = next(iter(powers)) if len(powers) == 1 else None
    if row["quality_state"] != expected_state or row["electricity_mw"] != expected_power:
        raise ValueError("Puissance ou état incompatible avec les variantes sources.")
    for key, value in {
        "power_available": expected_power is not None, "is_absent": n == 0,
        "is_ambiguous": expected_state == "ambiguous", "is_duplicate": n > 1,
        "has_missing_source_status": any(s in (None, "") for s in row["statut_rte_sources"]),
    }.items():
        if row[key] is not value:
            raise ValueError(f"Indicateur incohérent : {key}")
    if row["source_calendar_mismatch_count"] != mismatches:
        raise ValueError("Compte de discordances calendaires incohérent.")
    return stamp


def read_grid(path):
    previous = None
    with Path(path).open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            stamp = validate_slot(row)
            if previous is not None and stamp - previous != HALF:
                raise ValueError("Grille non strictement croissante ou non régulière.")
            previous = stamp
            yield stamp, row


def common_bounds(first, last):
    """Intersection des heures dont les labels nécessaires existent pour A et B."""
    start = first.replace(minute=0, second=0, microsecond=0)
    if start < first:
        start += HOUR
    end_exclusive = last.replace(minute=0, second=0, microsecond=0)
    if end_exclusive <= start:
        raise ValueError("Grille trop courte pour une heure commune aux deux hypothèses.")
    return start, end_exclusive


def make_hour(hour_start, components, convention):
    if convention not in ("experimental_start_label", "experimental_end_label"):
        raise ValueError("Convention expérimentale inconnue.")
    offsets = (timedelta(0), HALF) if convention == "experimental_start_label" else (HALF, HOUR)
    if len(components) != 2:
        raise ValueError("Deux composantes distinctes requises.")
    for component, offset in zip(components, offsets):
        if validate_slot(component) != hour_start + offset:
            raise ValueError("Mauvais alignement temporel des composantes.")
    if set(components[0]["source_positions"]) & set(components[1]["source_positions"]):
        raise ValueError("Observation source réutilisée dans deux demi-heures.")
    reasons, blockers = [], []
    for index, component in enumerate(components):
        def reason(code, scope):
            reasons.append({"component": index, "code": code, "scope": scope})
            if scope in ("power_and_strict", "strict_only"):
                blockers.append(scope)
        state = component["quality_state"]
        if state in ("absent", "ambiguous"):
            reason(state, "power_and_strict")
        elif state == "duplicate_same_power":
            reason("duplicate_resolved_same_power", "information")
        statuses = component["statut_rte_sources"]
        if any(status in (None, "") for status in statuses):
            reason("missing_rte_status", "strict_only")
        if any(status not in (None, "") and status not in KNOWN_STATUSES for status in statuses):
            reason("unknown_rte_status", "strict_only")
        if component["source_calendar_mismatch_count"]:
            reason("source_calendar_mismatch", "strict_only")
    all_statuses = [status for component in components for status in component["statut_rte_sources"]]
    if len(set(all_statuses)) > 1:
        reasons.append({"component": None, "code": "mixed_source_statuses", "scope": "strict_only"})
        blockers.append("strict_only")
    computable = "power_and_strict" not in blockers
    strict = computable and not blockers
    # La moyenne porte sur deux créneaux résolus, jamais sur leurs variantes.
    hourly_power = ((components[0]["electricity_mw"] + components[1]["electricity_mw"]) / 2
                    if computable else None)
    return {
        "hour_start_utc": hour_start.isoformat(), "hour_end_utc": (hour_start + HOUR).isoformat(),
        "hour_start_local": hour_start.astimezone(ZoneInfo("Europe/Paris")).isoformat(),
        "electricity_mw": hourly_power, "power_computable": computable,
        "target_eligible_strict": strict, "strict_electricity_mw": hourly_power if strict else None,
        "quality_reasons": reasons,
        "source_timestamps_utc": [c["timestamp_utc"] for c in components],
        "source_positions": [c["source_positions"] for c in components],
        "source_statuses": [c["statut_rte_sources"] for c in components],
        "source_flags": [c["flag_ignore_sources"] for c in components],
        "source_quality": [{k: c[k] for k in ("quality_state", "source_count",
                           "source_calendar_mismatch_count", "has_missing_source_status")}
                           for c in components],
        "timestamp_convention": convention,
    }


def serialize(row):
    return {key: (json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
                  if key in NESTED or value is None or isinstance(value, bool) else value)
            for key, value in row.items()}


def paired_hours(path, start, end):
    window = []
    for stamp, row in read_grid(path):
        window.append((stamp, row))
        if len(window) > 3:
            window.pop(0)
        if len(window) == 3:
            hour_start = window[0][0]
            if hour_start.minute == 0 and start <= hour_start < end:
                yield (make_hour(hour_start, [window[0][1], window[1][1]], "experimental_start_label"),
                       make_hour(hour_start, [window[1][1], window[2][1]], "experimental_end_label"))


def check_csv(path, start, end, convention):
    count, computable, strict = 0, 0, 0
    with Path(path).open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != FIELDS:
            raise ValueError("Schéma CSV incorrect.")
        for row in reader:
            stamp = start + count * HOUR
            if (row["hour_start_utc"] != stamp.isoformat()
                    or row["hour_end_utc"] != (stamp + HOUR).isoformat()
                    or row["timestamp_convention"] != convention):
                raise ValueError("Clé, bornes ou scénario CSV incorrects.")
            for key in NESTED:
                json.loads(row[key])
            power = json.loads(row["electricity_mw"])
            can_compute = json.loads(row["power_computable"])
            is_strict = json.loads(row["target_eligible_strict"])
            strict_power = json.loads(row["strict_electricity_mw"])
            if ((power is not None) != can_compute or (strict_power is not None) != is_strict
                    or is_strict and (not can_compute or strict_power != power)):
                raise ValueError("Puissance et qualité CSV incohérentes.")
            count += 1
            computable += int(can_compute)
            strict += int(is_strict)
    if count != int((end - start) / HOUR):
        raise ValueError("Nombre de lignes horaires incorrect.")
    return {"hours": count, "power_computable": computable,
            "not_computable": count - computable, "target_eligible_strict": strict,
            "not_strict": count - strict}


def run(input_path, expected_digest, start_output, end_output, report_path):
    source, out_a, out_b, report = [Path(p).resolve() for p in (input_path, start_output, end_output, report_path)]
    if len({source, out_a, out_b, report}) != 4:
        raise ValueError("Chemins distincts requis.")
    for target in (out_a, out_b, report):
        if target.exists():
            raise FileExistsError(f"Sortie existante, écrasement refusé : {target}")
    digest = sha256(source)
    if digest.lower() != expected_digest.lower():
        raise ValueError("Empreinte de la grille différente de celle attendue.")
    first = last = None
    grid_counts = Counter()
    source_positions = set()
    for stamp, row in read_grid(source):
        first = first or stamp
        last = stamp
        grid_counts["rows"] += 1
        grid_counts[row["quality_state"]] += 1
        for index in row["source_positions"]:
            if index in source_positions:
                raise ValueError("Provenance répétée entre créneaux.")
            source_positions.add(index)
    if first is None:
        raise ValueError("Grille vide.")
    start, end = common_bounds(first, last)
    counts = [Counter(), Counter()]
    for target in (out_a, out_b, report):
        target.parent.mkdir(parents=True, exist_ok=True)
    with ExitStack() as stack:
        streams = [stack.enter_context(target.open("x", encoding="utf-8", newline="")) for target in (out_a, out_b)]
        narrative = stack.enter_context(report.open("x", encoding="utf-8", newline="\n"))
        writers = [csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n") for stream in streams]
        for writer in writers:
            writer.writeheader()
        expected_hour = start
        for pair in paired_hours(source, start, end):
            if pair[0]["hour_start_utc"] != expected_hour.isoformat() or pair[1]["hour_start_utc"] != expected_hour.isoformat():
                raise ValueError("Heures manquantes ou désalignées entre scénarios.")
            for writer, row, counter in zip(writers, pair, counts):
                writer.writerow(serialize(row))
                counter["hours"] += 1
                counter["power_computable"] += int(row["power_computable"])
                counter["target_eligible_strict"] += int(row["target_eligible_strict"])
            expected_hour += HOUR
        if expected_hour != end or sha256(source) != digest:
            raise ValueError("Fin de grille incohérente ou entrée modifiée.")
        for stream in streams:
            stream.flush()
        checked = [check_csv(path, start, end, convention) for path, convention in (
            (out_a, "experimental_start_label"), (out_b, "experimental_end_label"))]
        for computed, reloaded in zip(counts, checked):
            if any(computed[k] != reloaded[k] for k in ("hours", "power_computable", "target_eligible_strict")):
                raise ValueError("Comptes CSV différents après relecture.")
        # Comparaison de chaque champ sérialisé aux règles sources, après relecture.
        with out_a.open(encoding="utf-8", newline="") as a, out_b.open(encoding="utf-8", newline="") as b:
            readers = (csv.DictReader(a), csv.DictReader(b))
            for pair in paired_hours(source, start, end):
                for reader, expected_row in zip(readers, pair):
                    expected_serialized = {k: str(v) for k, v in serialize(expected_row).items()}
                    if next(reader) != expected_serialized:
                        raise ValueError("CSV différent des composantes ou de la provenance.")
            if any(next(reader, None) is not None for reader in readers):
                raise ValueError("Lignes CSV supplémentaires.")
        if sha256(source) != digest:
            raise ValueError("Grille modifiée pendant les vérifications.")
        info = {"input": str(source), "input_sha256": digest, "grid_counts": dict(grid_counts),
                "grid_first_label": first.isoformat(), "grid_last_label": last.isoformat(),
                "hour_start_first": start.isoformat(), "hour_end_last": end.isoformat(),
                "script_sha256": sha256(Path(__file__)),
                "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "outputs": [{"path": str(path), "sha256": sha256(path), **counter}
                            for path, counter in zip((out_a, out_b), checked)]}
        narrative.write(report_text(info))
    print(json.dumps(info, ensure_ascii=False, indent=2))
    return info


def report_text(info):
    return """# Préparation horaire expérimentale — Mission 008

## Hypothèses et portée

Ces deux CSV sont expérimentaux et ne confirment aucune convention physique RTE/ODRÉ.
La nature « puissance moyenne sur 30 minutes » est une hypothèse commune. Sous A,
l'étiquette t désigne [t,t+30 min) ; sous B, elle désigne [t−30 min,t).
La cible est la puissance moyenne supposée sur [h,h+1 h), étiquetée par son début UTC.

- A : `hourly_power = (halfhour_power_at_h + halfhour_power_at_h_plus_30min) / 2`.
- B : `hourly_power = (halfhour_power_at_h_plus_30min + halfhour_power_at_h_plus_1h) / 2`.

Le résultat est en MW. L'énergie hypothétique de l'heure serait cette puissance multipliée
par 1 h, en MWh ; aucune colonne d'énergie n'est produite. Aucun décalage correctif,
interpolation, sélection de conflit ou analyse exploratoire n'est effectué.

## Bornes communes et intégrité

Toutes les étiquettes nécessaires aux deux scénarios doivent appartenir à la grille.
Le premier début horaire est l'arrondi supérieur à l'heure UTC de la première étiquette.
La borne finale exclusive est l'arrondi inférieur à l'heure UTC de la dernière étiquette.
Les heures sont énumérées entre ces bornes. Les heures de bord calculables pour un seul
scénario sont exclues symétriquement, sans extrapoler. Les labels non utilisés restent
intacts dans la grille ; une borne complète en étiquettes ne garantit pas une mesure résolue.

La grille est vérifiée ligne par ligne : UTC normalisé, cadence de 30 minutes, clés uniques,
puissances et indicateurs cohérents avec les variantes et provenance non répétée entre créneaux.
Le SHA-256 attendu est fourni explicitement. L'empreinte est contrôlée avant et après.
Les sorties sont relues et chaque champ est comparé aux composantes et règles sources.

## Résultats techniques effectivement calculés

Les comptes suivants sont des contrôles de préparation, pas des statistiques descriptives
de consommation ou une comparaison des performances des scénarios. Ordre des sorties : A puis B.

```json
""" + json.dumps(info, ensure_ascii=False, indent=2) + """
```

## Politique de qualité expérimentale

`power_computable` exige deux créneaux distincts, présents, résolus et de puissance finie.
Une absence ou ambiguïté donne `electricity_mw = null`. Les doublons de même puissance
déjà résolus en phase 1 comptent comme un seul créneau ; toutes leurs références restent présentes.
Aucune moyenne des variantes contradictoires n'est permise.

`target_eligible_strict` est une admissibilité technique **sous l'hypothèse du scénario**,
pas une certification physique. Elle exige en plus : tous les statuts dans le dictionnaire
explicite {Définitif, Consolidé}, un statut homogène sur toutes les variantes des deux
créneaux et zéro discordance entre calendriers sources et conversion UTC → Europe/Paris.
Le dictionnaire provient des libellés observés et ne démontre pas une équivalence physique.
Un statut absent, inconnu ou mixte exclut du strict sans empêcher une puissance expérimentale
calculable. Aucun statut n'est inventé. `strict_electricity_mw` est null si le strict échoue.

Un doublon de même puissance ne bloque pas à lui seul le strict ; ses autres anomalies
le peuvent. `flag_ignore` est propagé sans interprétation ni filtre. Les discordances
calendaires excluent du strict mais n'entraînent aucune réparation des timestamps.

`quality_reasons` est une liste JSON d'objets : composante 0/1 (ou null pour les deux),
code et portée `information`, `strict_only` ou `power_and_strict`. Tous les motifs
sont conservés ; un motif informatif n'est pas une exclusion. Les décomptes stricts
ne doivent pas être assimilés à la couverture d'une prévision opérationnelle.

## Format et provenance

CSV UTF-8, virgule, guillemets CSV standard, fins de ligne LF, ordre UTC croissant.
Les booléens sont `true`/`false` et les puissances manquantes le littéral `null`, jamais
une chaîne vide ni zéro. Lors d'une lecture ultérieure, ces conventions doivent être
explicitement interprétées. Les nombres sont écrits sans séparateur de milliers.

Les champs multi-valeurs sont du JSON compact à l'intérieur de cellules correctement
échappées par le module CSV. `source_timestamps_utc` référence les deux créneaux dans
l'ordre de la formule. Les positions, statuts et flags sont des listes de deux listes,
alignées sur ces créneaux. Chaque sous-liste conserve toutes les variantes de la phase 1,
y compris nulls et contradictions. `source_quality` propage état, nombre de sources,
discordances calendaires et absence de statut. Les positions sont les indices base 1
des objets JSON bruts, comme documenté en phase 1. L'empreinte d'entrée et sa provenance
dans le rapport de phase 1 permettent de remonter à l'instantané brut. Les horodatages
sources attendus sont conservés même pour un créneau absent, dont les listes de positions
sont alors vides. La provenance détaillée originale demeure dans la grille inchangée.

Le champ `timestamp_convention` porte `experimental_start_label` ou
`experimental_end_label`. Les deux fichiers ont les mêmes clés et bornes horaires.
`hour_start_local` contient son offset ; deux heures locales répétées restent distinctes
en UTC. Une heure locale inexistante n'est pas créée, aucune heure répétée n'est fusionnée.

## Limites scientifiques et reproductibilité

Les supports réels, la filiation éCO2mix/ODRÉ et leur stabilité historique restent ouverts
dans `reports/etude_agregation_horaire.md`. Aucun scénario ne doit être choisi selon
la continuité ou de futures performances pour prétendre résoudre la convention physique.
Les statuts/calendriers incomplets et la disponibilité des révisions restent des limites.
Le traitement UTC ne répare pas les anomalies d'horodatage identifiées dans l'archive.

Le script requiert des chemins distincts et refuse toute sortie existante. Une interruption
peut laisser des sorties partielles sans rapport validé : ne pas les utiliser. Choisir de
nouveaux chemins pour une relance, sans supprimer les versions précédentes. Le contenu CSV
est déterministe pour une même grille, un même code et une même base de fuseaux. Le rapport
contient une date d'exécution et n'est donc pas identique octet pour octet entre exécutions.

Aucune donnée précédente modifiée, aucun entraînement, graphique, analyse exploratoire,
commit ou push. Les CSV générés doivent rester ignorés par Git.
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--output-start", type=Path, required=True)
    parser.add_argument("--output-end", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    try:
        run(args.input, args.expected_sha256, args.output_start, args.output_end, args.report)
    except (OSError, ValueError, TypeError, KeyError, StopIteration) as error:
        parser.exit(1, f"Préparation expérimentale interrompue : {error}\n")


if __name__ == "__main__":
    main()
