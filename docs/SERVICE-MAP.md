# Service map (endpoint to endpoint)

Every edge was observed: same trace id in the access log, the RPC log and the SQL log.

| Caller | Callee | Endpoint |
|---|---|---|
| `api-gateway` | `customer-svc` | `GET /api/customers/{id}` |
| `api-gateway` | `order-svc` | `GET /api/orders/{id}` |
| `api-gateway` | `order-svc` | `POST /api/orders` |
| `api-gateway` | `report-svc` | `GET /api/reports/top` |
| `order-svc` | `customer-svc` | `GET /api/customers/{id}` |
| `report-svc` | `customer-svc` | `GET /api/customers/{id}` |
| `report-svc` | `order-svc` | `GET /api/orders/{id}` |

```
api-gateway
  +-> customer-svc
  +-> order-svc
        +-> customer-svc
  +-> report-svc
        +-> customer-svc
        +-> order-svc
```

## Why this matters for change

An edge is a contract nobody wrote down. Touching `customer-svc` GET /api/customers/{id}
affects `api-gateway`, `report-svc` and `order-svc` — three callers, three test suites to re-run.
