# A three-service repository, for one purpose

This tree exists so `kit/discover.py` can be tested on a repository it has never seen: three Spring services,
one gateway, two data services, one table each, no logs and no tests. Source only — no build, no database.

```bash
python3 kit/discover.py --root examples/multi-service
```

Expected: **3 services, 6 endpoints**, `customers` owned by `customer-svc`, `orders` owned by `order-svc`.

It is deliberately tiny. Its job is to answer one question honestly — *does discovery work without being
told anything* — not to look like a real system.
