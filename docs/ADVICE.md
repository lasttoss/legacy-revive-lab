# Advice (advisory, model-generated)

Source: **one request to `deepseek/deepseek-v4.1-flash` at `api.commandcode.ai`**. This file is a suggestion list, not evidence. Every claim in it must still be
checked against `docs/FINDINGS.md` and the artifact named in the `cites` column.
Accepted 7 of 7 suggestions; 0 dropped by the validator.

**Summary (model):** Prioritize the highest-traffic customer lookup N+1 and the order-creation path, which swallows exceptions and returns null while also using a time-based ID. Then address observed parsing and SQL errors, and only after that clean up the hard-coded fee and unused legacy artifacts.

| rank | action | why | cites |
|---|---|---|---|
| 1 | Fix the N+1 query behavior in GET /api/customers/{id} by avoiding one extra query per order. | This is the highest-traffic endpoint in the evidence, and F1 states it issues one extra query per order. | `F1` |
| 2 | Change LegacyService.createOrder so it does not swallow every exception and return null; propagate or handle errors explicitly. | F3 describes swallowed exceptions returning null, and the evidence includes an ERROR NullPointerException signature with 2 events. | `F3`, `E-538658668f` |
| 3 | Replace the System.currentTimeMillis()-based ID in POST /api/orders with a collision-resistant identifier approach. | F4 identifies time-based ID generation in the order-creation endpoint, which has recorded traffic in the evidence. | `F4` |
| 4 | Harden numeric parsing for the input path that produced NumberFormatException for the string "three". | The evidence records an ERROR NumberFormatException with 2 events for input string "three". | `E-793018aeb2` |
| 5 | Investigate and correct the SQL statement preparation failure behind the Hibernate SQLGrammarException. | The evidence records an ERROR SQLGrammarException: could not prepare stateme with 1 event. | `E-4262828dda` |
| 6 | Make the 7% fee in LegacyService.createOrder explicit rather than an inline literal, and document the business rule. | F2 states the 7% fee is a literal inside createOrder, making the business rule implicit. | `F2` |
| 7 | Confirm there are no external references, then remove the unused legacy_flags table usage expectation and LegacyDeadCode. | F5 says legacy_flags is never read or written, and F6 says LegacyDeadCode is referenced by nothing. | `F5`, `F6` |

## What this file is not

- it is not a measurement: no number here was produced by the pipeline;
- it is not part of the gate: CI validates it offline, it never decides a build;
- removing it changes nothing about the tests, the coverage or the maps.
