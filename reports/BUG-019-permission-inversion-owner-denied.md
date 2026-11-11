# BUG-019: Permission inversion — Tester and Reviewer can edit risks and narratives that Owner is explicitly denied

**Program:** Optro Managed Bug Bounty (private)
**Reporter:** zeno0 (zeno0@bugcrowdninja.com)
**Asset:** `https://bugbounty1.qe.optrostaging.ai`
**Build tested:** app_version **47.3.0-dev**, deployed 2026-11-10T17:56:45Z
**Date:** 2026-11-11
**Severity recommendation:** **P2 — Broken Access Control (role permission inversion)**
**Header on all requests:** `X-Optro-Bug-Bounty: zeno0`

---

## Access — how to reproduce

```
Login to : golden-snow-4771@bugcrowdninja.com
Password  : Zx9!Owner2026
Role      : Owner (role_id 5)
Navigate  : https://bugbounty1.qe.optrostaging.ai/workspace/7/risks/risk-list
```

Header on every request: `X-Optro-Bug-Bounty: zeno0`

Owner is denied `PUT /api/v1/risks/{id}`; Tester succeeds on the same object.

---

## 1. Summary

The RBAC configuration grants **edit** rights on `risk` and `narrative` to **Tester (role 4)** and **Reviewer (role 3)**, but **not** to **Owner (role 5)**. The result is a permission **inversion**: a lower-privileged role can modify records that a higher-privileged role is explicitly denied.

Verified by read-back on six independent objects (three risks, three narratives). The denial is a genuine authorization check, not a validation error — the response is `422 ModelActionPermissionDenied (Permission: risk:action.edit)` / `(Permission: narrative:action.edit)`.

This is not a case of "Owner can do everything." Owner is the tenant's default business role (116 of 145 login-enabled accounts) and is **less** able to edit risk and narrative content than a plain Tester.

---

## 2. Root cause

Per-role permission rows for `risk:action.edit` and `narrative:action.edit` are absent from role 5 (Owner) while present and permissive for roles 2, 3 and 4.

Confirmed against the live RBAC data returned by `GET /api/v1/role_permissions?role_id=5`:

```
role5 risk:action.edit        -> NOT PRESENT
role5 narrative:action.edit   -> NOT PRESENT
role5 control:action.edit     -> NOT PRESENT
```

`control:action.edit` being absent for role 5 does **not** block control edits (Owner receives 200 on `PUT /controls/{id}`), so the enforcement path for controls differs from risks/narratives. For risks and narratives the absence of the row is enforced as a denial.

The practical defect: the role configuration is internally inconsistent — a mid-tier role holds a write permission that the role above it lacks, with no documented reason.

---

## 3. Reproduction — copy-paste

```bash
H="https://bugbounty1.qe.optrostaging.ai"
BB="X-Optro-Bug-Bounty: zeno0"

# Owner (role 5)
O=$(curl -s -X POST "$H/api/v1/users/login" -H "$BB" -H "Content-Type: application/json" \
  -d '{"credentials":{"email":"golden-snow-4771@bugcrowdninja.com","password":"<pw>"}}' \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["session"]["token"])')

# Tester (role 4)
T=$(curl -s -X POST "$H/api/v1/users/login" -H "$BB" -H "Content-Type: application/json" \
  -d '{"credentials":{"email":"tester@soxhub.com","password":"<pw>"}}' \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["session"]["token"])')
```

### Step 1 — Owner is DENIED editing a risk

```bash
curl -s -X PUT "$H/api/v1/risks/1" -H "token: $O" -H "$BB" \
  -H "Content-Type: application/json" -H "X-Auditboard-Product: System" \
  -d '{"risk":{"name":"ZX-OWNER-PROBE"}}'
```

→ **`422`**

```json
{"errors":[{"code":"ModelActionPermissionDenied",
 "detail":"You do not have permission to perform this action. (Permission: risk:action.edit)"}]}
```

### Step 2 — Tester is ALLOWED editing the same risk

```bash
curl -s -X PUT "$H/api/v1/risks/1" -H "token: $T" -H "$BB" \
  -H "Content-Type: application/json" -H "X-Auditboard-Product: System" \
  -d '{"risk":{"name":"ZX-TESTER-PROBE"}}'
```

→ **`200`**, and the change persists:

```bash
curl -s "$H/api/v1/risks/1" -H "token: $T" -H "$BB" \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["risks"][0]["name"])'
# → ZX-TESTER-PROBE
```

### Step 3 — same inversion on narratives

```bash
curl -s -X PUT "$H/api/v1/narratives/31" -H "token: $O" -H "$BB" \
  -H "Content-Type: application/json" -H "X-Auditboard-Product: System" \
  -d '{"narrative":{"name":"ZX-OWNER-PROBE"}}'
# → 422 (Permission: narrative:action.edit)

curl -s -X PUT "$H/api/v1/narratives/31" -H "token: $T" -H "$BB" \
  -H "Content-Type: application/json" -H "X-Auditboard-Product: System" \
  -d '{"narrative":{"name":"ZX-TESTER-PROBE"}}'
# → 200, persists
```

---

## 4. Verified matrix (read-back confirmed, unique value per attempt)

| role | `PUT /risks/{id}` | `PUT /narratives/{id}` | `PUT /controls/{id}` |
| --- | --- | --- | --- |
| Owner (5) | **422 denied** | **422 denied** | 200 |
| System Admin (2) | 200 | 200 | 200 |
| Reviewer (3) | **200** | **200** | 200 |
| **Tester (4)** | **200** | **200** | 200 |
| External Auditor (6) | **422 denied** | **422 denied** | 200 |
| Third Party User (11) | 422 denied | 422 denied | 422 denied |

Reproduced on **six independent objects** — risks 1, 2, 3 and narratives 31, 38, 39 — with identical results for Owner (422), Reviewer (200) and Tester (200).

`DELETE` on the same resources is denied for **all** roles including Owner (422), so the inversion is specific to the edit verb.

---

## 4.1 Second affected resource: `project_plan` (read inversion)

The same inversion appears on `project_plan`, in the read direction.

| role | `GET /api/v1/project_plans` | `GET /api/v1/project_plans/154` |
| --- | --- | --- |
| Owner (5) | 200, **102 plans** | **422 `project_plan:action.view`** |
| Tester (4) | 200, **104 plans** | **200 — full record** |
| Third Party (11) | 200, 5 plans | 422 |

- Plans **154** and **155** are visible to Tester and **not** to Owner. Owner's list is a strict subset of Tester's (Tester-only: 154, 155; Owner-only: none).
- Owner denial is a genuine authorization check: `422 ModelActionPermissionDenied (Permission: project_plan:action.view)`.
- Tester reads the full record: `title='Emplovee Information Assessment'`, `budget_hours=100`, `total_hours=200`, `start_date=2024-01-01`, `end_date=2024-12-31`, `plannable_type=ControlsDatum`, `plannable_id=38`, `project_plan_container_id=1`.
- **Write is denied for both roles** (`PUT` -> 422 `project_plan:action.edit`), so this is read-only.

Note: `project_plan` does not appear in the RBAC matrix returned by `role_permissions` for roles 2, 4 or 5 (0 rows matched), so the permission is enforced by a path outside the exposed permission table — which is itself why the inversion is not visible to an administrator reviewing the matrix.

---

## 5. Impact

- **A lower-privileged role holds capabilities a higher-privileged role lacks.** Tester (role 4) and Reviewer (role 3) can **modify** risk and narrative records that Owner (role 5) cannot. Tester can also **read** project plans (154, 155) that Owner is denied.
- **Owner is the default business role** — 116 of 145 login-enabled accounts. The inversion affects the majority of the tenant's users, not an edge case.
- **Content integrity.** Risks and narratives are the core audit artefacts in this product. A role that is meant to be read-restricted on them can alter their content.
- **Indicates a misconfigured RBAC model.** A role matrix where a mid-tier role exceeds a higher tier is a configuration defect that will produce further unintended grants as roles evolve.

**Honest ceiling:** this is an **authorization inconsistency**, not a privilege escalation to a higher tier. The attacker (Tester/Reviewer) does not gain Owner's or Superuser's capabilities — they gain a specific write permission Owner happens to lack. The impact is unauthorized modification of risk and narrative content by a lower role. Note the program's own guidance that default role permission sets must not be edited; this finding is a defect in the shipped configuration, not a change made during testing.

---

## 6. What was tested and did NOT work (honest negatives)

| vector | result |
| --- | --- |
| `PUT /api/v1/issues/121` — all six roles | **422** uniformly (issue 121 is Closed; workflow blocks edits) |
| `DELETE` risks / narratives — Owner, Reviewer, Tester | **422** for all — delete is correctly denied |
| `PUT /api/v1/controls/1` — Owner, SysAdmin, Reviewer, Tester, ExtAuditor | 200 — consistent across those roles, not an inversion |
| Third Party User (role 11) — all edit attempts | **422** uniformly — correctly restricted |
| External Auditor (role 6) — risks / narratives | **422** — matches Owner, also denied |

**The inversion is specific to Tester and Reviewer on `risk` and `narrative` edit, and to Tester on `project_plan` read.**

---

## 7. Remediation

1. Audit the shipped role permission sets for `risk:action.edit` and `narrative:action.edit`; grant them to Owner (role 5) or remove them from Tester (role 4) and Reviewer (role 3) — whichever matches the intended model.
2. Add a consistency check to the role-configuration tooling: a role must not hold a permission that a role above it lacks, unless explicitly flagged as intentional.
3. Document the intended risk/narrative edit model so the enforcement path for these resources matches `control` (where Owner is permitted despite the absent row).

---

## 8. Evidence / cleanup

- **Test artifacts:** risk names on ids 1, 2, 3 and narrative names on ids 31, 38, 39 were modified during this sweep (values of the form `ZX-<ROLE>-<hex>`). These are content changes on real records and are disclosed here.
- No records were deleted (all DELETE attempts 422).
- Disclosed from this engagement: files 2712/2726/2730/2732 deleted (BUG-015); issue 121 status changed; narrative 67 created; attachments 11207–11220 generated; several account emails changed during BUG-017 testing and left in place at the operator's instruction.
- No role permission sets were edited during testing.
