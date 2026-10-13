# Journal de bord - TP01

## Q1. Délai de changement
Entre le premier commit et sa fusion sur main, il s'est écoulé environ 10 minutes.

## Ce qui a pris le plus de temps
La configuration initiale (clés SSH) et la résolution du conflit.

## Q2. Dépendance à GitHub
Ce qui fonctionnerait à l'identique sur GitLab ou Gitea : Toutes les commandes `git` natives (commit, switch, rebase, tag, push), l'utilisation de Docker, les tests avec `pytest`, et le formatage avec `pre-commit`.
Ce qui changerait : L'utilisation de l'outil `gh` (il faudrait utiliser `glab` pour GitLab par exemple), ainsi que l'interface de création et de fusion des Pull Requests.

## Q3. Intérêt de la signature des commits
Signer les commits permet de garantir l'identité de l'auteur de façon cryptographique et décentralisée. Si un collègue pousse nos commit depuis son poste, ou si le dépôt entier est un jour migré de GitHub vers GitLab, ma signature prouvera toujours que je suis l'auteur original de ce code, indépendamment de la plateforme.

# Journal de bord - TP02

## Rôles
- A (@ArmorialOfficiel, admin du dépôt) : ruleset sur `main` et CODEOWNERS.
- B (@AliKKarapetian) : Dependabot et gitleaks.

## Étape 1 - Ruleset sur main
Ruleset « main » (versionné dans `.github/rulesets/main.json`) : suppression et force push bloqués,
PR obligatoire avec 1 approbation, « dismiss stale approvals », revue des Code Owners,
historique linéaire, commits signés, fusion par squash uniquement. Le contrôle requis « test » sera ajouté au TP03.

Tests de refus (ruleset actif) :

- **Push direct sur `main`** (commit `chore: test de protection`) : refusé par le serveur.
  ```
  remote: error: GH013: Repository rule violations found for refs/heads/main.
  remote: - Changes must be made through a pull request.
   ! [remote rejected] main -> main (push declined due to repository rule violations)
  ```
  Le commit local a ensuite été annulé.
- **Commit non signé dans une PR** (`git -c commit.gpgsign=false commit --allow-empty`, PR #24) :
  le bouton « Squash and merge » est grisé, GitHub affiche « Merging is blocked » avec
  « At least 1 approving review is required » et « Commits must have verified signatures ».
  La PR a été fermée et la branche `test/non-signe` supprimée.

**Pourquoi « dismiss stale approvals » ?** Une approbation porte sur un diff précis. Sans cette option,
on peut faire approuver une PR anodine puis pousser un nouveau commit (bug, porte dérobée, secret)
et fusionner sans que personne ne l'ait relu. L'option annule l'approbation à chaque nouveau push.

## Étape 2 - CODEOWNERS
A possède `.github/` et `infra/`, B possède `app/` et `monitoring/`, les deux possèdent `docs/` et le reste.

**Propriétaire seul et absent ?** La PR est bloquée : personne d'autre ne peut donner la revue requise.
Il faut toujours au moins deux propriétaires par chemin sensible (ou une équipe GitHub plutôt
qu'une personne), et une procédure d'urgence écrite (qui peut contourner le ruleset, et comment c'est tracé).

## Étape 3 - Dependabot
`.github/dependabot.yml` : pip, github-actions et docker, hebdomadaire, préfixe `chore(deps)`.
`fastapi` est volontairement épinglé une version en retard dans `pyproject.toml` : la première PR
Dependabot devrait le mettre à jour.

**Qui approuve une PR Dependabot ?** Un membre du binôme, comme n'importe quelle PR : le ruleset
ne fait pas d'exception pour les robots. C'est une bonne chose, car une mise à jour de dépendance
peut casser l'application ou introduire du code malveillant (attaque de la chaîne d'approvisionnement) :
un humain relit le changelog et vérifie que les tests passent.

## Étape 4 - gitleaks en pre-commit
Hook `gitleaks` ajouté à `.pre-commit-config.yaml` (gitleaks 8.30). Test avec une ligne
`AWS_SECRET_ACCESS_KEY = "<40 caractères aléatoires>"` dans `app/config.py` : commit refusé.

```
Detect hardcoded secrets.....Failed
Finding:     AWS_SECRET_ACCESS_KEY = "REDACTED"
RuleID:      generic-api-key
Entropy:     4.90
File:        app/config.py
Line:        9
leaks found: 1
```

**Nom de la variable ou valeur ?** Les deux à la fois. En renommant la variable en `MA_VARIABLE`
avec la même valeur, le commit passe : la règle `generic-api-key` exige un mot-clé
(key, secret, token…) près de la valeur *et* une entropie élevée. Une valeur seule n'est détectée
que si elle a un format reconnaissable (ex. `AKIA…` pour un identifiant AWS, `ghp_…` pour GitHub).

## Étape 5 - Secret historique
Notre dépôt n'a pas été créé depuis le dépôt modèle (`--template`) : le faux jeton du formateur
n'y était pas (`gitleaks git .` : no leaks found sur 14 commits). Nous avons donc **simulé le scénario** :
un faux jeton `API_TOKEN` dans `app/old_settings.py`, commité en contournant le hook
(`SKIP=gitleaks git commit`, comme un collègue sans pre-commit) puis fusionné sur main (PR #27).

`gitleaks git --verbose --redact .` sur tout l'historique (26 commits) : **1 fuite trouvée**.

| Champ    | Valeur |
|----------|--------|
| Commit   | `091a0dffb2782a7ab2d563c4657d76af39bad051` (PR #27) |
| Auteur   | Alik Karapetian |
| Date     | 2026-10-13 09:05:41 UTC |
| Fichier  | `app/old_settings.py`, ligne 2 |
| Règle    | `generic-api-key` (entropie 4.86) |

Le fichier est supprimé (PR de rotation) et l'empreinte du commit historique est ajoutée à
`.gitleaksignore` : `gitleaks git . --report-path docs/gitleaks.json` renvoie le code 0.
Nous n'avons pas réécrit l'historique (`git filter-repo`) : le jeton est faux, et réécrire `main`
obligerait les deux membres à recloner ; la rotation suffit.

**Rotation :** un secret poussé sur une forge doit être considéré comme compromis, qu'on réécrive
l'historique ou non (des clones et des robots l'ont peut-être déjà récupéré). Avec un vrai jeton,
on l'aurait d'abord **révoqué côté fournisseur** et remplacé par un nouveau stocké hors du dépôt
(variable d'environnement, gestionnaire de secrets), puis supprimé le fichier par une PR.
Réécrire l'historique (`git filter-repo`) ne suffit pas et oblige tous les collaborateurs à recloner.

## Questions d'observation
**Q1. Quelles règles auraient empêché le secret d'arriver sur main ?**
- Automatiques : gitleaks en pre-commit (sur le poste) et gitleaks comme contrôle requis dans la CI,
  le push protection de GitHub Secret Scanning.
- Humaines : la revue obligatoire (et CODEOWNERS).
- La plus fiable : le contrôle automatique requis côté serveur (CI + ruleset), car il ne dépend
  ni de l'installation locale ni de l'attention du relecteur.

**Q2. gitleaks en pre-commit protège-t-il un collègue qui ne l'a pas installé ?**
Non : pre-commit est local et contournable (`git commit --no-verify`). Il faut lancer gitleaks dans
le pipeline (GitHub Actions) et en faire un contrôle requis du ruleset.

**Q3. Combien de temps un secret poussé reste-t-il privé ?**
Quelques secondes à quelques minutes : des robots surveillent en continu le flux public de GitHub.
GitHub Secret Scanning signale automatiquement les jetons aux fournisseurs partenaires,
qui peuvent les révoquer (ex. jetons GitHub `ghp_…`, clés AWS, Slack, Stripe, Azure, Google Cloud).

## Ce qui a pris le plus de temps
Comprendre Git et son environnement (commit, push, fusion) n'est pas simple. Ce qui nous a pris le plus de temps, c'est la fusion.

# Journal de bord - TP03

## Étape 1 - ci.yml minimal (PR #29)
Workflow `.github/workflows/ci.yml` déclenché sur `push` (main) et `pull_request`, permissions
`contents: read`, actions épinglées par tag majeur (`checkout@v5`, `setup-python@v6`) :
`pip install -e ".[dev]"`, `ruff check`, `ruff format --check`, `pytest`. Premier job vert en 23 s.

**Pourquoi le workflow se déclenche-t-il sur la PR alors que main ne contient pas ci.yml ?**
Pour l'événement `pull_request`, GitHub exécute le workflow présent dans le commit de fusion
de la PR (branche de la PR fusionnée avec main), donc celui de la branche, pas celui de main.

## Étape 2 - Couverture en artefact et pre-commit en CI (PR #30)
`pytest --cov=app --cov-report=xml --cov-report=html`, `htmlcov/` publié avec
`actions/upload-artifact@v4` (`name: coverage-py…`, `retention-days: 7`), et
`pre-commit run --all-files` pour appliquer ruff et gitleaks même à qui a sauté le hook.

**Fichier le moins couvert :** aucun, `app/config.py` et `app/main.py` sont couverts à 100 %.

**Faut-il échouer sous un seuil ?** Oui (`--cov-fail-under=80` par exemple) pour empêcher la
couverture de baisser. Pas 100 % : on finit par écrire des tests qui exécutent le code sans rien
vérifier, et certaines branches (erreurs réseau, cas improbables) coûtent cher à tester pour peu de valeur.

## Étape 3 - Matrice 3.12 / 3.13 et cache pip (PR #31)
`strategy.matrix.python: ["3.12", "3.13"]` avec `fail-fast: false`, jobs nommés
`test (py3.12)` / `test (py3.13)`, cache `pip` de setup-python. La clé du cache est calculée sur
`pyproject.toml` (`cache-dependency-path`), car le dépôt n'a pas de `requirements.txt` :
`setup-python-Linux-x64-24.04-Ubuntu-python-3.13.16-pip-<empreinte de pyproject.toml>`.

| Exécution                      | test (py3.12) | test (py3.13) | pip install | pre-commit |
|--------------------------------|---------------|---------------|-------------|------------|
| Avant matrice (1 job, sans cache) | -          | 1 min 11 s    | 19 s        | 43 s       |
| Matrice, cache miss            | 55 s          | 52 s          | 9 à 12 s    | 30 à 35 s  |
| Matrice, cache hit (rerun 1)   | 51 s          | 59 s          | 7 à 8 s     | 34 à 39 s  |
| Matrice, cache hit (rerun 2)   | 58 s          | 42 s          | 5 à 8 s     | 27 à 38 s  |

Le journal de setup-python affiche « Cache restored from key » aux relances.

**Combien de checks sur la PR ?** Deux, un par entrée de la matrice : `test (py3.12)` et
`test (py3.13)`. Ce sont ces deux noms exacts qu'il faut exiger (le nom `test` n'existe plus).

## Étape 4 - Contrôle requis et test cassé (PR #32, #33)
Contrôles requis ajoutés au ruleset `main` : **`test (py3.12)`** et **`test (py3.13)`**
(source GitHub Actions, versionnés dans `.github/rulesets/main.json`). Seul l'admin du dépôt
peut modifier le ruleset (`gh api -X PUT …/rulesets/<id>` renvoie 404 pour un membre en écriture).

PR #33 : `X-Visites-Version` passé à `0.2.0` dans `app/main.py`. Les deux checks sont rouges,
la fusion est bloquée (« Required statuses must pass ») :
```
>       assert resp.headers["X-Visites-Version"] == "0.1.0"
E       AssertionError: assert '0.2.0' == '0.1.0'
FAILED tests/test_api.py::test_root_expose_version_header
```
Un commit correctif (retour à `0.1.0`) fait repasser les deux checks au vert, la PR est
débloquée puis fusionnée. Les deux exécutions restent visibles dans l'historique de la PR.

**Et si un administrateur coche « bypass » ?** Il peut fusionner une PR rouge. Ce droit doit être
réservé à un ou deux admins pour les urgences ; chaque contournement est tracé dans
*Settings → Rules → Insights* (qui, quand, quelle règle).

## Étape 5 - act en local
act **0.2.89** (version épinglée, pas la dernière), image `catthehacker/ubuntu:act-latest` (Medium).
`~/.actrc` :
```
-P ubuntu-latest=catthehacker/ubuntu:act-latest
--container-architecture linux/amd64
```
`act -l` liste le job `test`. `act pull_request --matrix python:3.13` : 3 min 23 s.

| Étape                  | Résultat local | Durée   |
|------------------------|----------------|---------|
| checkout, setup-python | OK             | 30 s    |
| pip install            | OK             | 33 s    |
| ruff check / format    | OK             | < 1 s   |
| pre-commit             | OK             | 1 min 13 s |
| pytest + couverture    | OK             | 2 s     |
| upload-artifact        | **échec**      | < 1 s   |

**Identique à GitHub :** les mêmes étapes, les mêmes commandes, le même résultat ruff, pre-commit et pytest.

**Ce qui échoue et pourquoi :**
- `upload-artifact` : `Unable to get the ACTIONS_RUNTIME_TOKEN env variable`. Ce jeton et le service
  d'artefacts sont fournis par l'infrastructure GitHub, pas par le conteneur (act propose
  `--artifact-server-path` pour simuler un serveur d'artefacts local).
- Cache : `pip cache is not found`, `cache-hit=false` ; le service de cache de GitHub n'existe pas en local,
  chaque exécution repart de zéro.
- Plus lent qu'en ligne : premier téléchargement de Python et des hooks pre-commit dans le conteneur.

**act remplace-t-il GitHub Actions pour valider une PR ?** Non : seul le check exécuté par GitHub
est requis par le ruleset et fait foi. act sert à mettre au point un workflow sans pousser
une série de commits « fix ci », et devient indispensable quand le pipeline se complique (TP07).

## Étape 6 - Badge
Badge `CI` en tête du README, sur `main`.

## Questions d'observation
**Q1. Durée du pipeline, ce qui prend le plus de temps, effet du cache ?**
Environ 50 s à 1 min par job, les deux jobs en parallèle. Le plus long est `pre-commit`
(30 à 40 s : installation des environnements des hooks, dont gitleaks), puis `pip install`.
Le cache pip fait gagner environ 3 à 5 s sur l'installation : peu, car nos dépendances sont légères ;
la variabilité des runners GitHub est du même ordre. On reste très loin de la limite de 5 minutes.

**Q2. Qu'est-ce qui empêche un membre de contourner le pipeline ?**
Le ruleset : PR obligatoire, contrôles `test (py3.12)` et `test (py3.13)` requis, force push bloqué,
pas d'acteur de bypass. Sans ruleset, le pipeline n'est qu'un avis.

**Q3. Quelles lignes changer pour GitLab CI ou Gitea Actions ?**
Gitea Actions : presque rien, le fichier va dans `.gitea/workflows/` (syntaxe compatible).
GitLab CI : tout le fichier (`.gitlab-ci.yml` avec `stages`, `image: python:3.13`, `script:`,
`parallel: matrix`, `cache:`, `artifacts:`), mais les mêmes concepts.
