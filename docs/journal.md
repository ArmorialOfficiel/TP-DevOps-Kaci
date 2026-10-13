# Journal de bord - TP01

## Q1. Délai de changement
Le temps écoulé entre mon premier commit et sa fusion sur main a été de quelques heures pour cette première fois. L'étape qui m'a pris le plus de temps a été la configuration initiale (clés SSH) et la résolution du conflit.

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
`gitleaks git --verbose --redact .` sur tout l'historique : **no leaks found** (14 commits).
Notre dépôt n'a pas été créé depuis le dépôt modèle (`--template`) : le fichier
`app/old_settings.py` contenant le faux jeton du formateur n'est donc pas dans notre historique.
*À compléter si le formateur fournit le dépôt modèle : commit, auteur, date, fichier.*

Rapport : `docs/gitleaks.json` (vide, code de retour 0). `.gitleaksignore` est en place, sans empreinte.

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
*À compléter.*
