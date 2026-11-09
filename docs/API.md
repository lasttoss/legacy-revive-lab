# API reference (generated from recordings)

Source: `samples/golden/` — 20 recorded requests, 11 distinct calls.
Every example below is a real response the service produced, captured by the recorder.

## `GET /api/customers/1`

- statuses seen: 200
- recordings: 3

Response (one recorded example):
```json
{
  "id": 1,
  "name": "Alice",
  "email": "alice@example.com",
  "tier": "GOLD",
  "orders": [
    {
      "id": 1001,
      "customerId": 1,
      "status": "PAID",
      "total": 250,
      "fee": 17.5,
      "createdAt": "2024-01-05T10:00:00",
      "items": []
    },
    {
      "id": 1001,
      "customerId": 1,
      "status": "PAID",
      "total": 250,
      "fee": 17.5,
      "createdAt": "2024-01-05T10:00:00",
      "items": []
    },
    {
      "id": 1002,
      "customerId": 1,
      "status": "OPEN",
      "total": 40,
      "fee": 0,
      "createdAt": "2024-02-06T11:30:00",
      "items": []
    }
  ]
}
```

## `GET /api/customers/2`

- statuses seen: 200
- recordings: 1

Response (one recorded example):
```json
{
  "id": 2,
  "name": "Bob",
  "email": "bob@example.com",
  "tier": "SILVER",
  "orders": [
    {
      "id": 1003,
      "customerId": 2,
      "status": "CANCELLED",
      "total": 900,
      "fee": 63,
      "createdAt": "2024-02-07T09:15:00",
      "items": []
    }
  ]
}
```

## `GET /api/customers/3`

- statuses seen: 200
- recordings: 1

Response (one recorded example):
```json
{
  "id": 3,
  "name": "Carol",
  "email": "carol@example.com",
  "tier": null,
  "orders": []
}
```

## `GET /api/customers/999`

- statuses seen: 200
- recordings: 2

Response (one recorded example):
```json
null
```

## `GET /api/legacy/ping`

- statuses seen: 200
- recordings: 1

Response (one recorded example):
```json
{
  "ok": true
}
```

## `GET /api/orders/1001`

- statuses seen: 200
- recordings: 2

Response (one recorded example):
```json
{
  "id": 1001,
  "customerId": 1,
  "status": "PAID",
  "total": 250,
  "fee": 17.5,
  "createdAt": "2024-01-05T10:00:00",
  "items": []
}
```

## `GET /api/orders/1002`

- statuses seen: 200
- recordings: 1

Response (one recorded example):
```json
{
  "id": 1002,
  "customerId": 1,
  "status": "OPEN",
  "total": 40,
  "fee": 0,
  "createdAt": "2024-02-06T11:30:00",
  "items": []
}
```

## `GET /api/orders/1003`

- statuses seen: 200
- recordings: 2

Response (one recorded example):
```json
{
  "id": 1003,
  "customerId": 2,
  "status": "CANCELLED",
  "total": 900,
  "fee": 63,
  "createdAt": "2024-02-07T09:15:00",
  "items": []
}
```

## `GET /api/orders/999999`

- statuses seen: 200
- recordings: 1

Response (one recorded example):
```json
null
```

## `GET /api/reports/top?limit=3`

- statuses seen: 200
- recordings: 3

Response (one recorded example):
```json
[
  {
    "id": 2,
    "name": "Bob",
    "spent": 900,
    "orders": 1
  },
  {
    "id": 1,
    "name": "Alice",
    "spent": 290,
    "orders": 2
  }
]
```

## `POST /api/orders`

- statuses seen: 200
- recordings: 3

Request body (one recorded example):
```json
{
  "customerId": 1,
  "items": [
    {
      "sku": "SKU-A",
      "qty": 2,
      "price": 100.0
    },
    {
      "sku": "SKU-B",
      "qty": 1,
      "price": 50.0
    }
  ]
}
```

Response (one recorded example):
```json
{
  "id": 1794235787620,
  "customerId": 1,
  "status": "OPEN",
  "total": 250.0,
  "fee": 17.5,
  "createdAt": "2026-11-09T14:49:47.622",
  "items": [
    {
      "id": 5,
      "sku": "SKU-A",
      "qty": 2,
      "price": 100.0
    },
    {
      "id": 6,
      "sku": "SKU-B",
      "qty": 1,
      "price": 50.0
    }
  ]
}
```

