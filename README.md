# legacy → tested, documented, gated

A Spring Boot 2.7 / Java 8 / SQLite service with **no tests, no docs, no CI** — and the pipeline that
turns it into a service with a 20-test suite, generated documentation, a service map, an impact index and
a coverage gate at 80%.

The repository is two branches on purpose, so the change can be reviewed as a diff:

```
main      the service as found        14 files · no tests · no CI · no docs · dead code present
revival   the same service, revived   60 files · 20/20 tests · 89.2% line coverage · CI gate
```

```bash
git diff main..revival --stat       # exactly what was added, nothing hidden
```

## The claim, in one line

> None of the tests, docs or maps below were written by hand from memory. Every one is generated from
> three kinds of evidence — sampled traffic, SQL logs, error logs — and regenerating them is part of CI,
> so they cannot drift.

## What gets produced, and from what

```
samples/access.log   20 sampled requests          -> inventory (ranked by traffic) + golden recordings
samples/sql.log      10 statements with trace ids -> endpoint -> table map, orphan tables
samples/error.log    6 events, 4 signatures       -> error catalogue with fingerprints
samples/rpc.log      11 cross-service calls       -> service map, endpoint->endpoint, impact index
```

| Output | Command | What it answers |
|---|---|---|
| `docs/INVENTORY.md` | `make maps` | what exists, what is used, what is dead, what to do first |
| `docs/ENDPOINT-DB.md` | `make maps` | which endpoint touches which table; which tables nobody touches |
| `docs/ERRORS.md` | `make maps` | which failures repeat, on which endpoint, and what test to write |
| `docs/SERVICES.md` | `make maps` | service index: endpoints, tables, callers, traffic share |
| `docs/SERVICE-MAP.md` | `make maps` | endpoint → endpoint, joined by trace id |
| `docs/IMPACT.md` + `.json` | `make maps` | if I change X, what else must be re-checked |
| `samples/golden/*.json` | `make record` | what the service actually answers, today |
| `GoldenMasterTest.java` | `make tests` | one test per recording, generated |
| `docs/API.md` | `make docs` | per-endpoint contract with real request/response |

## Measured on this snapshot

```
tests              20/20 pass
line coverage      89.2%   (107/120)   floor 80%, ratchet baseline recorded at 89.2%
branch coverage    85.7%   (12/14)
method coverage    84.5%   (49/58)
generated artifacts 11 markdown files + 1 json, all reproducible
```

## The order that makes it possible

```
1  inventory     rank by traffic, not alphabet      -> 4 endpoints, 35% of traffic on one of them
2  record        replay the sample against the app  -> the only honest specification that exists
3  generate      one test per recording             -> 20 tests, zero hand-written assertions
4  cover         JaCoCo floor 80% + ratchet         -> the number cannot silently fall
5  document      from the recordings + logs         -> cannot drift, CI fails on a stale doc
6  gate          CI: regenerate, diff, verify       -> a stale map is a build failure
```

Coverage went 84.9% -> 89.2% with one change: deleting the class nothing referenced. That is the cheapest
coverage win in any legacy codebase, and the inventory finds it automatically.

## What the evidence found in the code

All six are in [`docs/FINDINGS.md`](docs/FINDINGS.md) with the artifact that proves each one:

```
N+1            GET /api/customers/{id} -> 4 statements for one request
magic number   the 7% fee lives as a literal in LegacyService.createOrder
swallowed      createOrder catches Exception, prints, returns null  -> HTTP 200 on a failed write
collision      order id comes from System.currentTimeMillis()
orphan table   legacy_flags is never read or written
dead code      LegacyDeadCode referenced by nothing (removed in this branch)
```

## What this does NOT prove

- **The sample logs are synthetic.** They imitate a production shape; they are not production data.
  The pipeline is what is being demonstrated, not the statistics of this service.
- **Only traffic that exists can be recorded.** Refunds, admin screens, scheduled jobs: no traffic, no
  test. `docs/FINDINGS.md` says so instead of pretending coverage is complete.
- **A characterization test protects current behaviour, bugs included.** `GET /api/customers/999`
  returns 200 with an empty body; the test locks that in. Approving a behaviour is a human step.
- **`why 7%` is not recoverable from any log.** Intent needs a person; the artifacts can only say what.

## Reproduce

```bash
make maps        # regenerate every map from samples/ (no build needed)
make record      # replay samples/access.log against the app -> samples/golden/
make tests       # generate the suite from the recordings
make verify      # run the suite + JaCoCo (fails under 80%)
make coverage    # coverage report + ratchet
make all         # the whole chain
```

Requires docker (Maven + JDK 8 image) and python3. No Java on the host.
