# Préparation contrôlée des données électriques — Mission 007, phase 1

> Note de suivi du 5 novembre 2026 : la condition de poursuite consignée en fin de phase 1 est historique. La phase 2 a ensuite donné lieu à [l'étude des conventions temporelles](etude_agregation_horaire.md), puis aux [deux scénarios horaires expérimentaux](preparation_horaire_experimentale.md). Cette note ne modifie ni la grille ni les résultats de la phase 1.

> Note documentaire — Mission 009 bis : les chemins locaux absolus de l’exécution historique ont été remplacés par leurs équivalents relatifs à la racine du dépôt. Les noms de fichiers, paramètres, résultats et empreintes sont inchangés.

## Provenance et paramètres

```json
{
  "created_at_utc": "2026-11-04T16:10:12.734623+00:00",
  "source": "data/raw/odre_f6gejuyq/observations.json",
  "source_sha256": "65f6a751d0e02d1a11c6d5e85dc620734b04ffc19f2c2ed3acc110e828125cf3",
  "manifest": "data/raw/odre_f6gejuyq/manifest.json",
  "manifest_sha256": "4f66201e22c85396905b250be88327e7c26bd7de8a268659df892da7718aa269",
  "reference_audit": "reports/audit_observations.json",
  "reference_audit_sha256": "ccbc9517d13d1b5ae199f370ea8d1f338285564ac58b53c7548042b8cebdaca0",
  "output": "data/processed/electricite_30min_phase1.jsonl",
  "output_sha256": "50a3e89a7f9bbd5325ad1e4f557e6a3081ad7d5a429d6f9143f255b8f1172762",
  "report": "reports/preparation_electricite_phase1.md",
  "preparation_code_sha256": "32c4e195418d9375d6750cb306d024812d8b555d50ad146af7ab15a9b9ddce19",
  "python": "3.14.6",
  "tzdata": "2026.6",
  "parameters": {
    "frequency_minutes": 30,
    "grid_timezone": "UTC",
    "local_timezone": "Europe/Paris",
    "bounds": "observed_inclusive",
    "timestamp_interval_convention": "unknown",
    "source_positions_base": 1,
    "power_unit": "MW (documented)",
    "conflict_policy": "null",
    "missing_policy": "null",
    "format": "JSONL UTF-8"
  },
  "start_utc": "2011-12-31T23:00:00+00:00",
  "end_utc": "2026-09-30T21:30:00+00:00"
}
```

## Méthode et schéma

La table JSONL UTF-8 contient un objet par étiquette UTC, dans l'ordre croissant. `timestamp_utc` est sa clé unique ; le format fichier ne porte pas d'index logiciel implicite. Le pas est de 30 minutes, bornes observées incluses. Aucune hypothèse de début/fin d'intervalle.

`electricity_mw` conserve la puissance observée pour un créneau unique ou des variantes de même puissance. Elle vaut JSON `null` pour un conflit (`ambiguous`) ou une absence (`absent`). Aucune moyenne, interpolation ni correction temporelle. Les colonnes gazières ne sont pas fusionnées.

`source_positions` référence les objets du tableau brut en base 1. `source_observations` conserve pour chaque variante son horodatage/calendrier brut, sa puissance, son statut et son flag. Les listes `statut_rte_sources` et `flag_ignore_sources` suivent ces positions, sans sélection. La source et son empreinte sont communes à toutes les lignes et consignées ci-dessus.

Les colonnes locales sont dérivées avec `Europe/Paris` : date, heure, année, mois, jour de semaine (lundi = 0), offset et `local_fold` (0/1 pour désambiguïser l'heure répétée). `source_calendar_mismatch_count` conserve les discordances avec les textes sources.

## Comptes vérifiés

```json
{
  "expected": 258574,
  "unique": 258510,
  "usable": 258521,
  "missing_source_status_slots": 1440,
  "source_rows": 258576,
  "duplicate_excess": 33,
  "calendar_mismatch_source_rows": 30,
  "duplicate_same_power": 11,
  "ambiguous": 22,
  "absent": 31
}
```

« Exploitable » signifie uniquement puissance présente et non contradictoire selon les règles autorisées. Cela ne garantit ni la validité physique, ni la disponibilité historique à l'instant de prévision. Un statut manquant ou une discordance de calendrier ne supprime pas la puissance. Les indicateurs permettent une sélection scientifique ultérieure, après validation.

## Répartition annuelle (année locale Europe/Paris)

| Année | Grille | Exploitables | Uniques | Doublons même MW | Ambigus | Absents | Statut source manquant |
|---|---|---|---|---|---|---|---|
| 2012 | 17568 | 17565 | 17564 | 1 | 1 | 2 | 0 |
| 2013 | 17520 | 17517 | 17516 | 1 | 1 | 2 | 0 |
| 2014 | 17520 | 17517 | 17516 | 1 | 1 | 2 | 0 |
| 2015 | 17520 | 17517 | 17516 | 1 | 1 | 2 | 0 |
| 2016 | 17568 | 17565 | 17564 | 1 | 1 | 2 | 0 |
| 2017 | 17520 | 17517 | 17516 | 1 | 1 | 2 | 0 |
| 2018 | 17520 | 17517 | 17516 | 1 | 1 | 2 | 0 |
| 2019 | 17520 | 17516 | 17516 | 0 | 2 | 2 | 0 |
| 2020 | 17568 | 17563 | 17562 | 1 | 2 | 3 | 0 |
| 2021 | 17520 | 17516 | 17516 | 0 | 2 | 2 | 0 |
| 2022 | 17520 | 17515 | 17514 | 1 | 2 | 3 | 0 |
| 2023 | 17520 | 17515 | 17514 | 1 | 2 | 3 | 0 |
| 2024 | 17568 | 17564 | 17564 | 0 | 2 | 2 | 0 |
| 2025 | 17520 | 17517 | 17516 | 1 | 1 | 2 | 0 |
| 2026 | 13102 | 13100 | 13100 | 0 | 2 | 0 | 1440 |

## Cohérence avec le diagnostic précédent

L'audit du brut est recalculé et comparé champ par champ à `reports/audit_observations.json` (chemin configurable). Les comptes de la table sont ensuite rapprochés du brut : sources conservées = lignes brutes ; doublons excédentaires = diagnostic ; absences = trous de grille ; créneaux non absents = instants uniques ; toutes les positions sources sont représentées exactement une fois. Le SHA-256 du brut est contrôlé avant et après, la table est relue intégralement.

## Limites et décisions différées

Les conflits et absences restent sans valeur. Les statuts JSON `null` restent nuls, sans propagation. Une absence de source produit des listes vides et non un statut inventé. `flag_ignore` est préservé sans interprétation ni critère de sélection. La divergence des statuts annuels et les conventions physiques non confirmées décrites dans `reports/diagnostic_anomalies_temporelles.md` restent ouvertes. Les extrêmes ou valeurs nulles/négatives éventuelles ne seraient pas corrigés par cette préparation.

Les comptes par année sont locaux ; ne pas les confondre avec les comptes par année UTC. Le rapport contient l'empreinte du code de préparation et les versions Python/base de fuseaux. La lecture JSON en mémoire reste une limite pour des exports plus volumineux.

Sorties créées exclusivement : une relance avec les mêmes chemins est refusée. En cas d'interruption d'écriture, un fichier partiel peut subsister sans rapport final validé ; ne pas le considérer comme un résultat complet. Aucun fichier existant n'est écrasé.

Aucune donnée brute modifiée, aucune série horaire, aucun modèle, commit ou push. La phase 2 nécessite une validation distincte.

## Exécution de la mission et tests

Commande de génération réellement exécutée depuis la racine :

```powershell
.\.venv\Scripts\python.exe -m src.preparer_electricite --input data/raw/odre_f6gejuyq/observations.json --manifest data/raw/odre_f6gejuyq/manifest.json --audit reports/audit_observations.json --output data/processed/electricite_30min_phase1.jsonl --report reports/preparation_electricite_phase1.md
```

Résultat : code de sortie 0. Le fichier dérivé mesure 210 447 656 octets. Sa relecture intégrale a été comparée aux règles de préparation et à la provenance source, ligne par ligne. Les 258 576 positions sources sont toutes conservées exactement une fois dans les listes de provenance des 258 574 créneaux. Les 22 créneaux ambigus et 31 absents portent une puissance JSON `null` ; les 11 groupes de même puissance conservent leur valeur et toutes leurs références.

Commande des tests réellement exécutée :

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Résultat exact : `Ran 19 tests in 0.466s`, puis `OK`, code de sortie 0. Cela comprend les 9 tests existants et 10 nouveaux tests synthétiques de `tests/test_preparer_electricite.py` :

- unicité, tri et positions sources originales ;
- doublons de même puissance, avec conservation des statuts et flags distincts ;
- conflits sans sélection ni moyenne ;
- créneau absent et provenance vide explicites ;
- saut d'heure au printemps sans trou UTC artificiel ;
- heure locale répétée à l'automne, avec offsets et `fold` distincts ;
- statut manquant conservé sans perte de puissance ;
- calendrier source discordant préservé ;
- rejet des entrées invalides sans correction implicite ;
- préparation de bout en bout sur données synthétiques, intégrité, refus d'écrasement et protection du dossier brut.

Ces tests n'entraînent aucun modèle et n'effectuent aucun accès réseau réel. Les validations sur l'instantané réel sont les contrôles d'intégrité, de cohérence et de relecture décrits plus haut.

La règle `/data/processed/*.jsonl` a été ajoutée à `.gitignore` et vérifiée par `git check-ignore -v` : la table générée volumineuse ne sera pas ajoutée par un `git add` ordinaire. Le script, les tests et le présent rapport permettent sa reproduction. Aucun fichier précédent n'a été remplacé.
