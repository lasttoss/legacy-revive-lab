# Spans from the test run

Source: `samples/spans.log`, written by `SpanRecorder` during `mvn verify`. **40 spans**, **20 traces**, **5 distinct calls**.

These numbers come from a developer machine running the suite, so they describe *this* run, not
production. They are useful for shape and for verifying the maps — not for a latency SLO.

| Call | Runs | p50 | max |
|---|---|---|---|
| `GET /api/customers/{id}` | 7 | 5.3 ms | 324.0 ms |
| `GET /api/legacy/ping` | 1 | 4.6 ms | 4.6 ms |
| `GET /api/orders/{id}` | 6 | 4.5 ms | 12.7 ms |
| `GET /api/reports/top` | 3 | 3.9 ms | 30.2 ms |
| `POST /api/orders` | 3 | 8.0 ms | 52.1 ms |

## Trace by trace

| trace | calls | total |
|---|---|---|
| `06adaea7b18e9f4d` | GET /api/customers/{id} | 6 ms |
| `0a9a0ba5e050c4cd` | GET /api/reports/top | 60 ms |
| `161b72e94dabc395` | POST /api/orders | 12 ms |
| `2085b4fa9e244a8f` | GET /api/legacy/ping | 9 ms |
| `4881c288db6a5e10` | GET /api/orders/{id} | 8 ms |
| `48c0331c30b3ea52` | GET /api/customers/{id} | 10 ms |
| `4fbef2f5938f8f5b` | GET /api/orders/{id} | 8 ms |
| `56b3badda27ec3bc` | GET /api/reports/top | 7 ms |
| `56c3d1101a376b57` | GET /api/customers/{id} | 5 ms |
| `5d3916f36ed67a79` | GET /api/customers/{id} | 581 ms |
| `5db4e65c8cebbb26` | GET /api/orders/{id} | 8 ms |
| `877478263a0f6011` | POST /api/orders | 102 ms |
| `94986b80f80f45c4` | GET /api/customers/{id} | 10 ms |
| `a2f547249e048041` | POST /api/orders | 14 ms |
| `ada63764abfe6936` | GET /api/orders/{id} | 25 ms |
| `c964415d771aebbb` | GET /api/reports/top | 7 ms |
| `c9909dcc1c47c346` | GET /api/customers/{id} | 10 ms |
| `d6839a0def5a1e93` | GET /api/orders/{id} | 7 ms |
| `e032248cefe80d1a` | GET /api/customers/{id} | 12 ms |
| `fd8ee837465e17f2` | GET /api/orders/{id} | 8 ms |

## Agreement with the maps

- every documented endpoint executed, and nothing undocumented executed.
