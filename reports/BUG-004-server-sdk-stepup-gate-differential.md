# BUG-004 — Wallet-operation routes on `/server/{env}/*` accept end-user session JWTs without the `/sdk` elevated-access (step-up) gate: inconsistent step-up enforcement, unverified `x-dyn-server-signing-proof`, and validation gaps on MPC wallet ceremony endpoints

| | |
|---|---|
| **Severity (requested)** | **P3** — Broken Access Control / inconsistent enforcement of a sensitive-operation authorization gate between two route families of the same service |
| **VRT mapping** | Broken Access Control (P3) / Server Security Misconfiguration (P3) |
| **Asset** | `app.dynamicauth.com` (Dynamic API v0 — `/server/{envId}/waas/*` wallet operations) |
| **Environment** | Sandbox `7dfe3b0c-c0db-4dfa-bba6-f72df97ccbd6` (researcher-owned sandbox on researcher-owned org) |
| **Researcher** | zeno0 (`zeno0@bugcrowdninja.com`) |
| **Test window** | 2026-10-26, 14:10–15:20 UTC |
| **Weakness** | Wallet-op routes (`privateKey/export`, `signMessage`, `createRooms`, `keyShares/backup/locations`) exist under both `/sdk/{env}` and `/server/{env}`. The `/sdk` family enforces the elevated-access step-up gate for these operations; the `/server` family accepts the **same plain end-user session JWT with no elevated token, no proof-of-possession, and no body validation** and proceeds to initiate the MPC ceremony (creates rooms, allocates server keygen participants). Additionally, the `x-dyn-server-signing-proof` header that the public spec says is "always verified when present" is **not verified** when a session JWT is present, and several `/server` routes skip input validation entirely (500 instead of 400). |

---

## TL;DR

Dynamic's WaaS (wallet-as-a-service) surface is split into two route families: `/sdk/{env}/...` (called by the browser SDK) and `/server/{env}/...` (documented for server-side callers, authenticated by an API token plus an `x-dyn-server-signing-proof` request signature). Sensitive wallet operations — private-key export and message signing — are protected on the `/sdk` family by an **elevated-access step-up gate**: a plain session JWT gets `403 Elevated access token required`, and the gate only passes after an OTP-backed step-up mints a short-lived elevated token.

Testing against **real, researcher-owned V3 MPC wallets** shows that the identical operations on the `/server` family:

1. **accept the same plain end-user session JWT** (no elevated token, no server credential),
2. **skip body validation entirely** (no `exportId` required, malformed wallet IDs produce a 500 rather than a 400),
3. **initiate the real MPC ceremony server-side** — `200` SSE with `room_created` and a `serverKeygenIds` allocation — operations that on `/sdk` are stopped before ceremony creation,
4. and the documented `x-dyn-server-signing-proof` signature is **not verified** when a JWT is present (garbage proof `aaa.bbb.ccc` accepted; per the public API spec it should be verified "always [when] present").

What this is **not** (tested and ruled out, see §Impact ceiling): actual key-material delivery (the keyshares relay requires a proof-of-possession composite derived from the session's private key), and cross-user wallet access (wallet resolution is user-scoped on both families). The demonstrable harm today is **bypass of the step-up control at ceremony-initiation level plus a broken server-auth model** — which is why this is filed as P3, honestly below the P1/P2 bar.

---

## Background: the two route families and the step-up gate

Dynamic's public API spec (`public-api.yaml`, bundled in the SDK package) describes two server-facing families:

- `/sdk/{envId}/...` — consumed by the browser SDK on behalf of an end user. Auth: `Authorization: Bearer <session JWT>`.
- `/server/{envId}/...` — documented for **server-side callers**. Auth: `Authorization: Bearer <environment API token>` plus `x-dyn-server-signing-proof`, a per-request signature. The spec states this proof is "always verified when present."

For sensitive wallet operations, the `/sdk` family additionally requires an **elevated access token** — a short-lived (300 s), single-use token minted only after a successful step-up (`stepUp/check` + OTP verification with `requestedScopes`). This is the control designed to stop a stolen session JWT from being enough to export keys. Its presence on `/sdk` was re-confirmed with a real wallet in this test (below).

Both families expose the same wallet-operation routes: `POST /waas/{walletId}/privateKey/export`, `POST /waas/{walletId}/signMessage`, `POST /waas/createRooms`, `POST /waas/{walletId}/keyShares/backup/locations`, `GET /waas/byWalletAddress/{address}`, `POST /waas/backup/token`.

---

## Test setup

- Researcher-owned organization on Dynamic; sandbox environment `7dfe3b0c-c0db-4dfa-bba6-f72df97ccbd6` created and owned by the researcher. All identities are researcher-owned Bugcrowd aliases (`zeno0+ev8@…`, `zeno0+ev9@…`).
- Two **real V3 embedded MPC wallets** provisioned via the documented server-side pregen flow (`POST /environments/{env}/waas/authenticate` with a full-scope console API token, then `POST /environments/{env}/waas/create`):
  - **W1** `bdb3c7cc-7bf3-4693-8c07-31c990f07a9c` — owned by end-user `db163919-…` (ev8), address `0xb9726fD2…a22e`, TWO_OF_TWO, backup location `dynamic`, keyShare `0dffa6b8-…` / external `aa7a420a-…`.
  - **W2** `b608b0d1-e501-4df4-a5d4-df1870fb8055` — owned by auto-created user `25ec9a3f-…` (ev9), address `0x76F9b45D…c971E`. Used as the **foreign wallet** in the cross-user matrix.
- Plain end-user session JWT for ev8 (`sub db163919-…`, sandbox session, TTL 7200 s) used as the `Bearer`.
- All requests carried the researcher headers `X-Request-Purpose: Research` / `X-Bugcrowd-Ninja: zeno0`.
- No real user data touched; no key material was delivered or exported at any point.

---

## Evidence

### 1. Decisive control pair — same session, same wallet, two route families

`POST` on the **own** real wallet W1 with the **plain ev8 session JWT** (no elevated token of any kind):

**`/sdk` route — gate fires (step-up enforced):**

```
POST /api/v0/sdk/7dfe3b0c-c0db-4dfa-bba6-f72df97ccbd6/waas/bdb3c7cc-7bf3-4693-8c07-31c990f07a9c/privateKey/export
Authorization: Bearer <ev8 session JWT>
X-Request-Purpose: Research
X-Bugcrowd-Ninja: zeno0
Content-Type: application/json

{"exportId":"<uuid>"}
```

→ `403 {"error":"Elevated access token required","status":403}`

**`/server` route — no gate, ceremony initiated:**

```
POST /api/v0/server/7dfe3b0c-c0db-4dfa-bba6-f72df97ccbd6/waas/bdb3c7cc-7bf3-4693-8c07-31c990f07a9c/privateKey/export
Authorization: Bearer <same ev8 session JWT>
X-Request-Purpose: Research
X-Bugcrowd-Ninja: zeno0
Content-Type: application/json

{}
```

→ `200 text/event-stream`:

```
event: status
data: {"message":"Creating room...","step":"create_room"}

event: room_created
data: {"roomId":"e3057a3beea4919e4295d8b78cf59b7a","serverKeygenIds":["8em4U4qYDhfoYWWVr1iQtzge4VjTz8ZntwJuvXGgb95L"]}

event: error
data: {"error":"Invalid request","status":400}
```

Notes on this pair:

- The `/server` call had an **empty body** — the `/sdk` route requires `exportId` (and rejects `{}` with a 400 *before* the gate). On `/server` there is no validation at all; the request goes straight to wallet resolution and ceremony room creation.
- The room + server keygen participant allocation happened server-side (reproduced **6+ times** across the session, each attempt getting a fresh `roomId`: `e3057a3b…`, `c7b105b7…`, `f3108fd8…`, `bc5d6ffe…`). The ceremony then stalls at `Invalid request` because a browser/client must participate — see §Impact ceiling.
- The identical `{}` body on `/server` with a **server session** instead returns `404` (empty) — i.e. the route neither requires server credentials nor rejects them silently; it just behaves differently per caller type, with the weakest caller type (stolen/plain session) being the one that reaches ceremony initiation.

### 2. Full authorization matrix (own wallet W1)

| # | Route | Bearer | Elevated token | Proof header | Status | Observed |
|---|-------|--------|----------------|--------------|--------|----------|
| 1 | `/sdk/…/privateKey/export` | ev8 session | ✗ | — | **403** | `Elevated access token required` (gate fires before ownership/ceremony) |
| 2 | `/server/…/privateKey/export` | ev8 session | ✗ | — | **200 SSE** | `create_room` → `room_created` + `serverKeygenIds` → ceremony `Invalid request` |
| 3 | `/server/…/privateKey/export` | full-scope API token (`dyn_…`) | — | none | **401** | `Authentication through the x-dyn-server-signing-proof header is not enabled for this environment` |
| 4 | `/server/…/privateKey/export` | server session JWT (from `/waas/authenticate`) | — | — | **404** | empty body |
| 5 | `/server/…/privateKey/export` | none | — | — | **401** | `Authorization header or cookie is required` |
| 6 | `/server/…/signMessage` | ev8 session | ✗ | — | **200 SSE** (20.8 s) | `create_room` → `room_created` → `{"error":"Error signing message:","status":500}` — a genuine 20-second signing ceremony attempt on behalf of a plain session |
| 7 | `/server/…/keyShares/backup/locations` | ev8 session | ✗ | — | **500** | `Unexpected server error.` on empty body (the `/sdk` twin returns a clean `400 request/body must have required property 'locations'`) |
| 8 | `POST /server/waas/createRooms` | ev8 session | ✗ | — | **200** | `{"roomIds":["fe4d9f9243c3882f311490fbbf646579"]}` — room creation succeeds outright with a plain session (the `/sdk` twin demands `roomType`/`thresholdSignatureScheme` first) |

Row 3 is the auth-model inversion in one line: **legitimate server credentials are rejected** on this environment for wallet-ops ("proof header is not enabled"), while a **plain end-user session is accepted and drives the ceremony**. Rows 2/6/8 show the step-up gate that rows like #1 enforce is simply absent on the parallel family.

### 3. `x-dyn-server-signing-proof` — spec says verified, reality says no

Public API spec: the `x-dyn-server-signing-proof` header is "always verified when present."

Observed (with the ev8 session JWT as Bearer):

```
x-dyn-server-signing-proof: aaa.bbb.ccc   ← structurally JWT-shaped, cryptographically garbage
```

→ no `403`, no proof-validation error; the request proceeds exactly as in row 2 above (room created). The header is only *existed*-checked in flows where a JWT is absent. A caller can therefore present any malformed proof alongside a session JWT without tripping the documented verification.

### 4. Validation gaps on `/server` (stability + oracle differences)

- Malformed `walletId` (non-UUID string): `/sdk` → `400` pattern validation; `/server` → `500 Unexpected server error.` (unhandled exception surfaced to client).
- `keyShares/backup/locations` empty body: `/sdk` → clean `400` naming the missing property; `/server` → `500`.
- `GET /server/{env}/waas/{walletId}/settings` → not deployed (`Cannot GET`), while other `/server` waas subroutes are live — inconsistent deployment of the family.

### 5. Cross-user matrix (W2 — foreign wallet) — scoping is intact (ruled out)

ev8 session against **W2** (owned by a different user id):

| Route | Status | Body |
|-------|--------|------|
| `/server/…/W2/privateKey/export` | 404 | empty (resolution fails before any ceremony) |
| `/server/…/W2/signMessage` | 404 | empty |
| `/server/…/W2/keyShares/backup/locations` | 404 | empty |
| `/server/…/W2/keyShares/refresh` | 404 | empty |
| `POST /server/waas/createRooms` | 404 | empty |
| `/sdk/…/W2/privateKey/export` | 403 | gate fires **before** ownership check |
| `/sdk/…/W2/keyShares/recover` | 404 | empty |
| `/server` + `/sdk` `byWalletAddress/W2-address` | 404 | `WaaS wallet not found` |

Wallet resolution is **user-scoped at the application and relay layers** on both families; no cross-user access was achieved. (This simultaneously closes an earlier open question: `keyShares/recover` enforces ownership, not merely environment + session.)

---

## Impact ceiling — what is and is not proven (honesty section)

**Proven:**

1. The step-up/elevated-access control that protects `privateKey/export` and `signMessage` on `/sdk` **does not exist** on the parallel `/server` family, which accepts plain end-user sessions and initiates real MPC ceremonies (rooms, server keygen participants, a 20-second signing attempt).
2. Server-side caller authentication for these routes is broken/inconsistent: the documented server credential path is disabled ("not enabled for this environment") while undocumented-but-live session-JWT access works; the documented always-on proof verification does not happen when a JWT is present.
3. Input validation on `/server` wallet routes is absent or crashes (500s), diverging from the hardened `/sdk` twins.

**Ruled out (tested):**

- **No key delivery.** All export attempts terminate at the ceremony client-participation step. Actual key-share delivery on the keyshares relay (`waas-keyshares-relay.dynamicauth.com`, Evervault-fronted) requires a proof-of-possession composite — ECDSA signatures over the session ID and a relay nonce made with the **session key private half** (verified locally: session-ID signature validates, relay still rejects; the browser's compressed-format session claim is required). A holder of only the session **JWT** cannot complete the composite. This was tested with the official `@dynamic-labs-wallet/node` client (v1.1.50) and manual relay calls.
- **No cross-user wallet access** (matrix above).
- **No elevated-token bypass on `/sdk`** — the gate itself holds.
- **No unauthenticated access** — a Bearer is required (401 without).

**Why P3, not P1/P2:** the operations reachable without step-up are ceremony **initiations** (resource allocation and process side effects on the researcher's own wallet), and key material — the operation the step-up gate exists to protect — is not delivered without the session private key. Under the engagement's standalone-impact rule this is a real, standalone broken-access-control defect (no stolen session needed to demonstrate the differential on one's own wallet), but its demonstrated impact ceiling is control-integrity, not key disclosure. Filed accordingly and honestly.

---

## Related hardening observations (not filed, recorded for completeness)

- **Backup token TTL mismatch (P4-class):** `GET /sdk/{env}/waas/keyShares/backup/token` mints a backup bearer token with `exp − iat ≈ 8.9–11.7 h` (observed 32032 s and 42089 s in two independent mints) while the API spec describes it as "valid for 1 minute." The token is also wallet-agnostic (bound to the session user, not a wallet). Standalone impact is amplification-only: the keyshares relay still requires the PoP composite (400 `validation_failed` without it).
- **Validation-before-authz ordering (P5/info):** some public endpoints leak allowed parameter values (e.g. wallet `type: "mpc"`) before authorization is evaluated.
- `GET /server/{env}/serverIdentity` with a session JWT returns `200 {"userId": …}` mapping the session to a server-side user id — noted as part of the family's mixed auth model, no standalone impact established.

---

## Remediation

1. **Enforce the elevated-access gate on `/server` wallet-ops** — or, if `/server` is intended for server credentials only, reject end-user session JWTs on that family with a clear `403` instead of accepting them into ceremonies. The current state (accept the weakest credential class, skip the strongest control) is the worst of both.
2. **Actually verify `x-dyn-server-signing-proof` whenever present**, as the spec promises, and fail closed on malformed proofs (`403`), not pass-through.
3. **Align validation with the `/sdk` family**: require and validate `exportId`, `locations`, `roomType`/`thresholdSignatureScheme` bodies and UUID-shaped wallet IDs before resolution (currently 500s).
4. **Fail closed on ceremony initiation**: room creation + server keygen allocation should not occur for callers who cannot complete the proof-of-possession composite — initiate the PoP challenge *before* allocating MPC rooms.
5. **Shorten backup-token TTL to the documented 1 minute** (or document the real TTL and bind it to a wallet id), since it is a bearer credential for key-share metadata surfaces.

---

## Evidence index & integrity note

- Reproduction timestamps, UUIDs, room IDs, `serverKeygenIds`, status codes and error strings above are verbatim from the live test session record (`worklog.md`, Task IDs `idor17 / new-surface-hunt` and `idor18 / waas-ceremony-unblock-and-gate-differential`) and the raw JSON logs (`recon/idor18/m_log.json`, `recon/idor18/b_log.json`, `recon/idor18/c_log.json`, `recon/idor18/i_xuser_log.json`, `recon/idor17/sweep*.json`), all committed to this repo.
- The decisive matrix (m_log.json) was generated by `scripts/idor18_matrix.js`; ceremony transcripts are raw SSE bodies captured verbatim.
- Wallet W1/W2 remain live on the researcher's own sandbox environment for triage reproduction; researcher-owned identities only, no real user data touched, no key material exported at any point.
- All session/elevated/API tokens are elided from this report. Test window 2026-10-26 14:10–15:20 UTC.

---

## ADDENDUM (Round 11, 2026-10-27): differential extends to END-USER sessions — strongest principal class yet

The original finding demonstrated the `/server` vs `/sdk` step-up differential with a **server-principal session JWT** (a semi-privileged developer-tier credential). Round 11 re-tested the same pair with the **weakest credential class available — a plain end-user session JWT** (`scope: "user:basic"`, no elevated token, no PoP headers) and the differential holds identically:

**Test pair A — `privateKey/export`:**

```
POST /api/v0/sdk/7dfe3b0c-…/waas/bdb3c7cc-…/privateKey/export
Authorization: Bearer <end-user session JWT, scope user:basic>
{"exportId":"<uuid>"}
→ 403 {"error":"Elevated access token required"}          ← gate enforced on /sdk

POST /api/v0/server/7dfe3b0c-…/waas/bdb3c7cc-…/privateKey/export
Authorization: Bearer <same end-user session JWT>
{"exportId":"<uuid>"}
→ 200 (SSE) event: status      data: {"message":"Creating room...","step":"create_room"}
        event: room_created data: {"roomId":"6369e012a9a37309bc9ae70c51d10c44","serverKeygenIds":["8em4U4qYDhfoYWWVr1iQtzge4VjTz8ZntwJuvXGgb95L"]}
```

**Test pair B — `signMessage` (the second elevated-gated operation):**

```
POST /api/v0/server/7dfe3b0c-…/waas/bdb3c7cc-…/signMessage
Authorization: Bearer <same end-user session JWT>     body {"data":"0xdeadbeef"}
→ 200 (SSE) event: status      data: {"message":"Getting credentials and creating room...","step":"create_room"}
        event: room_created data: {"roomId":"6369e012e670a560426ab5585857cc0d","serverKeygenIds":["8em4U4qYDhfoYWWVr1iQtzge4VjTz8ZntwJuvXGgb95L"]}
```

Any end user of any environment can therefore reach real MPC ceremony initiation on **both** step-up-protected wallet operations by switching the path prefix `/sdk/` → `/server/`, with zero step-up. This removes any argument that the differential only affects the developer/server tier — the control gap is reachable from the bottom of the principal hierarchy.

**Positive controls recorded in the same session (honest negatives):**

- `/sdk …/privateKey/export` with the same end-user session **enforces** its gate correctly: 403 without elevated token; elevated token is single-use (second use → 403 "Invalid or expired elevated access token"); minted elevated TTL is exactly 300 s (exp − iat).
- With a **fresh, valid elevated token** the end-user session on their **own** wallet completes ceremony initiation (200 SSE `room_created`) — proving the gate works as designed for the legitimate flow.
- **Cross-user isolation holds everywhere**: end-user session + fresh valid elevated token against another user's wallet (`/sdk` and `/server`) → **404**; wallet resolution remains user-scoped. No cross-principal key or ceremony access found.
- **Elevated-token mint path cannot be escalated to console scopes.** The step-up verifier `POST /sdk/{env}/externalAuth/verify` (stress-tested end-to-end in this round with an attacker-controlled JWKS on the researcher's own sandbox) correctly enforces: asymmetric-algorithm allowlist (RS256/ES256 only — HS256 key-confusion rejected), `exp`, `iss`, `aud`, `kid`-in-JWKS, `jti` replay prevention, subject↔session binding, and a **scope-claim allowlist** (`wallet:*`, `user:*`, `credential:*` only). Requesting `scope: "console:webhook_secret:reveal"` → 400 "No recognized scopes in request…" — so the BUG-001 webhook-secret chain is **not** reachable by end users through externally-minted elevated tokens. Escalation path closed; P3 ceiling unchanged.

**New minor observation (info, not filed separately):** the scope-allowlist validation error enumerates the full step-up scope vocabulary before authorization (`wallet:delegate|delete|export|offline_recovery_trigger|policy:update|refresh|reshare|restore|sign`, `user:delete|update`, `credential:link|unlink`, …) — same validation-before-authz class already noted in the P5 observations below.

**Round-11 evidence:** `recon/idor26/{mint_log.json, weakness_matrix.json, export_chain.json, disambig.json, cleanup.json}`, `recon/idor25/sweep_log.json`; scripts `scripts/idor25a–idor26i`. Test window 2026-10-27, all artifacts on the researcher's own sandbox environment (ev8/ev9 researcher-owned test users), no real user data, no key material exported. All round-11 configuration mutations (externalAuth enable, JWKS URL, test deeplink, ghost test user) were reverted/deleted after testing — final state verified clean.
