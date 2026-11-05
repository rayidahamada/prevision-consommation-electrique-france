# Préparation horaire expérimentale — Mission 008

> Note documentaire — Mission 009 bis : les chemins locaux absolus de l’exécution historique ont été remplacés par leurs équivalents relatifs à la racine du dépôt. Les noms de fichiers, paramètres, résultats et empreintes sont inchangés.

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
{
  "input": "data/processed/electricite_30min_phase1.jsonl",
  "input_sha256": "50a3e89a7f9bbd5325ad1e4f557e6a3081ad7d5a429d6f9143f255b8f1172762",
  "grid_counts": {
    "rows": 258574,
    "unique": 258510,
    "duplicate_same_power": 11,
    "ambiguous": 22,
    "absent": 31
  },
  "grid_first_label": "2011-12-31T23:00:00+00:00",
  "grid_last_label": "2026-09-30T21:30:00+00:00",
  "hour_start_first": "2011-12-31T23:00:00+00:00",
  "hour_end_last": "2026-09-30T21:00:00+00:00",
  "script_sha256": "53290fde3f24e2288f5800f317ca5c43d7adfc58a765da471c02f5e4305897a4",
  "created_at_utc": "2026-11-05T13:27:02.226188+00:00",
  "outputs": [
    {
      "path": "data/processed/electricite_horaire_hypothese_debut.csv",
      "sha256": "9208e6f00e0b1e9a5fc0ed69bcd69af023d54195defb3299656730c2100f3fb2",
      "hours": 129286,
      "power_computable": 129251,
      "not_computable": 35,
      "target_eligible_strict": 128532,
      "not_strict": 754
    },
    {
      "path": "data/processed/electricite_horaire_hypothese_fin.csv",
      "sha256": "8c26a057d265e9ca627d4157e166aaf26b1a99f36b987521d1342218edf920b5",
      "hours": 129286,
      "power_computable": 129233,
      "not_computable": 53,
      "target_eligible_strict": 128499,
      "not_strict": 787
    }
  ]
}
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

## Commande réellement exécutée et environnement

Depuis la racine du projet :

```powershell
.\.venv\Scripts\python.exe -m src.preparer_horaire_experimental --input data/processed/electricite_30min_phase1.jsonl --expected-sha256 50a3e89a7f9bbd5325ad1e4f557e6a3081ad7d5a429d6f9143f255b8f1172762 --output-start data/processed/electricite_horaire_hypothese_debut.csv --output-end data/processed/electricite_horaire_hypothese_fin.csv --report reports/preparation_horaire_experimentale.md
```

Exécution terminée avec code 0. Une reproduction doit employer de nouveaux chemins de sortie si ces fichiers existent déjà. Bibliothèque standard uniquement, aucune dépendance ajoutée. Python utilisé : 3.14.6. Le calendrier est calculé avec `zoneinfo` et la base de fuseaux de l'environnement ; l'environnement de phase 1 documente `tzdata` 2026.6.

Bornes communes exactes : première heure `[2011-12-31T23:00:00+00:00, 2012-01-01T00:00:00+00:00)` ; dernière heure `[2026-09-30T20:00:00+00:00, 2026-09-30T21:00:00+00:00)`. La première heure locale commence le 1er janvier 2012 à 00:00+01:00 ; la dernière commence le 30 septembre 2026 à 22:00+02:00. Le fichier ne prétend pas couvrir l'intégralité de ce dernier jour local.

| Contrôle technique | A — début | B — fin |
|---|---:|---:|
| Lignes hors en-tête | 129 286 | 129 286 |
| Heures calculables sous hypothèse | 129 251 | 129 233 |
| Heures non calculables, puissance `null` | 35 | 53 |
| Heures admissibles strictes sous hypothèse | 128 532 | 128 499 |
| Heures non strictes | 754 | 787 |

Les heures non strictes comprennent les heures non calculables : ne pas additionner ces catégories. La différence de couverture ne permet pas de décider quelle convention est physiquement correcte.

Les deux CSV mesurent respectivement 68 510 890 et 68 252 637 octets. Leurs empreintes sont données dans le bloc de traçabilité ci-dessus. Les clés, durées, comptes et contenus sérialisés des deux fichiers ont été relus intégralement et rapprochés des composantes originales. Toutes les raisons de qualité et références sources ont été contrôlées lors de cette relecture. Il n'y a pas eu de modification de la grille pour améliorer la continuité.

## Tests exécutés

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Résultat exact : `Ran 30 tests in 0.605s`, puis `OK`, code 0. Les 19 tests précédents et les 11 nouveaux tests synthétiques de `tests/test_preparer_horaire_experimental.py` réussissent :

- formule de moyenne pour les étiquettes de début ;
- formule de fin, différence d'alignement et rejet des mauvaises composantes ;
- valeur horaire manquante si une demi-heure est absente ;
- valeur horaire manquante en cas d'ambiguïté, sans moyenne des variantes ;
- doublon de même puissance, provenance complète, statuts connus et flags sans filtrage ;
- statuts manquants, inconnus ou mixtes : puissance calculable mais cible stricte non admissible ;
- discordance calendaire excluant uniquement du strict ;
- passages été/hiver avec offsets locaux et heures répétées distinctes ;
- bornes communes sans invention de mesures de bord ;
- exécution synthétique de bout en bout, sérialisation CSV/JSON, empreinte d'entrée inchangée et refus d'écrasement ;
- refus d'une grille irrégulière avant création des sorties.

Les tests utilisent uniquement des observations synthétiques. Aucun téléchargement supplémentaire ou calcul de performance prédictive n'a été effectué.

## État Git et fichiers préservés

`AGENTS.md` a été lu et l'état Git vérifié avant intervention. Les modifications antérieures sont conservées. Seuls le nouveau script, ses tests, le présent rapport, les deux CSV et une règle `.gitignore` relèvent de cette mission.

La règle `/data/processed/electricite_horaire_hypothese_*.csv` a été ajoutée et contrôlée avec `git check-ignore -v` pour chacun des deux fichiers. Aucun CSV n'est ajouté à l'index Git. Aucun fichier de données précédent n'est modifié, aucun commit ou push n'est réalisé. Validation requise avant toute nouvelle étape.
