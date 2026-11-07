# BUG-009 (P2 rec): Password-History Enumeration Oracle via Cross-Account User Write — Rate-Free Credential Recovery for Arbitrary Users

**Program:** Optro Managed Bug Bounty (private)
**Reporter:** zeno0
**Date:** 2026-11-07
**Asset:** `https://bugbounty1.qe.optrostaging.ai` (AuditBoard QE staging)
**Related:** BUG-008 (P1, submitted) — cross-account user-record write. BUG-009 uses the same write primitive but produces a **distinct impact: disclosure of the victim's real password**, not assignment of an attacker-chosen one. Report includes the dependency explicitly for triage dedup.

---

## Summary

The `PUT /api/v1/users/{id}` mass-assignment flaw documented in BUG-008 (no object-level authorization on user records) allows an authenticated lower-privileged user to attempt setting another user's password. The endpoint **rejects candidates that match the target's current or historical passwords** with a distinctive validation error — while candidates not in the history are accepted and applied (HTTP 200).

This differential turns the password-change endpoint into a **password-history enumeration oracle**: an attacker can submit policy-compliant candidate passwords one by one, and a `422 "Password has been used"` response confirms the candidate **is or was the target's real password**. With the real password recovered, the attacker logs in as the victim on the web UI — a login that is forensically indistinguishable from the victim's own (no forced password change, no password-expiry flag, no artifacts).

**The oracle path has no rate limiting.** During testing, 3 rapid password attempts completed in 2.5 seconds with zero 429 responses — in contrast to the dedicated `POST /api/v1/users/password-reset` endpoint, which returns 429 after ~3 rapid attempts. The unlimited branch is exactly where the guessing happens.

## PoC (authorized dual-account test, victim = tester-owned account 231)

### Step 1 — history hit on a PAST password (proves enumeration of previous passwords, not only current)

Attacker account B (user 230, role Owner) targets victim A (user 231):

```http
PUT /api/v1/users/231 HTTP/1.1
Host: bugbounty1.qe.optrostaging.ai
token: <B_api_token>
X-Optro-Bug-Bounty: zeno0
X-Auditboard-Product: System
X-Auditboard-Module: account
Content-Type: application/json

{"user":{"password":"ZzZtmpPw2!"}}
```

Response (the tested value `ZzZtmpPw2!` was A's password from a **previous** rotation — it is no longer current):

```json
{"errors":[{"detail":"Password has been used. Please choose another.","source":{"pointer":"data/attributes/password"},"disableGrowl":true}]}
```

HTTP **422**. A password that was replaced weeks earlier is still confirmed as "used" — the oracle reads the full password history.

### Step 2 — no rate limit on the guessing path

Three consecutive PUTs with different candidates completed in **2.5 seconds total**:

```
PUT {"user":{"password":"ZzZtmpPw3!"}}  -> 422 (history hit — current password)
PUT {"user":{"password":"Summer2025!"}} -> 200 (miss — password rotated)
PUT {"user":{"password":"Audit2026!"}}  -> 200 (miss — password rotated)
```

No 429, no lockout, no cooldown. For comparison, the pre-auth `POST /api/v1/users/password-reset` verification endpoint enforces 429 after ~3 rapid attempts — the control exists in the codebase but is absent on the user-update path where the oracle lives.

### Step 3 — miss branch still yields ATO (completeness of the attack tree)

On a miss the PUT applies the attacker's candidate; the only friction is `requires_password_change=true`, cleared in the same request family (BUG-008):

```http
PUT /api/v1/users/231
{"user":{"requires_password_change":false}}
```

then

```http
POST /api/v1/users/login HTTP/1.1

{"credentials":{"email":"<victim_email>","password":"ZzZtmpPw5!"}}
```

HTTP **200** with a full `session` object (fresh API token for the victim). Both branches end in attacker access.

## Attack tree

| Branch | Meaning | Outcome |
|---|---|---|
| Candidate → **422** history hit | Candidate is the victim's current **or past** real password | Attacker logs in via UI with the victim's **own** password — no forced-change artifacts, minimal forensic footprint |
| Candidate → **200** | Candidate was fresh | Victim's password is now the attacker's candidate; flag-clear → API/UI ATO anyway |

Either way the attacker wins. The 422 branch additionally leaks the victim's original credential, which may be reused **across other systems** (password reuse) — impact beyond this application.

## Impact

- Any user reachable by the BUG-008 write primitive — the entire org roster (316 users at test time), including role 1 Superuser (user id 1) — can have their **real password recovered** by an Owner-role attacker.
- Recovery is offline-rate-free: the only cost is one PUT per candidate; candidates constrained only by the org password policy (which is itself discoverable via error messages, e.g. reuse checks).
- The recovered password is the victim's genuine credential: UI login leaves no `requires_password_change` residue, MFA is not enabled on test accounts, and no current-password confirmation is required anywhere in the chain.
- No rate limit: contrast with `password-reset` (429 after ~3) proves the missing control is an implementation gap, not an intentional design.

## Severity reasoning (honest)

- **P2 recommendation.** The oracle depends on BUG-008's missing object-level authorization (the write primitive). It does not stand alone; it materially upgrades BUG-008's impact from *attacker assigns password* to *attacker recovers the victim's actual password* (credential disclosure + cross-system reuse risk). If triage prefers, treat this as an impact amplification addendum to BUG-008 — the technical content is self-contained either way.
- Not claimed: MFA bypass (MFA was not enabled on test accounts; behavior with MFA enabled is untested), persistence beyond password state, or any cross-org reach.

## Fix recommendations

1. Apply the same 429/lockout policy that `password-reset` already has to password-change attempts on `PUT /users/{id}` — especially failures driven by history checks.
2. Collapse the error: return a generic validation failure for history collisions (never reveal membership of a candidate in the history).
3. Root cause: fix BUG-008 (object-level authorization on user-record updates). Without the cross-account write the oracle disappears.
4. Alert on repeated `password_history` validation failures from a single actor — a natural tripwire for exactly this attack.

## Reproduction artifacts

- Script: `scripts/t034a_history_oracle.py` (PoC steps 1–3 + rate check)
- Raw results: `state/t034a_oracle.json`
- Victim state fully restored after testing (password rotated to a tester-managed value, flag cleared, login verified).
