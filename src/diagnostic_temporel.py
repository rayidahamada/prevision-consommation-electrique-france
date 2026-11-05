"""Diagnostic local ciblé de la Mission 006 bis ; aucune écriture des données."""

from collections import Counter, defaultdict
from datetime import timedelta
import hashlib
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from src.odre_data import ELECTRICITY, ROOT, audit, parse_time


def table(headers, rows):
    return "\n".join(["| " + " | ".join(headers) + " |",
                      "|" + "|".join("---" for _ in headers) + "|"] +
                     ["| " + " | ".join(str(x) for x in row) + " |" for row in rows])


def main():
    path = ROOT / "data/raw/odre_f6gejuyq/observations.json"
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    rows = json.loads(path.read_text(encoding="utf-8"))
    manifest = json.loads((path.parent / "manifest.json").read_text(encoding="utf-8"))
    initial = json.loads((ROOT / "reports/audit_observations.json").read_text(encoding="utf-8"))
    assert digest == manifest["sha256"] == initial["input_sha256"]
    result = audit(rows)
    assert all(result[k] == v for k, v in initial.items()
               if k not in ("input_sha256", "computed_at_utc"))
    local = ZoneInfo("Europe/Paris")
    groups = defaultdict(list)
    for index, row in enumerate(rows, 1):
        groups[parse_time(row["date_heure"])].append((index, row))
    times = sorted(groups)
    duplicates = {t: vs for t, vs in sorted(groups.items()) if len(vs) > 1}
    absent = []
    for a, b in zip(times, times[1:]):
        t = a + timedelta(minutes=30)
        while t < b:
            absent.append(t)
            t += timedelta(minutes=30)
    nulls = sorted(t for t, vs in groups.items() for _, r in vs if r["statut_rte"] in (None, ""))
    conflicts = sum(len({r[ELECTRICITY] for _, r in vs}) > 1 for vs in duplicates.values())
    equal = sum(all(r == vs[0][1] for _, r in vs) for vs in duplicates.values())
    mismatches = [(i, t, r) for t, vs in groups.items() for i, r in vs
                  if (r["date"], r["heure"]) !=
                  (t.astimezone(local).strftime("%d/%m/%Y"), t.astimezone(local).strftime("%H:%M"))]
    assert len(rows) == 258576 and len(times) == 258543
    assert len(duplicates) == 33 and all(len(vs) == 2 for vs in duplicates.values())
    assert len(absent) == 31 and conflicts == 22 and equal == 0
    assert len(nulls) == len(set(nulls)) == 1440
    assert all(b - a == timedelta(minutes=30) for a, b in zip(nulls, nulls[1:]))
    assert len(mismatches) == 30
    assert Counter(r["flag_ignore"] for r in rows) == {"non": 258576}
    counts = Counter((t.astimezone(local).year, r["statut_rte"] or "null")
                     for t, vs in groups.items() for _, r in vs)
    assert sum(counts.values()) == len(rows)
    for year in range(2012, 2027):
        assert sum(counts[year, status] for status in ("Définitif", "Consolidé", "null")) > 0
    parts = ["""# Diagnostic des anomalies temporelles ODRÉ — Mission 006 bis

Analyse initiale de référence : 4 novembre 2026. Cette date décrit l'étude historique de l'instantané et ne constitue pas un horodatage de réexécution du script. Aucun nettoyage appliqué.

## 1. Traçabilité et méthode

Données : `data/raw/odre_f6gejuyq/observations.json` ; manifeste et métadonnées dans le même dossier. Audit initial : `reports/audit_observations.json`, conservé sans modification. Le manifeste indique `complete`.

Le script `src/diagnostic_temporel.py` rend les calculs reproductibles avec `.venv`, la bibliothèque standard, les fonctions existantes `audit` et `parse_time`, et `ZoneInfo('Europe/Paris')`. Il ne modifie pas les données ; il écrit uniquement ce rapport. Commande : `python -m src.diagnostic_temporel` depuis la racine. Les assertions sont propres à cet instantané et doivent échouer si son contenu change. Le rapport décrit le diagnostic de l'instantané de référence et n'établit pas l'état Git ni l'avancement actuel du projet.

Empreinte SHA-256 recalculée, égale au manifeste et au rapport initial :

`""" + digest + """`

Tous les résultats descriptifs de l'audit initial ont été recalculés et comparés par assertions. Les conversions locales ci-dessous sont calculées depuis les instants UTC, sans reconstruction à partir des chaînes `date`/`heure`.

## 2. Résultats d'ensemble

- 258 576 lignes, 12 colonnes, 258 543 instants UTC distincts.
- 33 groupes de deux occurrences, soit 66 lignes concernées et 33 occurrences excédentaires.
- Zéro paire intégralement identique ; 22 groupes avec puissances électriques contradictoires ; 11 avec même puissance mais différences sur d'autres champs.
- 31 créneaux absents entre bornes observées ; aucune conclusion hors de ces bornes.
- 1 440 statuts RTE manquants, tous JSON `null` ; aucune puissance électrique manquante.
- `flag_ignore` vaut `non` sur toutes les lignes et toutes les anomalies.
- Aucun horodatage invalide ou hors grille demi-horaire UTC. Le fichier n'est pas trié chronologiquement de façon croissante ; seuls les instants en mémoire sont triés pour le diagnostic.

Bornes UTC : `2011-12-31T23:00:00+00:00` à `2026-09-30T21:30:00+00:00`. Bornes locales : `2012-01-01T00:00:00+01:00` à `2026-09-30T23:30:00+02:00`. La grille compte 258 574 instants attendus : 258 543 présents + 31 absents. Les doublons compensent presque numériquement les trous : un total annuel seul ne valide pas la continuité.

## 3. Les 33 groupes dupliqués : liste exhaustive

Les positions A/B sont les numéros des objets dans le tableau JSON, en commençant à 1, pas des lignes du fichier texte. Les variantes suivent l'ordre du fichier. Les valeurs électriques sont en MW selon les métadonnées. Tous les groupes ont deux occurrences et les deux statuts RTE sont égaux à l'intérieur de chaque groupe.
"""]
    entries = []
    for t, vs in duplicates.items():
        (ia, a), (ib, b) = vs
        entries.append((t.isoformat(), t.astimezone(local).isoformat(), f"{ia} / {ib}",
                        f"{a['heure']} / {b['heure']}", f"{a[ELECTRICITY]} / {b[ELECTRICITY]}",
                        a["statut_rte"], "non / non", "oui" if a[ELECTRICITY] != b[ELECTRICITY] else "non"))
    parts.append(table(["UTC", "Europe/Paris", "Positions A / B", "Heures brutes A / B",
                        "MW A / B", "Statut A = B", "Flags A / B", "Conflit MW"], entries))
    parts.append("### Champs différents dans chaque groupe\n\nComparaison des 12 champs, valeurs `null` incluses.")
    parts.append(table(["UTC", "Champs différents"], [(t.isoformat(), ", ".join(
        "`" + k + "`" for k in rows[0] if len({json.dumps(r.get(k), sort_keys=True) for _, r in vs}) > 1))
        for t, vs in duplicates.items()]))
    parts.append("""### Structure observée et hypothèses

30 groupes, deux par année 2012–2026, sont à 01:00 et 01:30 UTC lors du passage à l'heure d'été. Une occurrence indique `02:00` ou `02:30` en heure brute alors que l'instant se convertit en `03:00` ou `03:30`. Le fichier entier contient exactement 30 discordances entre calendrier brut et conversion locale, toutes dans ces groupes. À 01:30 UTC les puissances sont toujours différentes ; à 01:00 elles diffèrent en 2019, 2021, 2024 et 2026. Les 11 autres groupes ont même puissance mais d'autres champs différents.

Trois groupes supplémentaires se situent en décembre 2020, 2022 et 2023, hors changement d'heure ; chacun comporte un conflit électrique, avec date et heure locales brutes identiques entre variantes.

**Hypothèse non vérifiée** : transformation d'un calendrier local régulier ou traitement des heures inexistantes/ambiguës lors de l'intégration ou de l'export. La correspondance avec les transitions est calculée ; la cause technique chez le producteur et la bonne variante ne sont pas établies. Les anomalies de décembre peuvent relever d'un autre problème de date ou d'intégration : aucun déplacement n'est justifié par ces seuls constats.

## 4. Les 31 créneaux absents : liste exhaustive

Grille UTC de 30 minutes, bornes incluses. Un créneau absent n'est pas une ligne portant une puissance nulle.
""")
    parts.append(table(["UTC absent", "Europe/Paris", "Contexte calculé"], [
        (t.isoformat(), t.astimezone(local).isoformat(),
         "Retour heure hiver" if t.month == 10 else "Hors transition saisonnière") for t in absent]))
    parts.append("""28 créneaux, deux par année 2012–2025, correspondent au premier passage à 02:00/02:30 locales à l'automne, avec offset `+02:00`. Le second passage avec offset `+01:00` est présent. Une grille UTC réelle ne supprime aucune heure lors d'un changement de fuseau : ces trous ne sont pas inévitables.

Les trois autres trous sont à minuit local le 6 décembre 2020, 2022 et 2023. Les doublons de décembre sont au 5 décembre 2020, puis au 4 décembre 2022 et 2023 locaux : ils ne sont pas adjacents aux trous. Rien ne prouve qu'une valeur dupliquée devrait être déplacée pour les combler. Les 31 créneaux représentent 15,5 heures de durée de grille, pas une énergie manquante ni un nombre d'heures agrégées valides.

## 5. Les 1 440 statuts RTE manquants

Il s'agit exclusivement de valeurs JSON `null`, sans chaîne vide. Le bloc est continu et comporte 1 440 instants uniques à 30 minutes :

- UTC : `2026-08-31T22:00:00+00:00` à `2026-09-30T21:30:00+00:00`.
- Local : `2026-09-01T00:00:00+02:00` à `2026-09-30T23:30:00+02:00`.
- Mois UTC : 4 lignes en août et 1 436 en septembre 2026.
- Mois local : exactement septembre 2026, 48 lignes par jour sur 30 jours.
- Aucune puissance électrique manquante, aucun chevauchement avec un groupe dupliqué, tous les flags `non`.

L'absence de statut n'est pas une absence de mesure et ne démontre pas un statut provisoire. Une omission des métadonnées sur le dernier mois est une hypothèse ; ne pas compléter par propagation.

### Statuts par année locale

Comptes de lignes brutes, doublons inclus.
""")
    parts.append(table(["Année locale", "Définitif", "Consolidé", "null"], [
        (year, counts[year, "Définitif"], counts[year, "Consolidé"], counts[year, "null"])
        for year in range(2012, 2027)]))
    parts.append("""La description sauvegardée annonce 2012–2024 définitifs, mais les lignes 2020, 2021, 2023 et 2024 sont marquées `Consolidé`. Décrire ces statuts réellement observés, sans décider si le libellé ou la donnée est erroné. Le découpage scientifique n'est pas changé, mais l'hypothèse d'un test 2024 au statut définitif doit être réexaminée.

## 6. Distribution de `flag_ignore`

| Valeur | Lignes | Proportion |
|---|---|---|
| `non` | 258 576 | 100 % |
| `null` ou chaîne vide | 0 | 0 % |
| Autre | 0 | 0 % |

Croisement avec statut RTE : `non` + `Définitif` : 157 776 ; `non` + `Consolidé` : 99 360 ; `non` + `null` : 1 440. Les 66 lignes dupliquées ont aussi ce flag. Il n'est donc pas discriminant sur les anomalies de cet instantané. Sa description manque dans les métadonnées et la page officielle consultée. Ne pas assimiler `non` à une validation de qualité ni l'utiliser pour sélectionner une variante.

## 7. Documentation officielle consultée et limites

Consultations du 4 novembre 2026, sans acquisition supplémentaire d'observations :

1. [ODRÉ — Fiche et schéma](https://odre.opendatasoft.com/explore/dataset/consommation-quotidienne-brute/?flg=fr-fr), résultats indexés rapprochés de `metadata.json` : électricité demi-horaire en MW ; descriptions absentes de `date_heure`, `statut_rte`, `flag_ignore`.
2. [RTE — Spécifications éCO2mix, juin 2025](https://assets.rte-france.com/prod/public/2025-06/Eco2mix%20-%20Sp%C3%A9cifications%20des%20fichiers%20en%20puissance.pdf), §1.1 page 1 et section France page 6 : temps réel en puissance instantanée ; consolidé/définitif en puissance moyenne, au pas demi-horaire. Le document concerne éCO2mix ; son application exacte à l'export ODRÉ et à ses transformations reste à établir.
3. [RTE — Historiques éCO2mix](https://www.rte-france.com/donnees-publications/eco2mix-donnees-temps-reel/telecharger-indicateurs) : décrit les révisions mensuelles puis annuelles et renvoie aux spécifications ; ne résout pas les collisions du produit ODRÉ.

Le fuseau UTC est confirmé par les métadonnées locales et les timestamps avec offset. La convention début/fin d'intervalle demeure non confirmée. La nature moyenne est confirmée pour les fichiers éCO2mix consolidés/définitifs ; la transposition à ce jeu reste une inférence, particulièrement pour le mois sans statut. Aucun document consulté n'établit la cause des anomalies ni une règle de correction ou la signification de `flag_ignore`.

Questions techniques à clarifier auprès du producteur : traitement des transitions, anomalies de décembre, statut du dernier mois, divergence des statuts annuels et rattachement exact des puissances. Le script n'effectue aucun contact avec le producteur.

## 8. Règles documentées pour l'instantané de référence

1. Conserver le brut et son empreinte. Une future table dérivée gardera positions sources, UTC original, conversion locale, statuts bruts, flags et indicateurs d'anomalie.
2. Trier uniquement la table dérivée en UTC ; aucune localisation implicite ou reconstruction arbitraire depuis les heures textuelles.
3. Une déduplication stricte intégrale pourrait être proposée après validation pour des lignes identiques sur tous les champs ; aucune paire de ce type n'existe ici.
4. Pour les 11 groupes de même puissance, envisager après validation une valeur unique dans une projection strictement électrique, avec les deux références sources, sans fusion silencieuse des champs gaziers et sans qualifier les lignes complètes d'identiques.
5. Pour les 22 conflits électriques, aucune première/dernière valeur ni moyenne arbitraire. Proposer une quarantaine des cibles correspondantes dans une future table dérivée jusqu'à résolution par le producteur ou une source comparable autorisée. La cohérence du texte local seule ne prouve pas la validité de sa puissance.
6. Représenter les 31 absences dans une future grille sans imputation ; ne pas déplacer les doublons de décembre pour les combler.
7. Conserver les statuts manquants et leur indicateur de qualité ; envisager une sensibilité avec/sans septembre 2026, sans suppression automatique ni fabrication de statut. Signaler la divergence des statuts annuels.
8. Garder `flag_ignore` pour traçabilité, sans règle de nettoyage ou prédicteur fondé sur une signification supposée.
9. Après confirmation des conventions et validation, n'agréger une heure que si ses deux demi-heures sont distinctes, résolues et valides ; jamais une moyenne calculée sur une seule mesure. Aucune agrégation ici.
10. Identifier avant évaluation les origines, historiques et cibles touchés par trous/conflits ; un futur masque commun aux modèles et références devra quantifier les exclusions et leur saisonnalité, sans sélection selon les performances.

## 9. Contrôles et état final

Les assertions vérifient la concordance intégrale avec l'audit initial, les comptes d'anomalies, la continuité du bloc sans statut, les 30 discordances locales et le flag constant. Les valeurs annuelles sont contrôlées contre les libellés Unicode réels. L'empreinte brute est vérifiée avant et après calcul. Les contrôles sont descriptifs ; aucun résultat prédictif n'est produit.

Le JSON initial reste inchangé. Ce traitement produit uniquement le diagnostic de l'instantané de référence, sans nettoyage, imputation, déduplication, agrégation ni téléchargement d'observations. L'historique des tentatives et l'avancement des étapes sont documentés dans les rapports correspondants ; ils ne sont pas déduits d'une réexécution du script.
""")
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
    target = ROOT / "reports/diagnostic_anomalies_temporelles.md"
    target.write_text("\n\n".join(parts) + "\n", encoding="utf-8")
    print("Diagnostic écrit ; assertions réussies ; empreinte brute inchangée.")


if __name__ == "__main__":
    main()
