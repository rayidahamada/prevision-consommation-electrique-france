# Analyse exploratoire électrique — synthèse de la Mission 010

Analyse exécutée le 5 novembre 2026, hors ligne, sur l'instantané ODRÉ acquis le 4 novembre 2026. Les résultats détaillés, les effectifs par groupe et les exclusions figurent dans le [notebook exécuté](../notebooks/010_analyse_exploratoire.ipynb).

## Périmètre et reproductibilité

Le notebook lit les fichiers préparés existants et vérifie les quatre empreintes SHA-256 du brut, de la grille demi-horaire et des deux CSV horaires avant et après analyse. Aucune donnée n'est imputée, corrigée ou réagrégée. Les cellules n'écrivent aucun fichier. Les cinq figures de cette exécution sont également conservées dans `reports/figures/010_*.png`.

Depuis la racine du dépôt, sélectionner le noyau `.venv` et exécuter toutes les cellules de `notebooks/010_analyse_exploratoire.ipynb`. Les données locales, exclues de Git, sont nécessaires. Aucune donnée météorologique ou autre source externe n'est utilisée. Les liens ODRÉ du notebook constituent des références bibliographiques et ne déclenchent aucune requête réseau.

Les hypothèses restent distinctes : A utilise les étiquettes h et h+30 min ; B utilise h+30 min et h+1 h. Leur validité physique n'est pas confirmée. Les puissances sont décrites en MW, sans conversion abusive en énergie.

## Qualité et populations utilisées

Les deux CSV comprennent chacun 129 286 heures, de `2011-12-31T23:00:00+00:00` à `2026-09-30T20:00:00+00:00` pour les débuts d'heure. Le dernier intervalle se termine à `2026-09-30T21:00:00+00:00`. La grille UTC est régulière et les clés sont identiques entre scénarios.

| Population | Scénario A | Scénario B |
| --- | ---: | ---: |
| Puissance calculable | 129 251 | 129 233 |
| Puissance indisponible | 35 | 53 |
| Admissible selon les critères stricts hérités | 128 532 | 128 499 |

Les critères stricts existants écartent notamment les statuts RTE absents ou non homogènes et les discordances calendaires. Les flags sont conservés sans interprétation supplémentaire. La comparaison principale utilise les **128 493 heures strictes communes** : 793 heures de la grille sont exclues. Une sensibilité utilise les **129 227 heures calculables communes**, soit 59 exclusions. Les masques propres aux scénarios sont également présentés séparément.

La grille demi-horaire retrouve 22 créneaux ambigus, 31 absents et 11 doublons résolus par égalité des puissances. L'audit antérieur décrit 33 groupes de doublons et 1 440 statuts RTE manquants ; le notebook distingue ces résultats historiques des contrôles effectués sur la grille préparée.

Les 29 journées locales de changement d'heure comprises dans la période comportent 23 ou 25 étiquettes horaires UTC distinctes. Les anomalies de consommation présentes ces jours restent visibles. Le 30 septembre 2026 est une journée de bord incomplète, avec 23 étiquettes. Une journée de 23 heures lors du passage à l'heure d'été ne constitue pas en soi une lacune de la grille UTC.

## Résultats descriptifs

Sur les 128 493 heures strictes communes, la puissance moyenne est de **52 885,74 MW pour A** et **52 886,05 MW pour B**. Les extrêmes sont respectivement **28 987,0–101 533,5 MW** et **28 758,0–100 516,0 MW**. Ils décrivent la population retenue et ne sont pas automatiquement qualifiés d'erreurs. Les dates et références sources des cinq minima et maxima sont conservées dans le notebook.

Les profils calendaires portent sur **122 665 heures strictes communes des années 2012–2025**. Les observations de 2026 sont exclues de ces seuls profils ; les tableaux chronologiques les présentent avec leur couverture partielle. Dans les deux scénarios, le profil saisonnier moyen est le plus élevé en hiver et le plus bas en été ; le dimanche présente le profil journalier moyen le plus faible. Le maximum du profil horaire agrégé se situe à 12 h locale dans les deux cas. Ces moyennes regroupent des années et situations différentes et ne démontrent aucune causalité.

Le rapprochement « lundi–vendredi / samedi–dimanche » est une approximation calendaire : aucun calendrier de jours fériés n'est disponible ici. Il ne constitue donc pas une identification exacte des jours ouvrés.

Sur la population stricte commune, la médiane de la différence absolue A/B à la même clé horaire est de **764 MW**, et son maximum de **4 684,5 MW**. La différence moyenne B−A est de **0,32 MW**. Elle atteint **1,31 MW** lorsque chaque scénario utilise son propre masque ; le reliquat arithmétique de sélection est **0,99 MW**. Cette décomposition distingue les populations et ne mesure pas un effet causal. Les différences de profils horaires restent visibles malgré des moyennes globales proches.

## Vérifications techniques

Commandes de contrôle depuis la racine :

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe scripts/check_documentation.py --include-untracked
git diff --check
git status --short
```

La suite existante comprend 49 tests. Le notebook ne crée aucune fonction scientifique réutilisable supplémentaire ; aucun test unitaire redondant n'est ajouté. Son exécution complète contrôle également les empreintes, les clés UTC, les indicateurs de disponibilité, les populations comparées et les durées des journées locales.

Le contrôle documentaire standard examine les fichiers Markdown et Python, pas les notebooks. Une vérification complémentaire applique ses règles aux cellules Markdown et aux textes Python du notebook. Les fichiers nouveaux font également l'objet d'un contrôle des espaces en fin de ligne, puisque `git diff --check` ne les examine pas avant suivi.

Résultats effectivement obtenus le 5 novembre 2026 : **49 tests réussis en 1,801 s** ; contrôle documentaire sur **20 fichiers**, sans erreur ni avertissement ; `git diff --check` sans anomalie. Les **14 cellules de code** ont été exécutées sans erreur et les règles documentaires appliquées aux cellules n'ont signalé aucune formulation. Les cinq liens locaux du notebook existent. Les quatre empreintes de données et les empreintes des 30 fichiers déjà suivis sont inchangées par rapport au début de cette analyse. Les nouveaux textes ne contiennent ni espaces en fin de ligne ni chemins personnels absolus.

Les sept fichiers créés sont le notebook, cette synthèse et cinq figures : `010_evolution_chronologique.png`, `010_distribution_puissances.png`, `010_profils_horaires_hebdomadaires.png`, `010_profils_mensuels_saisonniers.png` et `010_comparaison_profils_AB.png`. Ils restent non suivis ; aucun fichier n'est ajouté à l'index.

## Limites et étapes suivantes

- Confirmer indépendamment la nature physique et la convention temporelle des mesures ; aucun scénario n'est privilégié.
- Définir l'instant d'émission et distinguer 24 heures écoulées du lendemain civil local de 23, 24 ou 25 heures.
- Établir la disponibilité historique des observations, des statuts et des révisions avant de construire des historiques prédictifs.
- Documenter les exclusions et leurs effets, notamment les statuts absents en septembre 2026.
- Fixer ultérieurement une validation chronologique et des références naïves ; aucune performance prédictive n'est calculée ici.
- Tenir compte du fait que cette exploration porte sur toute la période : une future période test déjà explorée ne devra pas être présentée comme entièrement inconnue lors des choix méthodologiques.

Aucune donnée source ou préparation antérieure n'est modifiée. Aucun téléchargement, entraînement, ajout à l'index, commit ou push n'est réalisé.
