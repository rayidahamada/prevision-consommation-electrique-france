# Faisabilité exploratoire d'une application de prévisions électriques actualisées

Étude du 6 novembre 2026, indépendante de la Mission 012 scientifique. Clôture de la consultation documentaire : **2026-11-06T13:14:36Z**, horloge UTC de l'environnement. Les heures individuelles de réception HTTP de l'outil web ne sont pas exposées ; cet instant est un repère de consultation, pas une heure de publication des sources. La tentative Python possède ses propres horodatages exacts ci-dessous.

## 1. Objet et état initial

La perspective étudiée est une application facultative affichant 24 prévisions horaires actualisées, éventuellement avec Streamlit, si le temps et les résultats techniques le permettent. Aucun composant de prévision ou d'interface n'est développé. L'étude porte sur les prérequis de source, disponibilité, compatibilité et horodatage.

État initial local : `main`, commit `cf8acc4`, répertoire de travail propre, suivi local `origin/main` sans interrogation distante Git. Lecture de `AGENTS.md`, du README et du [protocole de Mission 011](011_protocole_prevision_evaluation.md). Les métadonnées et le manifeste historiques, les scripts d'acquisition/préparation, les tests et les en-têtes et premières lignes des deux CSV ont été examinés. Le dossier `experiments/` n'existait pas ; son absence, signalée par `rg`, n'est pas un échec d'accès aux données.

## 2. Sources officielles et portée des preuves

Toutes les références suivantes ont été consultées le 6 novembre 2026 via l'outil web. Les réponses de consultation peuvent être mises en cache : elles servent de documentation, pas de test réseau depuis le Python local. Les extraits sont courts ; les sections indiquées permettent de vérifier les affirmations.

| Réf. | Source et URL exacte | Repère utile |
| --- | --- | --- |
| S1 | [ODRÉ — Données éCO2mix nationales temps réel](https://odre.opendatasoft.com/explore/dataset/eco2mix-national-tr/) | Description, identifiant et paragraphe sur le quota ; rafraîchissement « tous les quarts d'heure » |
| S2 | [Métadonnées Explore API v2.1](https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/eco2mix-national-tr) | `fields`, `metas.default`, `metas.custom`, `metas.dcat` ; contenu présenté comme exploré la veille par l'outil |
| S3 | [Documentation officielle Explore API v2.1, Opendatasoft/Huwise](https://help.opendatasoft.com/apis/ods-explore-v2/) | Introduction, Authentication, `GET /catalog/datasets/{dataset_id}/records`, paramètres `limit`, `offset`, `timezone` et erreurs HTTP |
| S4 | [RTE — Spécification des fichiers en puissance, juin 2025](https://assets.rte-france.com/prod/public/2025-06/Eco2mix%20-%20Sp%C3%A9cifications%20des%20fichiers%20en%20puissance.pdf) | §1.1 p. 1 ; §3.1 p. 3–4 et texte p. 6 ; distingue instantané et moyenne |
| S5 | [RTE — La consommation d'électricité en France](https://www.rte-france.com/donnees-publications/eco2mix-donnees-temps-reel/consommation-france) | Rubrique consommation, périmètre, pertes, pompage et révisions |
| S6 | [RTE — Changement d'heure : quel impact ?](https://www.rte-france.com/getPDF?uuid=3bbf009a-ca0c-40f0-9b45-1c6958066f13) | Note du 25 octobre 2019, p. 1 : besoin d'une 25e heure ; ne décrit pas l'encodage API |
| S7 | [Etalab — Licence Ouverte 2.0](https://github.com/etalab/licence-ouverte/blob/master/LO.md) | Rubriques réutilisation et paternité |
| S8 | [Console API ODRÉ](https://odre.opendatasoft.com/explore/dataset/eco2mix-national-tr/api/?flg=fr) | Paramètre UTC et exemples indexés de `date`, `heure`, `date_heure` ; pas un flux actuel vérifié |

L'URL `/information/` a échoué via l'outil web ; la page racine S1 a été lisible. Une adresse RTE supposée `consommation-electrique-nationale` était inaccessible ; S5 est l'adresse retrouvée. Le PDF Etalab lié depuis les métadonnées, `https://www.etalab.gouv.fr/wp-content/uploads/2017/04/ETALAB-Licence-Ouverte-v2.0.pdf`, a échoué après redirection ; le texte officiel S7 a été consulté séparément. Ces échecs documentaires ne sont pas masqués ni assimilés à des résultats API.

## 3. Caractéristiques documentées de la source candidate

| Propriété | Information vérifiée dans la documentation | Limite |
| --- | --- | --- |
| Identifiant et API | `eco2mix-national-tr` ; S2 ; endpoint `/records` sous le même chemin | Le script n'a pas pu confirmer la réponse courante |
| Champs utiles | `consommation` : entier, libellé MW ; `nature`, `perimetre`, `date`, `heure`, `date_heure` : datetime pour ce dernier (S2) | Les prévisions RTE `prevision_j1` et `prevision_j` sont distinctes d'observations ; non utilisées |
| Territoire | Champ `perimetre` décrit comme France ; RTE précise métropole hors Corse, pertes incluses et pompage STEP exclu (S2, S5) | La correspondance exacte de cette définition avec le champ historique reste à documenter |
| Nature | Télémesures et estimations ; S4 décrit l'instantané temps réel et les moyennes consolidées/définitives | `nature` n'est pas équivalent par simple renommage à `statut_rte` |
| Cadence | Consommation au quart d'heure et actualisation annoncée toutes les 15 minutes (S1) | Ni cadence effectivement observée ici ni garantie de retard maximal |
| Profondeur annoncée | `metas.custom.profondeur-dhistorique` : « Plusieurs mois à H-2 » (S2) | H−2 suggère un décalage ; aucun délai exact de publication garanti n'est démontré |
| Historique et révisions | Remplacement progressif vers les données consolidées puis définitives ; produit distinct `eco2mix-national-cons-def` (S1, S4) | Aucune rétention fixe de 30 jours n'est présumée pour ce portail actuel |
| Fuseau | `metas.default.timezone` : `Europe/Paris` (S2) ; paramètre `timezone=UTC` disponible (S3) | Le fuseau d'affichage ne définit pas un support physique ni toute la conversion amont |
| Licence | Licence Ouverte v2.0 indiquée (S2) ; S7 autorise la réutilisation avec mention de source et dernière mise à jour | Conserver RTE/ODRÉ, URL et version/date ; ne pas présenter les prévisions du projet comme celles de RTE |
| Accès et limites | GET public possible selon S3 ; S1 annonce 50 000 appels API par utilisateur et par mois | Authentification anonyme non démontrée depuis le script ; pas de test de quota ni de garantie de service |
| Pagination | S3 : limite 100 sans regroupement, `offset+limit < 10000`, pagination par offset, erreurs dont 429 | L'étude utilise au plus 200 lignes récentes, sans export massif |

La vue documentaire S2 mentionne 6 336 enregistrements et `data_processed = 2026-11-04T19:01:20+00:00`. Ces valeurs viennent d'une réponse présentée comme explorée la veille, **pas d'un appel local réussi le 6 novembre**. Elles ne prouvent ni la couverture courante ni la fraîcheur. `modified = 2026-01-28T09:37:12+00:00` est descriptif. La périodicité générique `metas.dcat.accrualperiodicity = Horaire` diffère du quart d'heure annoncé dans S1 : conserver cette divergence au lieu d'en déduire un retard réel. Un avis de maintenance daté du 4 novembre 2026 apparaît dans S2 ; il ne prouve pas la cause du refus socket local.

## 4. Méthode et résultat réel du test Python

Le [script autonome](../experiments/faisabilite_application/inspect_eco2mix_api.py) emploie uniquement la bibliothèque standard. Il ne lit ni ne transforme les données électriques historiques. Il commence par les métadonnées pour vérifier le schéma, puis prévoit deux pages récentes et une seule ligne ancienne. Les réponses sont bornées, les délais explicites et les sorties exclusives dans un nouveau sous-dossier `runs/` ignoré par Git. Aucun identifiant secret, relance automatique, export ou redirection suivie.

Commande réellement exécutée depuis la racine :

```powershell
.\.venv\Scripts\python.exe experiments/faisabilite_application/inspect_eco2mix_api.py
```

| Élément | Résultat constaté |
| --- | --- |
| Requête effectivement tentée | GET `https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/eco2mix-national-tr`, paramètres `{}` |
| Début UTC | `2026-11-06T13:12:43.777974+00:00` |
| Fin UTC | `2026-11-06T13:12:43.898195+00:00` |
| Code HTTP | Aucun (`null`) ; aucune réponse HTTP obtenue |
| Lignes récupérées | Aucune ; nombre de lignes distant non mesurable |
| Résultat de processus | Code 1, état `incomplete` |
| Journal local | `experiments/faisabilite_application/runs/20261106T131243776748Z_f0ca140a/audit.json` |

Erreur exacte conservée dans le journal :

```text
URLError: [WinError 10013] Une tentative d’accès à un socket de manière interdite par ses autorisations d’accès a été tentée
```

Le message indique un refus d'autorisation de socket sur le chemin d'exécution local, avant une réponse du serveur. Il ne permet pas de départager précisément le confinement d'exécution, les règles de sécurité Windows ou d'autres contrôles réseau locaux ; aucune conclusion sur la connexion Internet seule ou sur une panne ODRÉ n'est justifiée. Aucune restriction n'a été contournée.

Le schéma ne pouvant être vérifié, **aucun appel `/records` n'a été exécuté par le script**. Les paramètres préparés mais non testés réellement sont :

```text
select=date_heure,date,heure,consommation,nature,perimetre
timezone=UTC
where=date_heure <= date'<heure UTC de début de l'audit>'
order_by=date_heure desc
limit=96
offset=0 puis 96
```

La requête ancienne prévue utilise le même `select`, `timezone=UTC`, `order_by=date_heure asc`, `limit=1`. Elle n'est pas exécutée non plus. Une borne récente commune limite les changements entre pages sans garantir un instantané transactionnel en cas de corrections ou d'insertions tardives. Le script diagnostique les doublons sans sélectionner une variante ; la dernière valeur candidate utilisable doit avoir une étiquette unique dans l'échantillon.

## 5. Fraîcheur et disponibilité

| Indicateur | Résultat de cette étude |
| --- | --- |
| Dernier horodatage actuel effectivement récupéré par Python | Non disponible |
| Âge du dernier timestamp / de la dernière consommation exploitable | Non calculable ; jamais remplacé par zéro |
| Nature et nulls de la dernière valeur | Non observés |
| Pas récents, trous, doublons et profondeur accessible actuels | Non mesurés |
| Délai annoncé | Rafraîchissement quart-horaire et indication H−2 ; pas une même notion |
| Délai de publication démontré | Aucun ; aucune observation réseau réussie |

Les exemples de S8 illustrent une représentation UTC/locale, mais ne sont pas triés ou certifiés récents et peuvent être indexés. Ils ne sont pas utilisés pour calculer un âge, une distribution de délais ou un taux de disponibilité. Même une réponse fraîche unique ne démontrerait pas la stabilité quotidienne du service.

Lors d'une future exécution réussie, le script conservera l'heure d'envoi et de réception de chaque requête, l'âge signé du timestamp à la réception, le statut `nature`, les valeurs nulles et les pas uniques observés. Le temps de requête et un éventuel cache HTTP doivent être examinés ; l'heure de première publication n'est pas fournie par le timestamp de mesure ou le traitement global du dataset.

La [notice d'exécution](../experiments/faisabilite_application/README.md) permet de répéter l'audit manuellement à plusieurs dates et heures sans écraser les précédents. Prévoir une campagne raisonnable autour de 00:00 UTC et à plusieurs moments de la journée, sans cadence supérieure à celle justifiée par les mises à jour. Pour encadrer une première apparition entre deux audits, il faut avoir effectivement interrogé la même plage et constaté une absence puis une présence, sans erreur ni limite de pagination masquant la ligne. Une absence hors de l'échantillon récent n'est pas une preuve de non-publication ; un retrait de la fenêtre roulante n'est pas une suppression certifiée. Conserver les versions des champs d'une même étiquette permettrait d'étudier les révisions, pas de reconstruire celles antérieures au début du suivi.

## 6. Faisabilité à 00:00 UTC et horaires alternatifs

Le protocole de Mission 011 reste inchangé : origine envisagée à 00:00 UTC, H+1 sur `[t,t+1 h)`, puis 24 heures écoulées. Aucun panel concret de variables n'a encore été construit. La disponibilité de ses historiques n'est donc pas validée ici.

| Famille d'information | Condition pour une émission à t |
| --- | --- |
| Dernière consommation | Mesure achevée selon sa nature et version effectivement publiée à t ; l'étiquette seule ne suffit pas |
| Retards et moyennes mobiles | Tous les points nécessaires présents et accessibles à t ; aucune fenêtre raccourcie ni interpolation implicite |
| Référence quotidienne à H+24 | Dans le protocole horaire, l'heure de référence finit à t : elle n'est pas nécessairement déjà publiée |
| Référence hebdomadaire | Historique suffisant, mêmes définitions et disponibilité vérifiée ; profondeur de quelques jours non garantie par un échantillon de 48 h |
| Calendrier | Instants UTC et informations calendaires calculables à l'avance ; ne pas confondre week-end et jour férié |
| Nature provisoire | Ne pas la traiter comme une puissance définitive de même définition ; qualifier l'éventuel décalage apprentissage/production |

**Exemple conditionnel, non observé :** si la dernière étiquette réellement accessible à 00:00 UTC était celle de 22:00 UTC la veille, les étiquettes 22:15 à 23:45 ne seraient pas établies comme disponibles. Une statistique nécessitant l'intégralité de ces instants échouerait ; il faudrait un historique arrêté plus tôt, explicitement conçu et validé. L'indication H−2 de S2 motive ce contrôle, sans prouver que cet exemple représente le comportement réel.

Des audits manuels à 02:00 ou 03:00 UTC pourraient vérifier si les points manquants à minuit sont alors publiés. Aucune disponibilité précise à ces heures n'a été constatée. Si les horizons restaient les 24 prochaines heures à partir de la nouvelle émission, la fenêtre cible changerait ; si la fenêtre de minuit était conservée, des cibles seraient déjà passées. Retarder l'émission ne garantit pas que la dernière heure précédant cette nouvelle origine soit publiée. Ces variantes restent exploratoires et ne modifient pas la Mission 011.

## 7. Compatibilité avec l'historique et comparaison A/B

| Dimension | Historique local et scénarios A/B | Candidat temps réel | Conclusion |
| --- | --- | --- | --- |
| Variable | `consommation_brute_electricite_rte`, puis `electricity_mw` | `consommation` | Noms distincts ; pas de renommage suffisant |
| Unité et territoire | MW, métropole hors Corse, métadonnées locales | MW, national hors Corse selon S2/S5 | Correspondance générale, pas équivalence physique prouvée |
| Nature | Source demi-horaire, moyenne supposée ; statuts historiques | Instantanés télémesurés/estimés selon S4 | Risque de changement de grandeur et de distribution |
| Temps | Grille UTC 30 min ; sorties `[h,h+1 h)` hypothétiques | Points quart-horaires, fuseau paramétrable | Une moyenne de quatre points n'est pas automatiquement une moyenne horaire physique |
| Qualité | Conflits, absents, statuts, flags et provenance ; strict technique | `nature`, nulls et versions à auditer | Aucun dictionnaire d'équivalence automatique |
| Couverture | CSV disponibles jusqu'au 30 septembre 2026, intervalle final à 21:00 UTC | Profondeur actuelle non mesurée | Aucune période commune effectivement récupérée |
| Révisions | Archive de novembre, accessibilité historique inconnue | Révisions annoncées vers d'autres qualités/produits | Les séries révisées ne remplacent pas des versions de production archivées |

Les schémas locaux réels contiennent les 14 champs documentés dans [la préparation horaire](preparation_horaire_experimentale.md), dont `hour_start_utc`, `hour_end_utc`, `strict_electricity_mw`, `source_timestamps_utc`, `source_positions`, `source_statuses`, `source_flags`, `source_quality` et `timestamp_convention`. Les valeurs de convention sont `experimental_start_label` pour A et `experimental_end_label` pour B. Les préparations et leurs fichiers sont inchangés.

**Aucune comparaison numérique n'est scientifiquement forcée.** Ni période commune ni alignement physique ne sont établis ; les nombres de paires, exclusions et écarts sont donc non calculés, et non des zéros. Aucune corrélation n'est calculée. La moyenne de quatre instantanés serait une nouvelle approximation de cible, non une reproduction démontrée des moyennes historiques.

Un test ultérieur pourrait être proposé après clarification des supports : identifier une petite période commune réellement accessible, conserver ses versions, normaliser les instants UTC sans corriger arbitrairement les sources, imposer une méthode d'intégration/agrégation justifiée et vérifier les correspondances exactes des composantes. Compter séparément, pour A et B, les paires strictes et tous les motifs d'exclusion sur des clés comparables. Les écarts éventuels seraient descriptifs, susceptibles de refléter nature physique, révisions, estimation ou alignement, sans attribution causale ni preuve d'équivalence. Ce test n'est ni lancé ni autorisé implicitement par sa description.

## 8. Audit des horodatages et tests synthétiques

S4 qualifie les valeurs temps réel d'instantanées ; son tableau parle de points quart-horaires. Il ne décrit pas à lui seul toutes les transformations de `date_heure` dans ODRÉ. S2 donne un datetime sans description sémantique et un fuseau de métadonnées `Europe/Paris` ; S3 documente l'option UTC. S8 présente notamment une date locale estivale dont l'heure est supérieure de deux heures à son datetime UTC. C'est un exemple documentaire, pas un audit expérimental des conversions du flux.

Pour attribuer à chaque timestamp ODRÉ un instant exact de prélèvement, un début ou une fin de support et certifier les conversions autour des transitions : **Je ne peux pas confirmer cette convention à partir des sources consultées.** Pour les puissances instantanées documentées, un support moyen de 15 minutes ne doit pas être inventé.

Les fonctions nouvelles rejettent les heures sans offset, normalisent les offsets explicites en UTC, et énumèrent les instants entre deux minuits locaux convertis séparément. Les tests synthétiques couvrent :

- 29 mars 2026 : 23 heures locales, saut de l'heure 02:00, grille UTC continue ;
- 25 octobre 2026 : 25 heures locales, deux occurrences de 02:00 avec offsets et `fold` distincts ;
- minuit local estival du 1er juillet 2026 : correspondance au 30 juin 22:00 UTC ;
- âge signé au changement de jour UTC, horodatages futurs, absents ou invalides ;
- doublons non sélectionnés, trous quart-horaires et discordances du calendrier source ;
- parsing des réponses, schéma, limites, HTTP 429, erreurs réseau, taille, JSON invalide et absence d'écrasement.

Ces tests prouvent le comportement logiciel sur des exemples contrôlés. Ils ne prouvent ni l'absence d'anomalies saisonnières du dataset actuel ni l'exactitude de la conversion effectuée par son producteur. La note S6 confirme l'enjeu d'une 25e heure, sans résoudre les conflits UTC historiques. L'ambiguïté A/B demeure entière.

## 9. Architecture minimale envisageable, sans implémentation

```text
API officielle -> acquisition bornée -> journal/versionnement des observations
              -> contrôles de schéma, disponibilité, qualité et fraîcheur
              -> préparation physiquement compatible, puis variables admissibles à t
              -> modèle validé et enregistré -> 24 prévisions identifiées en UTC
              -> journal des émissions -> interface éventuelle Streamlit
```

La récupération doit être indépendante du rafraîchissement de l'interface pour ne pas multiplier les appels par visite. Il faudrait un stockage persistant et une politique de versions, une alerte sur les données anciennes, un traitement des réponses vides et des quotas, ainsi qu'une règle d'abstention si une entrée indispensable manque. Une ancienne prévision conservée doit porter son origine et son état périmé ; elle ne devient pas une nouvelle émission. Les champs de prévision RTE ne doivent pas être présentés comme des sorties du modèle du projet.

Un modèle enregistré, son schéma de variables, sa version et son hypothèse de cible sont indispensables, mais aucun modèle n'existe dans cette étude. Le journal devrait conserver origine UTC, instants cibles, scénario, empreintes des données accessibles, heures de récupération, version du modèle et raisons d'un refus. L'observation ultérieure de la cible et ses révisions permettraient une évaluation différée distincte, après définition de la vérité de référence.

Un prototype local pourrait associer des lancements manuels et une interface de lecture sur une machine allumée, après levée des blocages. Une application hébergée exigerait en plus exécution périodique durable, stockage persistant, accès réseau autorisé, surveillance, gestion des pannes et budget de requêtes partagé. Un cache d'interface ne garantit pas l'acquisition pendant l'absence de visiteurs. Aucun serveur, compte, dépendance, ordonnanceur ou service n'est créé.

## 10. Contrôles, risques et priorités

Les nouveaux fichiers pérennes sont le script, sa notice, son `.gitignore`, [les tests synthétiques](../tests/test_inspect_eco2mix_api.py) et ce rapport. Le seul journal réseau réel est le JSON local ignoré indiqué en section 4. Les résultats de la suite complète et des contrôles finaux sont consignés dans le compte rendu ; aucun succès réseau n'est déduit des tests simulés.

Contrôles effectivement exécutés le 6 novembre 2026 : **69 tests réussis en 2,010 s**, soit les 49 tests existants et 20 nouveaux ; contrôle documentaire avec `--include-untracked` sur **25 fichiers**, sans erreur ni avertissement ; `git diff --check` sans anomalie. Le premier passage de la suite complète avait réussi avec un `ResourceWarning` concernant la fermeture de l'erreur HTTP 429 simulée. La fermeture explicite de cette ressource a été ajoutée dans le nouveau script ; la seconde exécution complète ci-dessus ne présente plus cet avertissement. Aucun test réseau réussi n'est revendiqué.

Les empreintes SHA-256 des **48 fichiers préexistants contrôlés** sont inchangées, notamment celles du brut, des métadonnées, de la grille, des CSV A/B, des scripts et des travaux des Missions 010 et 011. Les nouveaux textes ont été contrôlés séparément : aucun espace final ni chemin personnel absolu, six liens internes valides. `git check-ignore -v` confirme que le journal `runs/` est ignoré. L'état final ne présente que cinq nouveaux fichiers non suivis ; les différences de fichiers suivis et l'index sont vides. Aucun ajout, commit ou push n'est réalisé.

Priorités avant toute application :

1. Obtenir une exécution réseau autorisée du script et répéter les audits, notamment autour de minuit, sans contourner le refus socket.
2. Établir la fraîcheur réelle, les retards variables, la couverture des historiques et les versions ; distinguer âge visible et première publication.
3. Clarifier auprès de preuves techniques applicables la nature et l'horodatage ODRÉ et la filiation avec le champ historique, sans choisir A/B selon un score.
4. Définir les variables utilisables et leurs fenêtres avant une future comparaison ; la météo n'est pas ajoutée.
5. Vérifier séparément chaque raccordement A/B sur une période commune si une comparaison physique devient justifiable.
6. Disposer ultérieurement d'un modèle validé, d'une gestion de l'abstention et d'un journal d'émissions avant l'affichage de nouvelles prévisions.

## 11. Diagnostic réseau et premier audit de fraîcheur

Complément du 6 novembre 2026. Les résultats précédents restent des constats de l'étude initiale ; ils ne sont pas remplacés rétroactivement. Aucun audit réussi d'observations n'est obtenu dans ce complément.

### 11.1 Environnement et contrôles locaux

État initial de ce complément : branche `main`, fichiers de l'expérience déjà non suivis, aucune différence de fichier suivi. Le terminal exécuté par Codex utilise Windows PowerShell **5.1.26100.9711**, édition Desktop. Python **3.14.6** est bien celui de `.venv/Scripts/python.exe` à la racine du projet, vérifié par comparaison des chemins résolus. Le chemin personnel absolu n'est pas reproduit. Le PowerShell ordinaire ouvert dans VS Code n'a pas été exécuté ni observé depuis cette session : une comparaison de ses permissions reste nécessaire.

Les huit variantes usuelles de variables de proxy (`HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY`, `NO_PROXY` et leurs variantes minuscules) sont absentes. `urllib.request.getproxies()` ne détecte aucun schéma de proxy. Les variables `SSL_CERT_FILE`, `SSL_CERT_DIR`, `REQUESTS_CA_BUNDLE`, `CURL_CA_BUNDLE` sont absentes. Cela ne démontre ni la validité des certificats ni l'absence de tout intermédiaire réseau.

La lecture des paramètres Internet du profil Windows courant indique un proxy explicite non activé, sans adresse de serveur ni URL de configuration automatique renseignées. Aucune adresse de proxy, aucun identifiant ni jeton n'est affiché. Ce contrôle ne couvre pas toutes les politiques système, tous les mécanismes automatiques ou le chemin réseau d'un autre processus.

| Niveau | Commande effectivement exécutée | Résultat et heure UTC |
| --- | --- | --- |
| DNS | `Resolve-DnsName odre.opendatasoft.com -DnsOnly -ErrorAction Stop` | Du `2026-11-06T13:26:01.6306776Z` au `2026-11-06T13:26:02.3552155Z` : alias `odre.outscale-euw2.opendatasoft.com`, IPv4 `109.232.232.161` et `5.104.97.33` |
| TCP | `Test-NetConnection odre.opendatasoft.com -Port 443 -InformationLevel Quiet -WarningAction Continue` | Du `2026-11-06T13:26:09.3757833Z` au `2026-11-06T13:26:09.5994301Z` : deux avertissements d'échec, résultat `False` |
| HTTPS | `Invoke-WebRequest -UseBasicParsing -Uri $apiUri -Method Get -TimeoutSec 15 -ErrorAction Stop` | Du `2026-11-06T13:26:20.1406518Z` au `2026-11-06T13:26:20.3503190Z` : erreur de connexion, aucune réponse HTTP |
| Python | Contrôle de version, interpréteur, chemins et détection de proxy ; lecture du script puis `--help` | Interpréteur attendu confirmé. Aucun nouvel appel Python réseau après le refus HTTPS ; l'échec Python historique reste celui de 13:12:43 UTC |

Dans la commande HTTPS, `$apiUri` vaut exactement `https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/eco2mix-national-tr`, sans paramètre ni authentification. Les erreurs recueillies sont :

```text
TCP connect to (109.232.232.161 : 443) failed
TCP connect to (5.104.97.33 : 443) failed
False

System.Net.WebException : Impossible de se connecter au serveur distant
System.Net.Sockets.SocketException : Une tentative d’accès à un socket de manière interdite par ses autorisations d’accès a été tentée 5.104.97.33:443
```

**Cause précise indéterminée.** La résolution DNS réussit ; ce n'est donc pas un échec général de résolution de ce domaine lors du contrôle. Le refus se produit aussi avec la pile HTTPS PowerShell, ce qui exclut une explication limitée à `urllib` ou au seul interpréteur Python pour ces tentatives. Aucune erreur de certificat TLS, authentification proxy ou erreur HTTP du serveur n'est observée. Cela ne certifie pas que ces couches fonctionneraient après résolution du refus socket.

Le profil de l'environnement d'exécution indique un accès réseau restreint. Les refus observés sont compatibles avec cette restriction, mais ne permettent pas d'identifier la règle exacte ni de départager cette couche d'autres contrôles Windows ou réseau. Aucune responsabilité exclusive du pare-feu, de l'antivirus, de la connexion Internet ou du serveur ODRÉ n'est démontrée. Aucun accès administrateur, changement de proxy, exception de sécurité, désactivation de protection ou exécution hors confinement n'est tenté.

### 11.2 Conséquences pour l'audit API et la fraîcheur

L'HTTPS local ne fonctionnant pas, le script n'a pas été relancé pour récupérer des observations. La limite de quatre requêtes potentielles et les arguments existants ont été relus, sans modification du code. Aucun nouveau dossier d'acquisition n'est créé. Le premier journal incomplet de 13:12:43 UTC est préservé.

Il n'y a donc toujours aucun code HTTP, aucune ligne reçue, aucun dernier timestamp de consommation, statut, pas observé, nombre de doublons ou âge calculable issus d'un audit local réussi. Ces indicateurs sont **non mesurés**, pas égaux à zéro. Aucune observation à minuit n'est disponible pour conclure à une émission réalisable à 00:00 UTC. Les scénarios A/B ne sont pas raccordés.

### 11.3 Comparaison manuelle dans un terminal ordinaire

La [notice de l'expérience](../experiments/faisabilite_application/README.md#diagnostic-réseau-et-premier-audit-de-fraîcheur) fournit les commandes à lancer depuis la racine dans un PowerShell Windows ordinaire, sans privilège administrateur. Les mêmes domaine, endpoint et interpréteur sont utilisés ; les paramètres réseau et de sécurité sont conservés. La commande du script n'est exécutée que si une réponse HTTP 200 est reçue.

Si le test externe réussit alors que les tests ci-dessus échouent, cela établira une différence entre contextes d'exécution, sans identifier automatiquement le composant responsable. Si l'HTTPS PowerShell fonctionne mais que le script Python échoue, les résultats de l'interpréteur, de la détection de proxy et les erreurs TLS/HTTP permettront un diagnostic comparatif supplémentaire. Aucun de ces cas n'est constaté actuellement.

Après une éventuelle réussite, transmettre uniquement les statuts, horaires UTC, erreurs non sensibles et le chemin relatif du nouvel `audit.json`. Ses métadonnées et ses champs d'audit permettront de vérifier les valeurs et leur âge avant toute conclusion. Ne pas transmettre de jeton, d'en-tête d'authentification, de cookie ou de configuration de proxy contenant des identifiants.

Une fois le script réellement exploitable, répéter manuellement la même commande en journée, en soirée et autour de 00:00 UTC sur plusieurs jours, avec des journaux distincts. Aucun automatisme permanent n'est créé. L'âge à réception reste distinct du délai réel de publication ; l'observation à minuit et l'accès aux fenêtres requises restent à établir. Le verdict B demeure inchangé.

Contrôles de ce complément : **69 tests réussis en 1,279 s** ; contrôle documentaire sur **25 fichiers**, sans erreur ni avertissement ; `git diff --check` sans anomalie. Les deux documents modifiés ont aussi été contrôlés séparément pour les espaces finaux et l'existence des fichiers liés. Les empreintes des **51 autres fichiers contrôlés** sont inchangées, y compris les données et les Missions 010/011. Aucun nouveau fichier n'est ajouté par ce complément ; les fichiers non suivis de l'étude initiale restent présents, l'index est vide.

## 12. Analyse hors ligne du premier journal réussi

Complément du 6 novembre 2026 : analyse du journal existant `experiments/faisabilite_application/runs/20261106T133016185908Z_6022c66f/audit.json`, sans relance de l'API ni nouvel accès réseau. Son empreinte SHA-256 est `b5d11aad8c5ad5d927b41a5b49adf5ac252ac3b225db7ff732ae6dfff791dc23`. Le fichier est lu sans modification ; les résultats négatifs des sections précédentes restent des constats historiques.

Le responsable du projet rapporte un succès DNS, TCP et HTTPS depuis le PowerShell Windows ordinaire. Le journal lu permet de vérifier séparément quatre réponses HTTP 200 enregistrées par le script, sans erreur consignée. Il ne contient pas les sorties DNS/TCP du terminal ni sa configuration complète. La différence entre contextes d'exécution est désormais étayée, mais la règle précise responsable des refus antérieurs reste indéterminée. Aucun nouveau succès dans l'environnement d'exécution Codex n'est revendiqué.

### 12.1 Requêtes enregistrées et métadonnées

État enregistré : `complete_sample`. Début : `2026-11-06T13:30:16.187345+00:00` ; fin : `2026-11-06T13:30:18.638448+00:00`, soit 2,451103 secondes. Quatre corps de réponse totalisent 73 358 octets selon le journal. L'accès du script ne comporte pas d'authentification.

La base exacte est `https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/eco2mix-national-tr`. Les trois requêtes d'observations ajoutent `/records`. Tous les instants du tableau sont en UTC, le 6 novembre 2026.

| Requête | Début UTC | Réception UTC | HTTP | Lignes | `total_count` |
| --- | --- | --- | ---: | ---: | ---: |
| Métadonnées, paramètres `{}` | 13:30:16.187362 | 13:30:16.452952 | 200 | Sans objet | Sans objet |
| Page 1, offset 0 | 13:30:16.453130 | 13:30:18.046390 | 200 | 96 | 4 500 |
| Page 2, offset 96 | 13:30:18.103099 | 13:30:18.385820 | 200 | 96 | 5 500 |
| Première ligne selon tri ascendant | 13:30:18.387466 | 13:30:18.636216 | 200 | 1 | 5 500 |

Les deux pages utilisent exactement le même filtre et le même tri, hormis l'offset :

```text
select=date_heure,date,heure,consommation,nature,perimetre
timezone=UTC
where=date_heure <= date'2026-11-06T13:30:16.187345+00:00'
order_by=date_heure desc
limit=96
offset=0 puis 96
```

La requête ancienne conserve le même `select` et `timezone=UTC`, utilise `order_by=date_heure asc`, `limit=1`, sans filtre `where`. Ses effectifs ne portent donc pas sur une sélection identique aux pages filtrées. Les URL complètes encodées sont conservées dans `requests[].called_url` du journal ; aucun nouvel endpoint n'est interrogé pour cette analyse.

Les métadonnées récupérées identifient `eco2mix-national-tr`, UID `da_36r18k`, producteur RTE, Licence Ouverte v2.0, fuseau descriptif `Europe/Paris`, pas annoncé quart-horaire et profondeur annoncée « Plusieurs mois à H-2 ». Elles indiquent `records_count = 6528` et `data_processed = 2026-11-06T13:15:10+00:00` ; `modified = 2026-01-28T09:37:12+00:00`, version non renseignée. Le traitement global ne constitue pas une date de publication de chaque consommation ; le nombre de métadonnées ne garantit pas une réponse transactionnelle avec les pages suivantes.

| Champ sélectionné | Type déclaré dans les métadonnées | Vérification dans les lignes conservées |
| --- | --- | --- |
| `date_heure` | datetime | Texte ISO avec offset UTC explicite, interprétable |
| `date`, `heure` | text | Calendrier local cohérent avec `Europe/Paris` dans l'échantillon |
| `consommation` | int, libellé `Consommation (MW)` | Entiers strictement positifs, sans valeur nulle ni invalide |
| `nature` | text | `Données temps réel` pour les 193 lignes |
| `perimetre` | text | `France` pour les 193 lignes |

L'unité MW provient des métadonnées ; elle n'est pas déduite de l'amplitude des valeurs. Le libellé temps réel ne signifie ni valeur définitive, ni fraîcheur garantie, ni moyenne d'intervalle. Aucune conversion vers les statuts historiques n'est effectuée.

### 12.2 Valeurs observées et âges vérifiés

L'âge est recalculé par `réception UTC de la réponse − timestamp UTC de l'observation`. Les audits de chaque page et l'audit combiné ont été reproduits hors ligne avec les fonctions existantes et correspondent exactement aux champs enregistrés. Il s'agit d'un contrôle de calcul sur le JSON conservé, pas d'une nouvelle récupération des réponses originales. Leurs empreintes HTTP sont consignées, mais les corps complets originaux ne sont pas conservés pour une nouvelle vérification octet par octet.

| Échantillon | Bornes des étiquettes UTC conservées | Dernière puissance présente | Âge à réception de cette réponse |
| --- | --- | --- | --- |
| Page 1, offset 0 | Du 16 octobre 19:00 au 17 octobre 18:45, 2026 | 43 041 MW à `2026-10-17T18:45:00+00:00` ; local 20:45+02:00 | **1 709 118,046390 s**, soit **19 j 18 h 45 min 18,046390 s** |
| Page 2, offset 96 | Du 26 octobre 06:00 au 27 octobre 05:45, 2026 | 47 405 MW à `2026-10-27T05:45:00+00:00` ; local 06:45+01:00 | **891 918,385820 s**, soit **10 j 7 h 45 min 18,385820 s** |
| Ligne ancienne, tri ascendant | `2026-08-31T22:00:00+00:00` ; local 1er septembre 00:00+02:00 | 42 233 MW | **5 758 218,636216 s**, soit **66 j 15 h 30 min 18,636216 s** |

La dernière valeur du tableau ancien est l'unique ligne obtenue par tri ascendant ; elle ne fait pas partie des deux pages récentes et ne doit pas être interprétée comme leur dernière consommation. Les trois échantillons totalisent 193 étiquettes distinctes.

L'audit combiné porte seulement sur les 192 lignes des deux pages. Son âge enregistré pour la plus récente de ces lignes est **891 918,636216 s** : il utilise l'heure de réception de la dernière requête, à 13:30:18.636216 UTC, et non celle de la page 2. L'écart de 0,250396 seconde vient donc du choix de l'instant de consultation. Pour décrire sa disponibilité observée, l'âge de la page 2 est le repère le plus direct.

Ces âges ne sont **pas des délais réels de publication**. Le journal prouve qu'une version était visible à réception, pas quand elle est apparue pour la première fois, ni quand elle a été révisée. Les en-têtes `Date` sont enregistrés ; `Age` est absent. Cette absence ne démontre pas l'absence de cache ou de décalage entre répliques. Une seule exécution ne mesure pas une distribution de disponibilité.

### 12.3 Anomalie déterminante de pagination et limites de fraîcheur

Chaque page est strictement décroissante et régulière en interne, mais **leur ordre relatif est incompatible avec une pagination décroissante sur un état unique stable** : la page `offset=96` contient exclusivement des dates plus récentes que la page `offset=0`. Le `total_count` passe aussi de 4 500 à 5 500 entre deux requêtes partageant le même filtre. Il n'est donc pas possible de considérer leur concaténation comme les 192 observations les plus récentes d'un instantané cohérent.

Le compteur 6 528 des métadonnées, le total filtré et le total non filtré ne décrivent pas nécessairement la même sélection ni le même état. Leur différence ne prouve ni ajouts, ni suppressions, ni corrections déterminées. Pour le changement de 4 500 à 5 500 sur le même filtre, le constat est une incohérence entre réponses successives ; sa cause n'est pas établie par le journal. Une évolution du dataset, des caches, un état de traitement ou une autre variation de service restent des hypothèses non vérifiées, pas des explications confirmées.

**La consommation du 27 octobre est la plus récente présente dans les lignes conservées, pas la dernière consommation disponible sur toute l'API certifiée par cet audit.** Les âges de dix et dix-neuf jours ne démontrent donc ni un retard général de cette ampleur ni une fraîcheur conforme à H−2. `complete_sample` signifie ici que le script n'a détecté aucune erreur technique ou structurelle ; il ne garantit ni la cohérence entre pages ni l'aptitude à la prévision actualisée. Le script n'est pas modifié pour masquer cette limite.

Les 812 créneaux quart-horaires absents indiqués dans l'audit combiné correspondent à l'intervalle entre les deux blocs échantillonnés : **731 700 secondes**, soit **8 j 11 h 15 min**, séparent le 17 octobre 18:45 du 26 octobre 06:00. Ils sont absents de cet échantillon ; il serait incorrect d'en déduire 812 lacunes réelles de l'ensemble du dataset sans extraction cohérente de cette période.

### 12.4 Qualité et cohérence temporelle de l'échantillon

Les deux pages comprennent chacune 96 consommations positives finies, 96 timestamps uniques et 95 pas de 900 secondes. Aucun doublon, timestamp invalide, point futur, point hors grille quart-horaire, champ sélectionné manquant ou valeur nulle n'est trouvé dans ces pages. La ligne ancienne possède également les six champs non nuls et une consommation entière positive. Ces contrôles ne certifient pas la justesse physique des valeurs ni les lignes non téléchargées.

Sur les 192 lignes combinées : 190 différences de 900 secondes, une différence de 731 700 secondes, aucune étiquette dupliquée. Les conversions `Europe/Paris` correspondent aux dates et heures sources : +02:00 en septembre et le 17 octobre ; +01:00 le 27 octobre. Aucun point du 25 octobre, jour de transition saisonnière, n'est présent dans cet échantillon : le bon encodage réel de ses heures répétées n'est pas vérifié par cette exécution.

Les six champs conservés ne renseignent ni le support physique d'un point ni sa date de publication. Les incertitudes de la section 8 sur la transposition à une puissance horaire et les conventions A/B demeurent. Aucune agrégation, correction, interpolation ou comparaison numérique avec les fichiers A/B n'est effectuée.

### 12.5 Conséquences pour une application et l'émission à minuit

L'accès public HTTPS et la récupération automatique d'un échantillon de consommations non nulles sont désormais étayés par ce journal, dans le contexte d'exécution externe rapporté. Le succès DNS/TCP est une déclaration du responsable du projet, distincte des réponses HTTP consignées et relues. Une panne globale permanente d'ODRÉ ou une incompatibilité générale de Python ne peuvent pas expliquer à elles seules le contraste avec les refus précédents ; la règle locale exacte reste à identifier.

L'aptitude des observations aux variables d'une prévision actuelle n'est toutefois pas démontrée. La tentative réussie date de **13:30 UTC**, pas de minuit ; elle fournit des blocs anciens et temporellement incohérents entre pages. Des mesures portant une heure locale proche de minuit ne prouvent pas qu'elles étaient accessibles à minuit à leur date d'observation. La référence quotidienne à H+24, les retards récents et les fenêtres glissantes exigent toujours une disponibilité explicitement vérifiée.

Avant un prototype de prévision actualisée, les vérifications prioritaires sont :

1. Examiner la cohérence du tri et des totaux sur de futurs audits autorisés, en conservant leurs réponses et les conditions de consultation ; une requête légère distincte visant le maximum horodaté et la consommation non nulle pourrait aider, sans remplacer une vérification de couverture. Aucun appel supplémentaire n'est exécuté dans cette analyse.
2. Déterminer une borne récente fiable et les versions réellement accessibles ; ne pas utiliser automatiquement les blocs conservés comme contexte d'une prévision du 6 novembre.
3. Répéter manuellement les observations en journée, en soirée et autour de 00:00 UTC sur plusieurs jours. Comparer des plages de requête identiques pour encadrer les premières apparitions, sans assimiler absence hors échantillon et absence de publication.
4. Confirmer les définitions physiques et l'alignement avant tout raccordement aux historiques A/B ; conserver ces deux expériences séparées et le protocole de Mission 011 inchangé.

Le verdict reste **B** : la récupération technique est mieux établie, mais les prérequis déterminants d'un prototype prévisionnel, dont la fraîcheur fiable et la compatibilité des entrées, ne sont pas encore démontrés. Aucune prévision, variable explicative, performance, application ou nouvelle donnée historique n'est produite.

### 12.6 Contrôles de cette analyse du journal

Résultats effectivement obtenus : **69 tests réussis en 1,363 s**, contrôle documentaire sur **25 fichiers** sans erreur ni avertissement, `git diff --check` sans anomalie. Les espaces finaux et les six liens locaux du rapport sont aussi contrôlés, car le document reste hors suivi Git à cette étape. Les audits enregistrés des pages et de leur combinaison ont été reproduits à l'identique hors ligne ; les contrôles complémentaires ont mis en évidence l'incohérence entre pages non détectée par l'état technique `complete_sample`.

Seul le présent rapport est modifié pendant cette analyse. Les empreintes des **54 autres fichiers contrôlés** restent identiques, notamment le journal analysé, les données historiques, les préparations A/B et les travaux des Missions 010/011. Aucun nouveau fichier n'est créé. Le journal reste ignoré par Git ; l'index est vide. L'état Git conserve les fichiers exploratoires déjà non suivis au début de cette tâche. Aucun appel réseau, ajout à l'index, commit ou push n'est effectué.

## 13. Audit documentaire du tri et préparation d'un contrôle sans pagination

Complément du 6 novembre 2026, consultation documentaire close à `2026-11-06T14:17:02Z`. Le journal de 13:30 est réexaminé hors ligne. Aucun nouvel appel aux endpoints de données ODRÉ n'est effectué ; la consultation web porte uniquement sur la documentation officielle. Les restrictions réseau déjà constatées ne sont pas contournées.

### 13.1 Paramètres et URL du journal initial

Les quatre URL suivantes sont reprises de `requests[].called_url`. Leur décodage avec `urllib.parse.parse_qs` correspond exactement aux paramètres enregistrés, sans paramètre dupliqué ni différence cachée entre les filtres des deux pages.

```text
https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/eco2mix-national-tr

https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/eco2mix-national-tr/records?select=date_heure%2Cdate%2Cheure%2Cconsommation%2Cnature%2Cperimetre&timezone=UTC&where=date_heure+%3C%3D+date%272026-11-06T13%3A30%3A16.187345%2B00%3A00%27&order_by=date_heure+desc&limit=96&offset=0

https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/eco2mix-national-tr/records?select=date_heure%2Cdate%2Cheure%2Cconsommation%2Cnature%2Cperimetre&timezone=UTC&where=date_heure+%3C%3D+date%272026-11-06T13%3A30%3A16.187345%2B00%3A00%27&order_by=date_heure+desc&limit=96&offset=96

https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/eco2mix-national-tr/records?select=date_heure%2Cdate%2Cheure%2Cconsommation%2Cnature%2Cperimetre&timezone=UTC&order_by=date_heure+asc&limit=1
```

Le champ sélectionné et trié est bien `date_heure`, déclaré `datetime` dans les métadonnées du journal, et non une chaîne locale `heure`. Les dates UTC exactes de début et réception, codes HTTP et compteurs figurent au tableau 12.1. Les limites et premiers/derniers éléments effectivement retournés se résument ainsi ; les heures sont UTC et les dates de 2026.

| Requête | Filtre et tri | Limite / offset | `total_count` | Premier timestamp retourné | Dernier timestamp retourné |
| --- | --- | --- | ---: | --- | --- |
| Métadonnées | Aucun | Sans objet | Sans objet | Sans objet | Sans objet |
| Page 1, début 13:30:16.453130 le 6 novembre | `date_heure <= date'2026-11-06T13:30:16.187345+00:00'` ; `date_heure desc` | 96 / 0 | 4 500 | 17 octobre 18:45 | 16 octobre 19:00 |
| Page 2, début 13:30:18.103099 le 6 novembre | Même filtre ; `date_heure desc` | 96 / 96 | 5 500 | 27 octobre 05:45 | 26 octobre 06:00 |
| Ancienne, début 13:30:18.387466 le 6 novembre | Aucun filtre ; `date_heure asc` | 1 / absent, défaut 0 | 5 500 | 31 août 22:00 | 31 août 22:00 |

Le script construit une URL avec `urlencode`, puis fournit cette même chaîne à `urllib.request.Request`. Il n'inverse pas les pages ni les lignes dans le journal. La présence du tri dans l'URL et dans l'objet de requête est ainsi vérifiable côté client ; ce n'est pas une capture du traitement côté serveur ni une preuve que l'ordre global a été respecté.

### 13.2 Vérification de la syntaxe officielle

Source consultée : [Explore API v2.1 — référence officielle Opendatasoft/Huwise](https://help.opendatasoft.com/apis/ods-explore-v2/), rubriques « Query dataset records », « Order by clause », « Date literal », « IS NULL filter », `max()` et `count()`.

| Paramètre ou expression | Syntaxe documentée et application à cette étude |
| --- | --- |
| `order_by` | Champ suivi de `asc` ou `desc` ; `date_heure desc` est conforme. Le tri implicite est croissant |
| `where` | Expression ODSQL ; les littéraux `date'…'` acceptent l'ISO 8601. La borne avec offset explicite est conforme ; aucun filtre de publication n'est impliqué |
| Nulls | `consommation is not null` est un filtre documenté ; ajouter `consommation > 0` explicite le critère exploratoire de valeur positive |
| `limit` / `offset` | Sans regroupement : limite 100, `offset+limit < 10000` ; offset de départ 0. Les offsets 0 et 96 avec limite 96 respectent ces bornes |
| Contrôle indépendant | `max(date_heure)` et `count(*)` dans `select` permettent un maximum et un comptage, sans parcourir les pages |

La borne temporelle sélectionne des observations selon leur timestamp, pas des versions selon une date de publication. Elle ne fige pas les corrections ou insertions rétroactives. Aucune garantie de transaction entre requêtes successives n'a été trouvée dans les sections consultées. Ce constat ne désigne pas une cause de l'anomalie.

**Diagnostic :** formulation des paramètres correcte et encodage côté client vérifié ; chaque page est décroissante en interne. En revanche, le tri global et la pagination sur un état stable ne sont pas établis par les réponses. La séquence conservée est incompatible avec un tel état unique. Le changement de `total_count` pour le même filtre confirme une différence entre réponses, sans prouver qu'exactement 1 000 observations ont été ajoutées. La ligne ancienne et les métadonnées ne portent pas sur la même sélection que les pages filtrées. Cache, évolution du jeu, répliques ou traitement restent des hypothèses ; **la cause précise est indéterminée**.

### 13.3 Deux requêtes minimales préparées, non exécutées sur ODRÉ

Le module distinct [audit_latest.py](../experiments/faisabilite_application/audit_latest.py) est ajouté pour éviter une pagination dont la cohérence n'est pas démontrée. Le script initial est inchangé afin de préserver sa reproductibilité. Les champs nécessaires sont vérifiés dans les métadonnées déjà récupérées ; aucune nouvelle métadonnée distante n'est présumée identique sans limite.

Les deux requêtes GET utilisent `/api/explore/v2.1/catalog/datasets/eco2mix-national-tr/records`, sans offset et avec `limit=1`, `timezone=UTC`. La même borne est fixée au lancement ; leurs autres paramètres sont :

```text
where=consommation is not null and consommation > 0 and date_heure is not null and date_heure <= date'<borne UTC du lancement>'

Requête 1 :
select=date_heure,date,heure,consommation,nature,perimetre
order_by=date_heure desc

Requête 2 de contrôle :
select=max(date_heure) as last_timestamp,count(*) as eligible_count
```

La seconde ne dépend pas d'un offset ni du tri de la première. Elle doit fournir un maximum égal au timestamp de la première et un comptage égal à son `total_count`. Les schémas, valeurs finies positives, fuseaux et borne de non-futur sont contrôlés. L'âge de la ligne est calculé à la réception de la première réponse, jamais confondu avec la première publication.

Même en cas d'accord, la conclusion ne dépasserait pas une **concordance sur le sous-ensemble filtré et les deux états successifs consultés**. Ce n'est pas une certification absolue du dernier point de toute qualité, de l'absence de doublons contradictoires au maximum, ni d'une disponibilité stable. Si les réponses divergent, la dernière ligne retournée ne devient pas une dernière observation certifiée ; les deux réponses restent conservées pour examen. Une absence, un schéma invalide ou une erreur HTTP n'est pas un succès de fraîcheur.

La commande suivante a été exécutée localement uniquement en mode de préparation ; elle affiche `mode=plan_only`, sans réseau ni nouveau journal :

```powershell
.\.venv\Scripts\python.exe -m experiments.faisabilite_application.audit_latest
```

L'exécution réseau explicite doit être effectuée depuis un PowerShell Windows ordinaire à la racine du dépôt :

```powershell
.\.venv\Scripts\python.exe -m experiments.faisabilite_application.audit_latest --execute
```

Cette commande est préparée, **pas exécutée par Codex**. Elle limite l'audit à deux requêtes, ou une seule si la première échoue, et conserve un fichier distinct dans `experiments/faisabilite_application/runs/latest_<date UTC>_<suffixe>/audit_latest.json`, ignoré par Git. Le client existant assure délai, taille maximale et refus de redirection ; aucune dépendance ni configuration réseau n'est changée.

### 13.4 Conséquences scientifiques

Aucune nouvelle observation ni nouvelle mesure d'âge n'est disponible pendant cette préparation. Les valeurs et âges de la section 12 restent des propriétés des lignes conservées, pas une mesure certifiée du dernier point accessible. La disponibilité à 00:00 UTC et la compatibilité physique A/B restent non démontrées. Le verdict B est maintenu ; les résultats des deux requêtes devront être examinés avant toute nouvelle conclusion. Aucun modèle, variable prédictive ou composant d'application n'est créé.

Contrôles de ce complément : **79 tests réussis en 2,476 s**, dont 10 nouveaux tests synthétiques du module minimal ; contrôle documentaire sur **27 fichiers**, sans erreur ni avertissement ; `git diff --check` sans anomalie. Le mode de préparation a été exécuté et testé sans requête réseau ni écriture. Les nouveaux textes ont été contrôlés séparément pour les espaces finaux, les liens locaux et la syntaxe Python. Seuls les deux documents exploratoires sont modifiés et le module minimal avec son fichier de tests est ajouté ; les empreintes des **53 autres fichiers préexistants contrôlés** sont inchangées. Les journaux, le script initial et les Missions 010/011 sont préservés. Aucun ajout à l'index, commit ou push n'est réalisé.

## 14. Première concordance ponctuelle du contrôle minimal

Complément du 6 novembre 2026 : lecture hors ligne du journal `experiments/faisabilite_application/runs/latest_20261106T142426723229Z_e8635e9b/audit_latest.json`, produit dans le PowerShell Windows ordinaire selon les informations transmises. Son empreinte SHA-256 vérifiée est `3337086a7f15b4a52616f24bf695418a476e5c15a08876e8dc28923790d88552`. Aucun appel réseau ni nouveau journal d'acquisition n'est créé pendant cette lecture. Les observations et limites des sections précédentes sont conservées comme faits historiques.

### 14.1 Requêtes et données vérifiées

Les deux appels GET portent sur `https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/eco2mix-national-tr/records`. Les URL enregistrées ont été décodées et rapprochées des paramètres et du plan construit par le module existant. Les filtres sont identiques, la limite vaut 1, le fuseau UTC et aucun offset n'est envoyé.

```text
where=consommation is not null and consommation > 0 and date_heure is not null and date_heure <= date'2026-11-06T14:24:26.724201+00:00'
timezone=UTC
limit=1

Requête 1 :
select=date_heure,date,heure,consommation,nature,perimetre
order_by=date_heure desc

Requête 2 :
select=max(date_heure) as last_timestamp,count(*) as eligible_count
```

| Requête | Début UTC le 6 novembre 2026 | Réception UTC | HTTP | Lignes dans `results` |
| --- | --- | --- | ---: | ---: |
| Ligne triée décroissante | 14:24:26.724828 | 14:24:27.076782 | 200 | 1 observation |
| Maximum et comptage indépendants | 14:24:27.076864 | 14:24:27.428542 | 200 | 1 ligne agrégée |

Les erreurs enregistrées sont nulles ; les corps représentent 207 et 107 octets. Le champ générique `requests[].rows` reste nul dans ce module : les nombres de lignes ci-dessus sont obtenus directement par lecture des tableaux `responses[].results`, pas par assimilation aux compteurs du dataset.

L'observation conservée est :

| Champ | Valeur réellement lue |
| --- | --- |
| `date_heure` | `2026-11-06T14:00:00+00:00` |
| `date` / `heure` | `2026-11-06` / `15:00` |
| Conversion recalculée vers `Europe/Paris` | `2026-11-06T15:00:00+01:00`, cohérente avec les champs locaux |
| `consommation` | **59 358**, entier strictement positif et fini |
| Unité | **MW**, selon les métadonnées déjà conservées, non inférée de cette valeur |
| `nature` | `Données temps réel` |
| `perimetre` | `France` |

Aucun des six champs sélectionnés n'est nul. Cette absence de nulls concerne une seule observation, pas toute la couverture. Le statut temps réel n'est pas une garantie de valeur définitive ni une preuve de moyenne horaire ; aucun statut historique n'est fabriqué.

### 14.2 Concordance et âge

Le maximum indépendant vaut `2026-11-06T14:00:00+00:00`, identique au timestamp de la ligne triée. Le `total_count` de la première réponse est **6 397** ; le `eligible_count` agrégé est également **6 397**. Ces nombres décrivent le sous-ensemble satisfaisant le filtre, pas le nombre d'observations téléchargées. L'état enregistré `consistent_evidence` a été reproduit à l'identique avec la fonction de comparaison existante, sans nouvel accès à l'API.

L'âge a été recalculé à la réception de la **première** réponse :

```text
2026-11-06T14:24:27.076782+00:00 − 2026-11-06T14:00:00+00:00
= 1 467,076782 secondes
= 24 minutes 27,076782 secondes.
```

L'observation est antérieure à la borne fixée au lancement et à sa réception ; aucun point futur n'est utilisé. L'accord entre la ligne triée et le maximum constitue une preuve ponctuelle plus forte que les anciennes pages incohérentes : les deux réponses sont compatibles avec un dernier timestamp **du sous-ensemble filtré**, dans les états successivement consultés. Ce n'est pas une garantie transactionnelle, une preuve d'unicité sans variantes contradictoires à ce timestamp, ni un audit de toutes les qualités du jeu.

**L'accès ponctuel à une consommation récente est démontré par le journal. Le délai réel de publication ne l'est pas.** Le fichier ne renseigne pas la première apparition ni les révisions de cette observation. Les en-têtes HTTP `Date` sont présents et `Age` absent ; cela ne certifie pas l'absence d'un cache. Les 24 minutes 27 secondes sont l'âge du timestamp à réception, pas une mesure de latence de publication.

### 14.3 Interprétation et réserves maintenues

Le succès renforce la faisabilité technique d'une récupération légère depuis le contexte externe rapporté. Il n'est pas un nouveau succès réseau dans l'environnement Codex. Il montre que les valeurs anciennes du journal de 13:30 ne suffisent pas à décrire la fraîcheur générale de la source ; il ne prouve pas que leurs observations ont été corrigées ou que le mécanisme de leur incohérence a été identifié.

L'anomalie de pagination précédente demeure inexpliquée : ce nouvel audit évite les offsets et ne valide pas rétroactivement le tri inter-pages, les totaux ou la complétude de l'ancien échantillon. Le script initial et les journaux ne sont pas modifiés.

La consultation réussie a lieu à **14:24 UTC**, pas à 00:00 UTC. Une seule observation récente ne démontre ni une disponibilité quotidienne, ni la présence de toutes les consommations nécessaires aux retards, fenêtres glissantes et références de la Mission 011. Elle ne garantit pas non plus une continuité en cas de panne. Des répétitions manuelles à plusieurs horaires et dates, notamment autour de minuit, restent nécessaires, avec conservation de journaux distincts et vérification de fenêtres comparables.

La nature physique des points, l'agrégation et leur compatibilité avec les séries horaires A/B restent des questions distinctes. Aucun raccordement, moyenne de points, changement de convention, variable prédictive, modèle ou application n'est produit. Le protocole de Mission 011 est inchangé.

**Le verdict B est conservé** : la récupération d'une donnée récente est étayée ponctuellement, mais les conditions scientifiques et opérationnelles nécessaires à une application de prévisions actualisées ne sont pas toutes établies.

### 14.4 Contrôles de cette lecture

La comparaison enregistrée a été reproduite à l'identique ; l'âge, les paramètres décodés, l'absence de point futur et la conversion locale ont été vérifiés hors ligne. La suite complète retourne **79 tests réussis en 1,902 s**. Le contrôle documentaire examine **27 fichiers**, sans erreur ni avertissement ; `git diff --check` ne signale aucune anomalie. Les espaces finaux et les sept liens locaux du rapport ont aussi été contrôlés séparément.

Seul ce rapport est modifié et aucun nouveau fichier n'est créé. Les empreintes des **57 autres fichiers contrôlés** sont inchangées, notamment le journal examiné, les données, les scénarios A/B, les scripts, les tests et les Missions 010/011. Les fichiers exploratoires demeurent dans l'état Git non suivi constaté au début de cette lecture ; l'index est vide. Aucun appel réseau, ajout à l'index, commit ou push n'est effectué.

## 15. Conclusion

Une source officielle et une API documentée existent. Le contrôle minimal analysé en section 14 étaye ponctuellement l'accès à une consommation de 59 358 MW horodatée le 6 novembre 2026 à 14:00 UTC, avec concordance du maximum indépendant et un âge de 24 minutes 27,076782 secondes à réception. L'incohérence du journal paginé antérieur et les refus réseau historiques restent documentés et ne sont pas résolus rétroactivement. Aucune disponibilité quotidienne à 00:00 UTC ni compatibilité physique avec A/B n'est démontrée. Le délai réel de publication, les révisions et la continuité d'accès restent à établir ; aucune chaîne opérationnelle n'est validée.

**B — Faisabilité envisageable, mais conditionnelle**
