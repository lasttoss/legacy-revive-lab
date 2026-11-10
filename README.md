# legacy-revive-lab — the service as found

This branch is the service **exactly as it was inherited**, deliberately untouched:

```
Spring Boot 2.7 · Java 8 · SQLite · 14 files
no tests · no CI · no documentation · dead code still present
```

It is kept this way on purpose. It is the *before* side of a diff, so the work can be
reviewed as a change instead of being taken on trust.

## The work is on the `revival` branch

**[→ Branch `revival`](https://github.com/lasttoss/legacy-revive-lab/tree/revival)** — the same
service with the pipeline that revives it:

```
20/20 golden recordings pass            behaviour recorded before the refactor
89.2% line coverage (107 of 120)        gate floor 80%, ratchet locked at 0.892
endpoint → table map                    which table a change actually touches
changed-file impact report              UNMAPPED files are named, never silently ignored
generated docs + CI drift check         regenerating and not committing fails the build
```

## See the difference in one command

```bash
git diff main..revival --stat     # exactly what was added, nothing hidden
```

## Run it

```bash
git switch revival
make all        # maps, tests, docs, coverage gate, smoke
```

| Branch | Role |
|---|---|
| `main` | the service as found — no tests, no docs, no CI |
| `revival` | the same service, recorded, mapped, gated — and the pipeline that keeps it that way |

Nothing on `revival` was written from memory: every test, map and page is generated from the
code, and the CI fails when the generated output drifts from what is committed.
