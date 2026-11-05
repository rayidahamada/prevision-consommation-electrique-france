# Diagnostic des anomalies temporelles ODRÉ — Mission 006 bis

Analyse locale du 4 novembre 2026. Aucun nettoyage appliqué.

## 1. Traçabilité et méthode

Données : `data/raw/odre_f6gejuyq/observations.json` ; manifeste et métadonnées dans le même dossier. Audit initial : `reports/audit_observations.json`, conservé sans modification. Le manifeste indique `complete`.

Les règles `AGENTS.md` et l'état Git ont été examinés avant intervention. Plusieurs fichiers de missions précédentes étaient déjà non suivis. Le script `src/diagnostic_temporel.py` rend les calculs reproductibles avec `.venv`, la bibliothèque standard, les fonctions existantes `audit` et `parse_time`, et `ZoneInfo('Europe/Paris')`. Il ne modifie pas les données ; il écrit uniquement ce rapport. Commande : `python -m src.diagnostic_temporel` depuis la racine. Les assertions sont propres à cet instantané et doivent échouer si son contenu change.

Empreinte SHA-256 recalculée, égale au manifeste et au rapport initial :

`65f6a751d0e02d1a11c6d5e85dc620734b04ffc19f2c2ed3acc110e828125cf3`

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


| UTC | Europe/Paris | Positions A / B | Heures brutes A / B | MW A / B | Statut A = B | Flags A / B | Conflit MW |
|---|---|---|---|---|---|---|---|
| 2012-03-25T01:00:00+00:00 | 2012-03-25T03:00:00+02:00 | 254539 / 254540 | 03:00 / 02:00 | 46435 / 46435 | Définitif | non / non | non |
| 2012-03-25T01:30:00+00:00 | 2012-03-25T03:30:00+02:00 | 254537 / 254538 | 02:30 / 03:30 | 47196 / 46383 | Définitif | non / non | oui |
| 2013-03-31T01:00:00+00:00 | 2013-03-31T03:00:00+02:00 | 236731 / 236732 | 02:00 / 03:00 | 62421 / 62421 | Définitif | non / non | non |
| 2013-03-31T01:30:00+00:00 | 2013-03-31T03:30:00+02:00 | 236729 / 236730 | 03:30 / 02:30 | 62694 / 62765 | Définitif | non / non | oui |
| 2014-03-30T01:00:00+00:00 | 2014-03-30T03:00:00+02:00 | 219259 / 219260 | 03:00 / 02:00 | 48138 / 48138 | Définitif | non / non | non |
| 2014-03-30T01:30:00+00:00 | 2014-03-30T03:30:00+02:00 | 219257 / 219258 | 03:30 / 02:30 | 47855 / 48737 | Définitif | non / non | oui |
| 2015-03-29T01:00:00+00:00 | 2015-03-29T03:00:00+02:00 | 201787 / 201788 | 03:00 / 02:00 | 52087 / 52087 | Définitif | non / non | non |
| 2015-03-29T01:30:00+00:00 | 2015-03-29T03:30:00+02:00 | 201785 / 201786 | 02:30 / 03:30 | 52852 / 52100 | Définitif | non / non | oui |
| 2016-03-27T01:00:00+00:00 | 2016-03-27T03:00:00+02:00 | 184315 / 184316 | 03:00 / 02:00 | 51429 / 51429 | Définitif | non / non | non |
| 2016-03-27T01:30:00+00:00 | 2016-03-27T03:30:00+02:00 | 184313 / 184314 | 02:30 / 03:30 | 52243 / 51335 | Définitif | non / non | oui |
| 2017-03-26T01:00:00+00:00 | 2017-03-26T03:00:00+02:00 | 166843 / 166844 | 03:00 / 02:00 | 50720 / 50720 | Définitif | non / non | non |
| 2017-03-26T01:30:00+00:00 | 2017-03-26T03:30:00+02:00 | 166841 / 166842 | 03:30 / 02:30 | 50891 / 51624 | Définitif | non / non | oui |
| 2018-03-25T01:00:00+00:00 | 2018-03-25T03:00:00+02:00 | 149371 / 149372 | 02:00 / 03:00 | 56943 / 56943 | Définitif | non / non | non |
| 2018-03-25T01:30:00+00:00 | 2018-03-25T03:30:00+02:00 | 149369 / 149370 | 03:30 / 02:30 | 56971 / 57529 | Définitif | non / non | oui |
| 2019-03-31T01:00:00+00:00 | 2019-03-31T03:00:00+02:00 | 131563 / 131564 | 02:00 / 03:00 | 47262 / 47805 | Définitif | non / non | oui |
| 2019-03-31T01:30:00+00:00 | 2019-03-31T03:30:00+02:00 | 131561 / 131562 | 03:30 / 02:30 | 47329 / 47262 | Définitif | non / non | oui |
| 2020-03-29T01:00:00+00:00 | 2020-03-29T03:00:00+02:00 | 114091 / 114092 | 03:00 / 02:00 | 46904 / 46904 | Consolidé | non / non | non |
| 2020-03-29T01:30:00+00:00 | 2020-03-29T03:30:00+02:00 | 114089 / 114090 | 02:30 / 03:30 | 47184 / 47024 | Consolidé | non / non | oui |
| 2020-12-04T23:00:00+00:00 | 2020-12-05T00:00:00+01:00 | 102047 / 102048 | 00:00 / 00:00 | 64891 / 66352 | Consolidé | non / non | oui |
| 2021-03-28T01:00:00+00:00 | 2021-03-28T03:00:00+02:00 | 96619 / 96620 | 03:00 / 02:00 | 52042 / 51662 | Consolidé | non / non | oui |
| 2021-03-28T01:30:00+00:00 | 2021-03-28T03:30:00+02:00 | 96617 / 96618 | 02:30 / 03:30 | 51662 / 51893 | Consolidé | non / non | oui |
| 2022-03-27T01:00:00+00:00 | 2022-03-27T03:00:00+02:00 | 79147 / 79148 | 03:00 / 02:00 | 46101 / 46101 | Définitif | non / non | non |
| 2022-03-27T01:30:00+00:00 | 2022-03-27T03:30:00+02:00 | 79145 / 79146 | 02:30 / 03:30 | 46141 / 43922 | Définitif | non / non | oui |
| 2022-12-03T23:00:00+00:00 | 2022-12-04T00:00:00+01:00 | 67055 / 67056 | 00:00 / 00:00 | 57335 / 59811 | Définitif | non / non | oui |
| 2023-03-26T01:00:00+00:00 | 2023-03-26T03:00:00+02:00 | 61675 / 61676 | 03:00 / 02:00 | 45221 / 45221 | Consolidé | non / non | non |
| 2023-03-26T01:30:00+00:00 | 2023-03-26T03:30:00+02:00 | 61673 / 61674 | 03:30 / 02:30 | 43011 / 44812 | Consolidé | non / non | oui |
| 2023-12-03T23:00:00+00:00 | 2023-12-04T00:00:00+01:00 | 49535 / 49536 | 00:00 / 00:00 | 61954 / 64171 | Consolidé | non / non | oui |
| 2024-03-31T01:00:00+00:00 | 2024-03-31T03:00:00+02:00 | 43867 / 43868 | 02:00 / 03:00 | 46682 / 46681 | Consolidé | non / non | oui |
| 2024-03-31T01:30:00+00:00 | 2024-03-31T03:30:00+02:00 | 43865 / 43866 | 02:30 / 03:30 | 46619 / 44538 | Consolidé | non / non | oui |
| 2025-03-30T01:00:00+00:00 | 2025-03-30T03:00:00+02:00 | 26395 / 26396 | 02:00 / 03:00 | 48398 / 48398 | Consolidé | non / non | non |
| 2025-03-30T01:30:00+00:00 | 2025-03-30T03:30:00+02:00 | 26393 / 26394 | 03:30 / 02:30 | 46395 / 47832 | Consolidé | non / non | oui |
| 2026-03-29T01:00:00+00:00 | 2026-03-29T03:00:00+02:00 | 8923 / 8924 | 02:00 / 03:00 | 54157 / 53876 | Consolidé | non / non | oui |
| 2026-03-29T01:30:00+00:00 | 2026-03-29T03:30:00+02:00 | 8921 / 8922 | 02:30 / 03:30 | 53876 / 51908 | Consolidé | non / non | oui |

### Champs différents dans chaque groupe

Comparaison des 12 champs, valeurs `null` incluses.

| UTC | Champs différents |
|---|---|
| 2012-03-25T01:00:00+00:00 | `heure`, `consommation_brute_gaz_grtgaz`, `consommation_brute_gaz_terega`, `consommation_brute_gaz_totale`, `consommation_brute_totale` |
| 2012-03-25T01:30:00+00:00 | `heure`, `consommation_brute_electricite_rte` |
| 2013-03-31T01:00:00+00:00 | `heure`, `consommation_brute_gaz_grtgaz`, `consommation_brute_gaz_terega`, `consommation_brute_gaz_totale`, `consommation_brute_totale` |
| 2013-03-31T01:30:00+00:00 | `heure`, `consommation_brute_electricite_rte` |
| 2014-03-30T01:00:00+00:00 | `heure`, `consommation_brute_gaz_grtgaz`, `consommation_brute_gaz_terega`, `consommation_brute_gaz_totale`, `consommation_brute_totale` |
| 2014-03-30T01:30:00+00:00 | `heure`, `consommation_brute_electricite_rte` |
| 2015-03-29T01:00:00+00:00 | `heure`, `consommation_brute_gaz_grtgaz`, `consommation_brute_gaz_terega`, `consommation_brute_gaz_totale`, `consommation_brute_totale` |
| 2015-03-29T01:30:00+00:00 | `heure`, `consommation_brute_electricite_rte` |
| 2016-03-27T01:00:00+00:00 | `heure`, `consommation_brute_gaz_grtgaz`, `consommation_brute_gaz_terega`, `consommation_brute_gaz_totale`, `consommation_brute_totale` |
| 2016-03-27T01:30:00+00:00 | `heure`, `consommation_brute_electricite_rte` |
| 2017-03-26T01:00:00+00:00 | `heure`, `consommation_brute_gaz_grtgaz`, `consommation_brute_gaz_terega`, `consommation_brute_gaz_totale`, `consommation_brute_totale` |
| 2017-03-26T01:30:00+00:00 | `heure`, `consommation_brute_electricite_rte` |
| 2018-03-25T01:00:00+00:00 | `heure`, `consommation_brute_gaz_grtgaz`, `consommation_brute_gaz_terega`, `consommation_brute_gaz_totale`, `consommation_brute_totale` |
| 2018-03-25T01:30:00+00:00 | `heure`, `consommation_brute_electricite_rte` |
| 2019-03-31T01:00:00+00:00 | `heure`, `consommation_brute_gaz_grtgaz`, `consommation_brute_gaz_terega`, `consommation_brute_gaz_totale`, `consommation_brute_electricite_rte`, `consommation_brute_totale` |
| 2019-03-31T01:30:00+00:00 | `heure`, `consommation_brute_electricite_rte` |
| 2020-03-29T01:00:00+00:00 | `heure`, `consommation_brute_gaz_grtgaz`, `consommation_brute_gaz_terega`, `consommation_brute_gaz_totale`, `consommation_brute_totale` |
| 2020-03-29T01:30:00+00:00 | `heure`, `consommation_brute_gaz_grtgaz`, `consommation_brute_electricite_rte` |
| 2020-12-04T23:00:00+00:00 | `consommation_brute_gaz_grtgaz`, `consommation_brute_gaz_terega`, `consommation_brute_gaz_totale`, `consommation_brute_electricite_rte`, `consommation_brute_totale` |
| 2021-03-28T01:00:00+00:00 | `heure`, `consommation_brute_gaz_grtgaz`, `consommation_brute_gaz_terega`, `consommation_brute_gaz_totale`, `consommation_brute_electricite_rte`, `consommation_brute_totale` |
| 2021-03-28T01:30:00+00:00 | `heure`, `consommation_brute_electricite_rte` |
| 2022-03-27T01:00:00+00:00 | `heure`, `consommation_brute_gaz_grtgaz`, `consommation_brute_gaz_terega`, `consommation_brute_gaz_totale`, `consommation_brute_totale` |
| 2022-03-27T01:30:00+00:00 | `heure`, `consommation_brute_electricite_rte` |
| 2022-12-03T23:00:00+00:00 | `consommation_brute_gaz_grtgaz`, `consommation_brute_gaz_terega`, `consommation_brute_gaz_totale`, `consommation_brute_electricite_rte`, `consommation_brute_totale` |
| 2023-03-26T01:00:00+00:00 | `heure`, `consommation_brute_gaz_grtgaz`, `consommation_brute_gaz_terega`, `consommation_brute_gaz_totale`, `consommation_brute_totale` |
| 2023-03-26T01:30:00+00:00 | `heure`, `consommation_brute_electricite_rte` |
| 2023-12-03T23:00:00+00:00 | `consommation_brute_gaz_grtgaz`, `statut_grtgaz`, `consommation_brute_gaz_terega`, `consommation_brute_gaz_totale`, `consommation_brute_electricite_rte`, `consommation_brute_totale` |
| 2024-03-31T01:00:00+00:00 | `heure`, `consommation_brute_gaz_grtgaz`, `consommation_brute_gaz_terega`, `consommation_brute_gaz_totale`, `consommation_brute_electricite_rte`, `consommation_brute_totale` |
| 2024-03-31T01:30:00+00:00 | `heure`, `consommation_brute_electricite_rte` |
| 2025-03-30T01:00:00+00:00 | `heure`, `consommation_brute_gaz_grtgaz`, `consommation_brute_gaz_terega`, `consommation_brute_gaz_totale`, `consommation_brute_totale` |
| 2025-03-30T01:30:00+00:00 | `heure`, `consommation_brute_electricite_rte` |
| 2026-03-29T01:00:00+00:00 | `heure`, `consommation_brute_gaz_grtgaz`, `consommation_brute_gaz_terega`, `consommation_brute_gaz_totale`, `consommation_brute_electricite_rte`, `consommation_brute_totale` |
| 2026-03-29T01:30:00+00:00 | `heure`, `consommation_brute_electricite_rte` |

### Structure observée et hypothèses

30 groupes, deux par année 2012–2026, sont à 01:00 et 01:30 UTC lors du passage à l'heure d'été. Une occurrence indique `02:00` ou `02:30` en heure brute alors que l'instant se convertit en `03:00` ou `03:30`. Le fichier entier contient exactement 30 discordances entre calendrier brut et conversion locale, toutes dans ces groupes. À 01:30 UTC les puissances sont toujours différentes ; à 01:00 elles diffèrent en 2019, 2021, 2024 et 2026. Les 11 autres groupes ont même puissance mais d'autres champs différents.

Trois groupes supplémentaires se situent en décembre 2020, 2022 et 2023, hors changement d'heure ; chacun comporte un conflit électrique, avec date et heure locales brutes identiques entre variantes.

**Hypothèse non vérifiée** : transformation d'un calendrier local régulier ou traitement des heures inexistantes/ambiguës lors de l'intégration ou de l'export. La correspondance avec les transitions est calculée ; la cause technique chez le producteur et la bonne variante ne sont pas établies. Les anomalies de décembre peuvent relever d'un autre problème de date ou d'intégration : aucun déplacement n'est justifié par ces seuls constats.

## 4. Les 31 créneaux absents : liste exhaustive

Grille UTC de 30 minutes, bornes incluses. Un créneau absent n'est pas une ligne portant une puissance nulle.


| UTC absent | Europe/Paris | Contexte calculé |
|---|---|---|
| 2012-10-28T00:00:00+00:00 | 2012-10-28T02:00:00+02:00 | Retour heure hiver |
| 2012-10-28T00:30:00+00:00 | 2012-10-28T02:30:00+02:00 | Retour heure hiver |
| 2013-10-27T00:00:00+00:00 | 2013-10-27T02:00:00+02:00 | Retour heure hiver |
| 2013-10-27T00:30:00+00:00 | 2013-10-27T02:30:00+02:00 | Retour heure hiver |
| 2014-10-26T00:00:00+00:00 | 2014-10-26T02:00:00+02:00 | Retour heure hiver |
| 2014-10-26T00:30:00+00:00 | 2014-10-26T02:30:00+02:00 | Retour heure hiver |
| 2015-10-25T00:00:00+00:00 | 2015-10-25T02:00:00+02:00 | Retour heure hiver |
| 2015-10-25T00:30:00+00:00 | 2015-10-25T02:30:00+02:00 | Retour heure hiver |
| 2016-10-30T00:00:00+00:00 | 2016-10-30T02:00:00+02:00 | Retour heure hiver |
| 2016-10-30T00:30:00+00:00 | 2016-10-30T02:30:00+02:00 | Retour heure hiver |
| 2017-10-29T00:00:00+00:00 | 2017-10-29T02:00:00+02:00 | Retour heure hiver |
| 2017-10-29T00:30:00+00:00 | 2017-10-29T02:30:00+02:00 | Retour heure hiver |
| 2018-10-28T00:00:00+00:00 | 2018-10-28T02:00:00+02:00 | Retour heure hiver |
| 2018-10-28T00:30:00+00:00 | 2018-10-28T02:30:00+02:00 | Retour heure hiver |
| 2019-10-27T00:00:00+00:00 | 2019-10-27T02:00:00+02:00 | Retour heure hiver |
| 2019-10-27T00:30:00+00:00 | 2019-10-27T02:30:00+02:00 | Retour heure hiver |
| 2020-10-25T00:00:00+00:00 | 2020-10-25T02:00:00+02:00 | Retour heure hiver |
| 2020-10-25T00:30:00+00:00 | 2020-10-25T02:30:00+02:00 | Retour heure hiver |
| 2020-12-05T23:00:00+00:00 | 2020-12-06T00:00:00+01:00 | Hors transition saisonnière |
| 2021-10-31T00:00:00+00:00 | 2021-10-31T02:00:00+02:00 | Retour heure hiver |
| 2021-10-31T00:30:00+00:00 | 2021-10-31T02:30:00+02:00 | Retour heure hiver |
| 2022-10-30T00:00:00+00:00 | 2022-10-30T02:00:00+02:00 | Retour heure hiver |
| 2022-10-30T00:30:00+00:00 | 2022-10-30T02:30:00+02:00 | Retour heure hiver |
| 2022-12-05T23:00:00+00:00 | 2022-12-06T00:00:00+01:00 | Hors transition saisonnière |
| 2023-10-29T00:00:00+00:00 | 2023-10-29T02:00:00+02:00 | Retour heure hiver |
| 2023-10-29T00:30:00+00:00 | 2023-10-29T02:30:00+02:00 | Retour heure hiver |
| 2023-12-05T23:00:00+00:00 | 2023-12-06T00:00:00+01:00 | Hors transition saisonnière |
| 2024-10-27T00:00:00+00:00 | 2024-10-27T02:00:00+02:00 | Retour heure hiver |
| 2024-10-27T00:30:00+00:00 | 2024-10-27T02:30:00+02:00 | Retour heure hiver |
| 2025-10-26T00:00:00+00:00 | 2025-10-26T02:00:00+02:00 | Retour heure hiver |
| 2025-10-26T00:30:00+00:00 | 2025-10-26T02:30:00+02:00 | Retour heure hiver |

28 créneaux, deux par année 2012–2025, correspondent au premier passage à 02:00/02:30 locales à l'automne, avec offset `+02:00`. Le second passage avec offset `+01:00` est présent. Une grille UTC réelle ne supprime aucune heure lors d'un changement de fuseau : ces trous ne sont pas inévitables.

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


| Année locale | Définitif | Consolidé | null |
|---|---|---|---|
| 2012 | 17568 | 0 | 0 |
| 2013 | 17520 | 0 | 0 |
| 2014 | 17520 | 0 | 0 |
| 2015 | 17520 | 0 | 0 |
| 2016 | 17568 | 0 | 0 |
| 2017 | 17520 | 0 | 0 |
| 2018 | 17520 | 0 | 0 |
| 2019 | 17520 | 0 | 0 |
| 2020 | 0 | 17568 | 0 |
| 2021 | 0 | 17520 | 0 |
| 2022 | 17520 | 0 | 0 |
| 2023 | 0 | 17520 | 0 |
| 2024 | 0 | 17568 | 0 |
| 2025 | 0 | 17520 | 0 |
| 2026 | 0 | 11664 | 1440 |

La description sauvegardée annonce 2012–2024 définitifs, mais les lignes 2020, 2021, 2023 et 2024 sont marquées `Consolidé`. Décrire ces statuts réellement observés, sans décider si le libellé ou la donnée est erroné. Le découpage scientifique n'est pas changé, mais l'hypothèse d'un test 2024 au statut définitif doit être réexaminée.

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

Questions à adresser au producteur après autorisation de contact : traitement des transitions, anomalies de décembre, statut du dernier mois, divergence des statuts annuels et rattachement exact des puissances. Aucun message envoyé.

## 8. Règles de préparation proposées, non appliquées

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

Le JSON initial reste inchangé. Le rapport narratif est complété par un renvoi à ce diagnostic, en conservant l'historique des tentatives. Aucun nettoyage, imputation, déduplication, agrégation, téléchargement d'observations, modèle, commit ou push. Mission 007 non commencée.
