# BUG-024: Broken Function-Level Authorization — limited Third Party User reaches `suggestions/bulk-accept-with-control-implementation`

**Program:** Optro Managed Bug Bounty (private)
**Reporter:** zeno0 (zeno0@bugcrowdninja.com)
**Asset:** `https://bugbounty1.qe.optrostaging.ai`
**Build tested:** app_version **47.3.0-dev**, deployed 2026-11-10T17:56:45Z
**Date:** 2026-11-11
**Severity recommendation:** **P3 — Broken Function-Level Authorization (no successful mutation demonstrated)**
**Header on all requests:** `X-Optro-Bug-Bounty: zeno0`

---

## 1. Summary

`POST /api/v1/suggestions/bulk-accept-with-control-implementation` performs **no role or permission check**. A **Third Party User (role 11, `is_limited: true`)** — the lowest-privilege role in the product — reaches the same handler as an Owner and receives a **byte-identical response**.

The endpoint is a privileged bulk mutation: it accepts AI match suggestions and creates controls plus control implementations across programs and entities.

**Honest constraint:** the handler currently crashes on every suggestion in this environment (`suggestable[...] is not a function`), so I could **not** demonstrate a successful mutation. The authorization gap is proven; the write impact is not.

---

## 2. The control that proves TPU is genuinely limited

Before the finding, TPU's restrictions were confirmed on every adjacent resource:

| request | TPU result |
| --- | --- |
| `GET /api/v1/suggestions` | 200 — **0 rows** (correctly scoped; Owner sees 111) |
| `GET /api/v1/suggestions/41` | **422 `ModelActionPermissionDenied`** |
| `GET /api/v1/narratives/38` | **422 `ModelActionPermissionDenied`** |
| `GET /api/v1/users/1` | **403 `ForbiddenError`** |
| `GET /api/v1/timesheet_entries/43` | **422** |

TPU cannot read the suggestion it is about to accept, cannot read the narrative the suggestion belongs to, and cannot read the user record. It is a genuinely limited role.

---

## 3. The finding

```
POST /api/v1/suggestions/bulk-accept-with-control-implementation
{"data":{"suggestionIds":[41],"createControlImpls":false,"programIds":[]}}
```

| caller | status | response |
| --- | --- | --- |
| **TPU (role 11, limited)** | **422** | processing failure |
| Owner (role 5) | 422 | **byte-identical** |

`IDENTICAL RESPONSE: True`

The 422 is **not** an authorization denial. Keyword scan of the TPU response body:

```
contains 'permission':                 False
contains 'forbidden':                  False
contains 'denied':                     False
contains 'not authorized':             False
contains 'modelactionpermissiondenied': False
```

The body is a **processing summary**:

```json
{"status":"failed",
 "summary":{"created":{"controls":{"count":0,"ids":[],"uids":[]},
                      "controlImplementations":{"count":0,"ids":[],"uids":[]}},
            "failed":{"processes":{"count":1,"errors":[{"uid":"41",
              "error":"Error processing suggestion 41: suggestable[(intermediate value)(intermediate value)(intermediate value)] is not a function"}]},
            "existingUids":{"count":0,"ids":[],"uids":[]},
            "controlImplementations":[]}}
```

TPU reached the business logic. The handler failed on an internal JavaScript error, not on a permission gate.

---

## 4. Second unguarded privileged action

The same role also reaches the export plane:

| request | TPU result |
| --- | --- |
| `POST /api/v1/users/export` | **200 `{"status":"ok"}`** |
| `POST /api/v1/users/_op/async_export` | **200 `{"status":"ok"}`** |

Both queue a **full user-table export** (354 users, 317 emails) for a limited third-party user. In this environment the export produces no retrievable artifact (no file appears in `/files` or `/attachments` after the call), so the data-exfiltration impact is **not** demonstrated — but the privileged action is authorized for the wrong role.

---

## 5. Reproduction — copy-paste

```bash
H="https://bugbounty1.qe.optrostaging.ai"
BB="X-Optro-Bug-Bounty: zeno0"

# Limited Third Party User (role 11)
T=$(curl -s -X POST "$H/api/v1/users/login" -H "$BB" \
  -H "Content-Type: application/json" \
  -d '{"credentials":{"email":"<tpu-account>","password":"<pw>"}}' \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["session"]["token"])')

# Control: this role cannot read the suggestion
curl -s "$H/api/v1/suggestions/41" -H "token: $T" -H "$BB"
# → 422 ModelActionPermissionDenied

# Control: this role cannot read the parent narrative
curl -s "$H/api/v1/narratives/38" -H "token: $T" -H "$BB"
# → 422 ModelActionPermissionDenied

# Finding: but it reaches the bulk mutation handler
curl -s -X POST "$H/api/v1/suggestions/bulk-accept-with-control-implementation" \
  -H "token: $T" -H "$BB" -H "Content-Type: application/json" \
  -H "X-Auditboard-Product: System" \
  -d '{"data":{"suggestionIds":[41],"createControlImpls":false,"programIds":[]}}'
# → 422 with a PROCESSING summary (no permission keyword), identical to Owner
```

---

## 6. What was tested and did NOT work (honest negatives)

| vector | result |
| --- | --- |
| `GET /suggestions/{id}` as TPU | **422 permission denied** — correctly gated |
| `GET /narratives/{id}` as TPU | **422 permission denied** — correctly gated |
| `GET /users/1` as TPU | **403** — correctly gated |
| `POST /suggestions/bulk-accept` (plain) | **500** for every role — endpoint broken, shape-independent |
| `POST /suggestions/bulk-reject` | **500** for every role — broken |
| `POST /esg_metric_values/bulk-delete` | **500** all roles |
| `POST /framework_items/bulk-complete-version-mapping` | 204 all roles (no-op) |
| `POST /ticketing/tickets/bulk` | 201 `{}` all roles (no-op; ticketing integration not configured) |
| `POST /policy_*/bulk_accept`, `bulk_upsert`, `bulk_update` | 422 shape-gated |
| `POST /{model}/bulk_update` (risks, controls, issues) | **404** — no such route |
| Successful suggestion acceptance as TPU | **not achievable** — handler crashes on all 111 suggestions (`suggestable[...] is not a function`) |

**No successful mutation was demonstrated.** All 111 suggestions are `suggestable_type: Narrative` and every one hits the same internal error.

---

## 7. Impact

- **A limited Third Party User reaches a privileged bulk-mutation handler** that creates controls and control implementations across programs and entities — the same handler an Owner uses.
- **No authorization check exists on the route.** The response is byte-identical between role 11 and role 5, which means the only thing preventing a write is the handler's own bug.
- **If the handler is fixed** (the `suggestable[...]` error resolved), role 11 would be able to accept AI match suggestions and create control implementations — a write action on audit content the role cannot even read.
- **The export plane is likewise reachable** by role 11 for the full user table.

**Honest ceiling:** this is **P3**. The authorization gap is proven by control-versus-finding differential, but I could not produce a successful state change because the endpoint crashes for every caller including Owner. I am not claiming a working write primitive.

---

## 8. Remediation

1. Add an explicit permission check to `suggestions/bulk-accept-with-control-implementation` — the same `suggestion:action.*` check that already protects `GET /suggestions/{id}`.
2. Apply the same check to `users/export` and `users/_op/async_export`.
3. Audit the remaining bulk routes for the same missing gate; several are currently broken (500) and their authorization state is unknown.
4. Fix the `suggestable[...] is not a function` handler error — a crashing privileged endpoint is both a reliability and a security-signal problem.

---

## 9. Evidence / cleanup

- Read-only probing plus one bulk-accept attempt per role. **No state change occurred** (all responses report `created.count: 0`).
- Export calls queued but produced no artifact; nothing was downloaded.
- Disclosed from this engagement: files 2712/2726/2730/2732 deleted (BUG-015); issue 121 status changed; narrative 67 created; risk/narrative names modified (BUG-019); attachments 11207–11220, 11252–11266 generated; several account emails changed during BUG-017 and left in place at the operator's instruction; comments 903–968 on ExceptionRequest 33.
- **BUG-022 (stored XSS in comments) is RETRACTED.**
