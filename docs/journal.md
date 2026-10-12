# Journal de bord - TP01

## Q1. Délai de changement
Le temps écoulé entre mon premier commit et sa fusion sur main a été de quelques heures pour cette première fois. L'étape qui m'a pris le plus de temps a été la configuration initiale (clés SSH) et la résolution du conflit.

## Q2. Dépendance à GitHub
Ce qui fonctionnerait à l'identique sur GitLab ou Gitea : Toutes les commandes `git` natives (commit, switch, rebase, tag, push), l'utilisation de Docker, les tests avec `pytest`, et le formatage avec `pre-commit`.
Ce qui changerait : L'utilisation de l'outil `gh` (il faudrait utiliser `glab` pour GitLab par exemple), ainsi que l'interface de création et de fusion des Pull Requests.

## Q3. Intérêt de la signature des commits
Signer les commits permet de garantir l'identité de l'auteur de façon cryptographique et décentralisée. Si un collègue pousse nos commit depuis son poste, ou si le dépôt entier est un jour migré de GitHub vers GitLab, ma signature prouvera toujours que je suis l'auteur original de ce code, indépendamment de la plateforme.
