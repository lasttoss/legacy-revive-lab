# System map — multi-service

Services: 3 · calls in sample: 7 · trace ids: 5

## Services

- `api-gateway` — 2 endpoints, tables none, 0 test file(s)
- `customer-svc` — 2 endpoints, tables customers, 0 test file(s)
- `order-svc` — 2 endpoints, tables orders, 0 test file(s)

## Endpoint to table

- `GET /api/customers` → customers (SELECT 1, UPDATE 1)
- `GET /api/customers/{id}` → customers (SELECT 4)
- `GET /api/orders/by-customer/{id}` → orders (SELECT 1)
- `GET /api/orders/{id}` → orders (SELECT 1)
- `POST /api/orders` → orders (INSERT 1, SELECT 1)

## Call edges

- `api-gateway` → `customer-svc` — 2 call(s): /api/customers, /api/customers/{id}
- `api-gateway` → `order-svc` — 2 call(s): /api/orders, /api/orders/{id}
- `customer-svc` → `order-svc` — 1 call(s): /api/orders/by-customer/{id}
- `order-svc` → `customer-svc` — 2 call(s): /api/customers/{id}
