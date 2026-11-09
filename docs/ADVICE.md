# Advice (advisory, model-generated)

Source: **one request to `deepseek/deepseek-v4.1-flash` at `api.commandcode.ai`**. This file is a suggestion list, not evidence. Every claim in it must still be
checked against `docs/FINDINGS.md` and the artifact named in the `cites` column.
Accepted 8 of 8 suggestions; 0 dropped by the validator.

**Summary (model):** The pack covers legacy-app with 5 observable endpoints, and traffic is concentrated on GET /api/customers/{id} (7) and GET /api/orders/{id} (6); POST /api/orders and GET /api/reports/top each record 3. Six findings are listed (F1–F6) and four error signatures (two ERROR types at 2 events each, one SQLGrammarException, one WARN with an empty exception). Recorded statuses are 200 only, so the error signatures are the sole failure evidence available, and the pack contains no stack trace, endpoint tag or code location that maps any error signature to a specific finding — any causal link below is stated as a hypothesis, not a fact. Note also that tables_seen holds the values "INSERT" and "SELECT" rather than table names, which does not match the table ids in impact_keys; that field is ambiguous and I do not rely on it.

| rank | action | why | cites |
|---|---|---|---|
| 1 | Rework the customer lookup so the per-order extra query (N+1) is replaced by a single batched/joined fetch, and verify the response shape is unchanged. | F1 is the only finding on the highest-traffic endpoint (7 in endpoints_by_traffic). It is a query-count problem with no behavioural change required, which makes it the highest ratio of traffic affected to risk taken. | `F1`, `endpoint:GET /api/customers/{id}` |
| 2 | Stop createOrder from catching every exception and returning null; propagate or explicitly map failures, and check callers that treat a null result as success. | F3 describes blanket exception swallowing plus a null return. The pack records a NullPointerException signature at ERROR level, and a null order result is a plausible producer of it on POST /api/orders — but no evidence ties that signature to this method, so treat the link as a hypothesis to confirm before relying on it. | `F3`, `E-538658668f`, `endpoint:POST /api/orders` |
| 3 | Replace the System.currentTimeMillis()-derived order id with a collision-safe id source and check what depends on the current id format. | F4 states POST /api/orders takes its id from the clock. Under concurrent requests this allows duplicate ids; the endpoint has 3 recorded requests, so collision risk is real but unquantified in the pack. | `F4`, `endpoint:POST /api/orders` |
| 4 | Extract the 7% fee out of LegacyService.createOrder into named configuration and add a test pinning the current value so the change is behaviour-preserving. | F2 places the fee as a literal inside the order-creation method: a business constant embedded in code, on the write path (3 requests). The pack gives no fee history or config mechanism, so the only defensible first step is extraction with the value unchanged. | `F2`, `endpoint:POST /api/orders` |
| 5 | Locate the input path that produces the parse failure behind this signature and add validation or a handled error response before the parse. | E-793018aeb2 records 2 ERROR events for NumberFormatException on input "three". No finding in the pack identifies the parsing site or the endpoint it arrives on, so the source must be found before any fix is proposed. | `E-793018aeb2` |
| 6 | Identify the statement and mapping behind the SQLGrammarException and reproduce it against the current schema before changing anything. | E-4262828dda is a single ERROR event. The pack records no artifact or finding naming the failing query or table, so no specific repair can be justified from the evidence. | `E-4262828dda` |
| 7 | Confirm no external consumer or operational job depends on legacy_flags, then retire the table; if ownership cannot be established, document it instead of dropping it. | F5 says the table is never read or written. That supports removal, but the pack does not show whether anything outside this service touches it, which is why the confirmation step is part of the action. | `F5` |
| 8 | Delete LegacyDeadCode after a build and reference check confirms nothing reaches it. | F6 states it is referenced by nothing. This is the lowest-risk item in the pack and has no traffic implication; its value is reducing surface area for future readers. | `F6` |

## What this file is not

- it is not a measurement: no number here was produced by the pipeline;
- it is not part of the gate: CI validates it offline, it never decides a build;
- removing it changes nothing about the tests, the coverage or the maps.
