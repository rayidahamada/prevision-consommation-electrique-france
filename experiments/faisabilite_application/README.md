# Audit ponctuel de la source éCO2mix

Étude exploratoire facultative, indépendante de la Mission 012 scientifique. Le [rapport de faisabilité](../../reports/exploration_faisabilite_application.md) distingue documentation, test réseau réel et cas synthétiques. Aucune application ni prévision n'est produite.

## Exécution manuelle

Depuis la racine du dépôt, avec l'environnement existant :

```powershell
.\.venv\Scripts\python.exe experiments/faisabilite_application/inspect_eco2mix_api.py
```

Bibliothèque standard uniquement, aucune installation nécessaire. Chaque lancement crée un dossier neuf dans `experiments/faisabilite_application/runs/`, identifié par date UTC et suffixe aléatoire. Le fichier `audit.json` conserve les paramètres, URL, heures UTC de début et de fin des requêtes, codes HTTP ou erreurs, empreinte des réponses réussies, métadonnées sélectionnées et un petit échantillon de champs publics. Les données du projet ne sont jamais utilisées comme sortie. Les audits antérieurs ne sont pas remplacés.

Le script vérifie d'abord le schéma ; un échec empêche les appels d'observations. Au maximum : une requête de métadonnées, deux pages de 96 lignes récentes et une ligne ancienne, soit quatre requêtes et 193 observations. Paramètres possibles : `--pages` de 1 à 2, `--page-size` de 1 à 100, `--timeout` de 1 à 30 secondes, et `--output-dir`. Aucune authentification, relance automatique ou redirection suivie. Chaque réponse est limitée à 1 Mio. Le délai s'applique aux opérations socket et un budget de lecture est contrôlé entre blocs ; ce n'est pas une garantie absolue de durée totale face à un serveur qui transmet très lentement dans un même bloc.

Le script utilise Explore API v2.1 et `timezone=UTC`. Les pages récentes sont filtrées par une borne supérieure fixée au lancement, triées par `date_heure desc`, puis paginées par `limit`/`offset`. Cette borne évite les ajouts postérieurs à l'heure d'audit ; elle ne rend pas les pages transactionnelles si des données anciennes sont insérées ou corrigées pendant l'appel. Les doublons sont signalés, sans résolution automatique. Les dates futures sont exclues de la sélection récente ; l'audit ne mesure donc pas leur présence dans le dataset entier.

La « dernière valeur utilisable » est ici une valeur positive finie, horodatée avant réception et unique dans l'échantillon. Ce filtre exploratoire n'est pas une preuve de qualité ou de nature physique. Les valeurs nulles, non numériques, non positives, futures ou dupliquées restent diagnostiquées. Le calendrier source est comparé à une date ISO et une heure locale `HH:MM` : un autre format est une discordance descriptive, pas une correction. Le champ `nature` est conservé sans conversion vers les statuts historiques.

Codes de sortie : `0` pour un échantillon récupéré sans erreur technique, `1` pour un audit incomplet ou vide, `2` pour des paramètres ou une sortie invalides. Même le code `0` ne démontre ni fraîcheur suffisante ni compatibilité avec l'historique. Un succès HTTP suivi d'un schéma invalide reste une erreur d'audit.

## Répétitions et tests

Répéter manuellement la commande à plusieurs heures, notamment autour de 00:00 UTC et des transitions saisonnières, pour conserver des observations de disponibilité distinctes. Aucun service ni planification n'est créé. Ne pas lancer de boucle rapide : le portail annonce un rafraîchissement au quart d'heure et un quota ; consulter le rapport avant une campagne. Une répétition ne permet d'encadrer une première publication que si l'absence puis la présence d'une même observation ont réellement été contrôlées dans une plage de requête comparable, sans trou de couverture ni erreur.

Les sorties `runs/` sont ignorées par le `.gitignore` propre à cette expérience ; elles ne rejoignent pas `data/raw/` et ne sont pas proposées pour publication. Leur conservation locale permet d'étudier ultérieurement les versions et les premières apparitions, sans assimilation à un instantané historique officiel.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_inspect_eco2mix_api.py -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe scripts/check_documentation.py --include-untracked
```

Les nouveaux tests fonctionnent sans réseau et utilisent uniquement des cas synthétiques. Ils ne prouvent pas l'accès effectif à ODRÉ.

## Diagnostic réseau et premier audit de fraîcheur

Complément du 6 novembre 2026 : depuis le terminal d'exécution Codex, le DNS répond, mais TCP 443 et HTTPS échouent avec un refus de socket. Aucun nouvel échantillon n'est récupéré ; la cause exacte reste indéterminée. Les constats et horaires sont conservés dans le [complément du rapport](../../reports/exploration_faisabilite_application.md#11-diagnostic-réseau-et-premier-audit-de-fraîcheur).

Pour comparer avec un PowerShell Windows ordinaire, ouvrir un terminal sans privilège administrateur à la racine du projet et exécuter :

```powershell
Get-Location
$PSVersionTable.PSVersion
.\.venv\Scripts\python.exe -c "import sys,pathlib,urllib.request; print('Python:',sys.version.split()[0]); print('Interpreteur .venv attendu:',pathlib.Path(sys.executable).resolve()==(pathlib.Path.cwd()/'.venv/Scripts/python.exe').resolve()); print('Schemas proxy detectes:',sorted(urllib.request.getproxies()))"
Resolve-DnsName odre.opendatasoft.com -DnsOnly
Test-NetConnection odre.opendatasoft.com -Port 443 -InformationLevel Quiet
$apiUri = 'https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/eco2mix-national-tr'
[DateTime]::UtcNow.ToString('o')
try {
    $response = Invoke-WebRequest -UseBasicParsing -Uri $apiUri -Method Get -TimeoutSec 15 -ErrorAction Stop
    Write-Output ('HTTP ' + [int]$response.StatusCode)
    if ([int]$response.StatusCode -eq 200) {
        .\.venv\Scripts\python.exe experiments/faisabilite_application/inspect_eco2mix_api.py
    }
} catch {
    $diagnosticError = $_.Exception
    while ($null -ne $diagnosticError) {
        Write-Output ($diagnosticError.GetType().FullName + ': ' + $diagnosticError.Message)
        $diagnosticError = $diagnosticError.InnerException
    }
}
[DateTime]::UtcNow.ToString('o')
```

La vérification HTTPS préalable ajoute une requête de métadonnées au maximum de quatre appels du script. Si elle échoue, aucun appel du script n'est lancé. Ne pas multiplier les tentatives en cas de refus. Les erreurs sont examinées séparément aux niveaux DNS, TCP, TLS/proxy et HTTP ; une réponse HTTP 200 seule ne garantit pas une consommation exploitable.

Le chemin affiché par `Get-Location` reste local ; masquer les éléments personnels avant tout partage. Ne partager aucune valeur de proxy, aucun identifiant ni en-tête de session. Le script affiche le chemin relatif de son journal horodaté et les résultats des requêtes. Conserver ce journal, puis examiner `metadata`, `requests`, `pages` et, s'il existe, `combined_sample_audit`. Une réussite permet une première mesure d'âge, pas une preuve de régularité ou de compatibilité avec A/B.

Après vérification du premier audit réussi, les répétitions manuelles décrites plus haut devront couvrir plusieurs moments et notamment minuit UTC ; aucune tâche planifiée n'est nécessaire à ce stade.

## Contrôle minimal du tri et du maximum temporel

L'analyse du journal du 6 novembre 2026 révèle un ordre incohérent entre pages malgré un paramètre de tri conforme. Le script initial est conservé pour la reproductibilité de cette exécution. Le nouveau module `audit_latest.py` évite la pagination : une requête demande une consommation non nulle et positive, avec timestamp non nul, tri décroissant et `limit=1` ; une seconde calcule indépendamment le maximum temporel et le nombre d'observations éligibles sur le même filtre. Les deux appliquent une borne UTC fixée au lancement et ne contiennent aucun offset.

Depuis la racine, afficher le plan **sans réseau ni fichier créé** :

```powershell
.\.venv\Scripts\python.exe -m experiments.faisabilite_application.audit_latest
```

Dans le PowerShell Windows ordinaire, lancer explicitement les deux requêtes préparées :

```powershell
.\.venv\Scripts\python.exe -m experiments.faisabilite_application.audit_latest --execute
```

Cette dernière commande n'a pas été exécutée dans l'environnement Codex pendant la préparation. Aucun test réseau supplémentaire n'est annoncé. Le module réutilise le client borné existant : 15 secondes par requête par défaut, 1 Mio maximum par réponse, aucune authentification, redirection suivie ou relance. `--timeout` autorise 1 à 30 secondes. `--output-dir` permet une sortie distincte hors des données du projet.

Chaque exécution explicite conserve un nouveau `runs/latest_<date UTC>_<suffixe>/audit_latest.json`, avec URL et paramètres, dates de requête et réception, code HTTP, réponses JSON bornées, empreintes de leurs corps et comparaison. Si le premier appel échoue, le second n'est pas lancé. Aucun journal existant n'est remplacé et les sorties restent ignorées par Git.

L'état `consistent_evidence` exige une consommation positive finie, une date non future respectant la borne, un timestamp égal au maximum agrégé et un total filtré égal au comptage agrégé. Ce résultat reste une concordance entre deux réponses successives, sans transaction garantie, sans vérification des doublons au maximum et sans mesure de première publication. Une divergence donne `inconsistent`, une absence cohérente `empty`, une erreur `incomplete` ; ces états ne sont pas des succès de fraîcheur. Le code de sortie vaut 0 pour `consistent_evidence`, 1 pour les autres résultats d'audit et 2 pour des arguments ou une sortie invalides.

L'âge est calculé à la réception de la première réponse ; il est conservé comme âge de la ligne retournée même en cas de divergence avec le maximum, sans la certifier dernière observation du jeu. Aucune agrégation de puissance ni comparaison A/B n'est effectuée. Après exécution dans le terminal ordinaire, conserver le journal et examiner les deux réponses avant toute conclusion.
