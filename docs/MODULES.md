# Services in this repository

Discovered by `kit/discover.py` under `legacy-revive-lab`: **1 Spring service(s)**, **5 endpoints**.

Discovery reads source text only: no build, no run, no database. That is why it works on a
repository nobody prepared for it.

| Service | Path | Controllers | Endpoints | Entities | Tables | Test files |
|---|---|---|---|---|---|---|
| `legacy-svc` | `legacy-app` | 1 | 5 | 3 | `customers`, `order_items`, `orders` | 4 |

## Tables owned by more than one service

- none: every table has exactly one owner

## Endpoints per service

### `legacy-svc`
- `GET /api/customers/{id}` — legacy-app/src/main/java/com/example/legacy/web/LegacyController.java
- `GET /api/orders/{id}` — legacy-app/src/main/java/com/example/legacy/web/LegacyController.java
- `POST /api/orders` — legacy-app/src/main/java/com/example/legacy/web/LegacyController.java
- `GET /api/reports/top` — legacy-app/src/main/java/com/example/legacy/web/LegacyController.java
- `GET /api/legacy/ping` — legacy-app/src/main/java/com/example/legacy/web/LegacyController.java
