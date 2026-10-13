# Compteur de Visites

[![CI](https://github.com/ArmorialOfficiel/TP-DevOps-Kaci/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/ArmorialOfficiel/TP-DevOps-Kaci/actions/workflows/ci.yml)

API FastAPI qui compte les visites dans Redis et expose des métriques Prometheus.
Dépôt fil rouge du module « Introduction au DevOps ».

## Endpoints

| Méthode | Chemin     | Rôle                                                             |
|---------|------------|------------------------------------------------------------------|
| GET     | `/`        | Incrémente le compteur et renvoie `{"visites": n}` ; en-tête `X-Visites-Version` |
| POST    | `/reset`   | Remet le compteur à zéro et renvoie `{"visites": 0}`             |
| GET     | `/health`  | `{"status": "ok"}`, ou 503 si Redis est injoignable              |
| GET     | `/metrics` | Métriques Prometheus (requêtes, latence)                         |

## Lancer en local

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
docker run -d --name redis -p 6379:6379 redis:8-alpine
uvicorn app.main:app --reload
curl -s localhost:8000/
```

L'adresse de Redis se règle avec la variable `REDIS_URL` (défaut : `redis://localhost:6379`).

## Tests et qualité

```bash
pytest -q                    # tests unitaires (Redis simulé avec fakeredis)
pytest -q -m integration     # tests d'intégration (Redis réel requis)
pre-commit install
pre-commit run --all-files   # hooks de base + ruff
```

## Contribuer

Voir [CONTRIBUTING.md](CONTRIBUTING.md). Journal de bord : [docs/journal.md](docs/journal.md).
