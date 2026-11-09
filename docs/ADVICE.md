# Advice (advisory, model-generated)

Source: **saved fixture (no request)**. This file is a suggestion list, not evidence. Every claim in it must still be
checked against `docs/FINDINGS.md` and the artifact named in the `cites` column.
Accepted 3 of 4 suggestions; 1 dropped by the validator.

**Summary (model):** The service is testable but not observable: the highest-risk item is the swallowed exception, because a failed write looks like success.

| rank | action | why | cites |
|---|---|---|---|
| 1 | Replace the swallowed exception in createOrder with an error response | a failed write currently returns HTTP 200, so the caller cannot tell success from failure | `F3`, `docs/ERRORS.md` |
| 2 | Move the fee percentage out of the literal and into configuration | the fee is a pricing rule that lives in code; every change becomes a deploy | `F2` |
| 3 | Add a test for the customer endpoint with an unknown id | the current behaviour returns an empty body with status 200, which no client can act on | `F1`, `GET /api/customers/{id}` |

## Dropped by the validator

- rank 4: invented number(s) ['40']

## What this file is not

- it is not a measurement: no number here was produced by the pipeline;
- it is not part of the gate: CI validates it offline, it never decides a build;
- removing it changes nothing about the tests, the coverage or the maps.
