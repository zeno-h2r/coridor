# BUG-002 — hCaptcha secretKey (spec-declared "never surfaced in a GET response") returned in plaintext by GET /environments/{environmentId}, including to viewer-role members

- **Target:** Dynamic Labs Managed Bug Bounty (`app.dynamic.xyz` / `app.dynamicauth.com`)
- **Researcher:** zeno0 (zeno0@bugcrowdninja.com)
- **Date:** 2026-10-26
- **Suggested severity:** P4 (Sensitive Data Disclosure / Broken Access Control — least-privilege violation; argued up given explicit spec promise)
- **VRT:** Broken Access Control → Sensitive Data Disclosure

---

## Summary

The public OpenAPI spec makes an **explicit, absolute confidentiality promise** for the hCaptcha validation secret:

> `HCaptchaSettings.secretKey` — "Secret key used to validate captcha response. **This will never be surfaced in a GET response.**"

The dedicated captcha settings endpoints honor this promise: they return only a `hasSecretKey` boolean and document that "The secret itself is encrypted at rest and never returned."

However, the primary environment-detail route **`GET /api/v0/environments/{environmentId}`** returns the raw secret in plaintext inside the (deprecated but still populated) embedded `settings.security.hCaptcha` object:

```json
"hCaptcha": { "enabled": false, "secretKey": "fake-secret-key-456", "siteKey": "fake-site-key-123" }
```

The disclosure reaches **viewer-role organization members** — the least-privileged console role. This is the same unintended-behavior class as BUG-001 (spec-declared protection not enforced), on a second credential type. While BUG-001's webhook signing secret enabled a full forgery chain (P2), this one exposes the customer's captcha-validation credential.

## Why this is not "expected viewer read"

The program's false-positive rule excludes GET endpoints readable by viewer as intended behavior. This endpoint fails that exclusion test because:

1. **The spec itself forbids it.** "This will never be surfaced in a GET response" leaves no room for role-based exceptions.
2. **Sibling endpoints enforce masking for the same secret.** `GET/POST/PUT /environments/{environmentId}/settings/captcha` return `hasSecretKey` only; the dashboard uses those endpoints precisely because the secret must never round-trip to any client.
3. **Contrast within the same response.** The modern `settings.security.captcha` object in the identical response body correctly omits the secret — only the legacy `settings.security.hCaptcha` object leaks it. This is a masking gap in one serializer, not a design decision.

## Steps to Reproduce

All requests carry `X-Request-Purpose: Research` and `X-Bugcrowd-Ninja: zeno0`.

**Setup (org owner, own environment):** configure captcha with the hCaptcha provider and a known secret (here a canary value `fake-secret-key-456`, set by the researcher — evidence integrity: no third-party secret was involved).

**1. Owner view (baseline):**

```bash
curl "https://app.dynamicauth.com/api/v0/environments/{environmentId}" \
  -H "Authorization: Bearer <owner JWT>" \
  -H "X-Request-Purpose: Research" -H "X-Bugcrowd-Ninja: zeno0"
# → 200; settings.security.hCaptcha.secretKey = "fake-secret-key-456" (plaintext)
```

**2. Viewer-role member (least privilege):**

```bash
curl "https://app.dynamicauth.com/api/v0/environments/{environmentId}" \
  -H "Authorization: Bearer <viewer-role member JWT>" \
  -H "X-Request-Purpose: Research" -H "X-Bugcrowd-Ninja: zeno0"
# → 200; identical plaintext secretKey
```

Viewer membership was obtained through the normal invite + accept flow (role `viewer`, confirmed via `GET /organizations/{orgId}/members`). Evidence artifacts: `recon/idor5/t8_final_evidence.txt` (captured 2026-10-26T10:37:59Z), and the independent round-3 artifact `recon/idor3/final/env_detail.body` — both viewer responses contain the raw secret.

**3. Control — dedicated captcha endpoint masks correctly:**

```bash
curl "https://app.dynamicauth.com/api/v0/environments/{environmentId}/settings/captcha" \
  -H "Authorization: Bearer <owner JWT>" \
  -H "X-Request-Purpose: Research" -H "X-Bugcrowd-Ninja: zeno0"
# → 200 {"enabled":false,"provider":"hcaptcha","siteKey":"fake-site-key-123"} — hasSecretKey-family response, NO secret
```

**4. Control — unauthenticated SDK view excluded:**

```bash
curl "https://app.dynamicauth.com/api/v0/sdk/{environmentId}/settings" \
  -H "X-Request-Purpose: Research" -H "X-Bugcrowd-Ninja: zeno0"
# → 200; contains siteKey (public) but NOT secretKey — 236 fields properly excluded
```

**5. Control — outsider cross-tenant blocked:**

```bash
curl "https://app.dynamicauth.com/api/v0/environments/{victimEnvironmentId}" \
  -H "Authorization: Bearer <non-member JWT>" ...
# → 403 "Environment not found"
```

## Impact

- **Who can exploit:** any organization member of role viewer, developer, admin (and owner) — i.e., every console role. A compromised or malicious low-privilege member (contractor, support staff, auditor) can exfiltrate the captcha validation secret with a single GET. The exact threat model step-up authentication exists for (BUG-001): session theft or insider overreach.
- **What the secret enables:** the hCaptcha secretKey is the server-side credential for `siteverify` — the enforcement primitive behind captcha-protected signup/login/transaction flows. Customers commonly reuse the same hCaptcha site/secret pair on their production properties. Disclosure enables (a) offline captcha-token validation for relayed/scaled abuse tooling against the customer's captcha-protected endpoints, (b) use of hCaptcha enterprise features keyed to the secret, and (c) cross-environment credential reuse exposure.
- **No rotation path surfaced:** as with BUG-001's webhook secret, the 525-operation spec exposes no self-service rotate operation for the captcha secret (only update via PUT with a new value — which requires the very admin access an insider already holds; the leaked value itself never needs to be re-derived).
- **Systemic pattern:** combined with BUG-001 (P2 — webhook signing secret revealed without step-up), this shows the console's secret-masking layer is enforced inconsistently per serializer: dedicated settings routes mask correctly; embedded legacy objects in composite responses do not. Any other secret riding a legacy embedded object (captcha today, potentially others) is exposed by the same route.

## Remediation

1. Strip `settings.security.hCaptcha.secretKey` from the `GET /environments/{environmentId}` serializer (mirror the modern `security.captcha` object, which already omits it).
2. Audit all composite response serializers for additional write-only fields leaking through legacy embedded objects (the spec already tags `x-write-only` intent in places).
3. Optionally honor the spec promise at the schema layer so the guarantee cannot regress.
