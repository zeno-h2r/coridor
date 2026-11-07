# BUG-011 — Long-Term API Token Accepted as URL Query Parameter Across All API Planes (CWE-598)

**Program:** Optro Managed Bug Bounty (AuditBoard QE staging) — `https://bugbounty1.qe.optrostaging.ai`
**Reporter:** zeno0 (zeno0@bugcrowdninja.com)
**Severity recommendation:** P3
**Weakness:** CWE-598 (Use of GET Request Method With Sensitive Query Strings) / credential exposure via query string

---

## Summary

The AuditBoard QE API accepts the **long-term, non-expiring API token** (`id:secret` scheme) as a **URL query parameter** (`?token=`) — with **no headers required at all**. The same acceptance exists on all three API planes behind the gateway:

| Plane | Example endpoint | Query-token auth result |
|---|---|---|
| Rails API (`/api/v1/*`) | `GET /api/v1/users/230?token=...` | 200 — authenticated |
| Rails mutations | `PUT /api/v1/users/230?token=...` | 200 — **authenticated write** |
| Rails metadata | `GET /api/v1/roles?token=...` | 200 — authenticated |
| Fastify file service | `GET /api/v1/files/{id}?token=...` | Auth passes (reaches model lookup) |
| `we_*` workflow service | `GET /api/v1/we_tasks?token=...` | 200 — authenticated |

The API token is a **permanent credential** (observed non-expiring across multiple days; invalidation only via manual rotation). Accepting it in query strings places the full-privilege credential into every system that records URLs: web server access logs, reverse-proxy/CDN logs, APM/OTel traces (the application emits `traceparent` headers — traces carry full URLs), browser history, `Referer` headers on any outbound navigation, log aggregation/SIEM pipelines, and support tooling. Any single capture of a query-token URL = full account compromise via the token.

## Copyable proof

**1. Authenticated read via query parameter — no headers, no auth header:**

```bash
curl -s "https://bugbounty1.qe.optrostaging.ai/api/v1/users/230?token=<id:secret>"
# → 200, full user profile (Bugcrowd Tester34)
```

**2. Authenticated MUTATION via query parameter (no-op write on own account):**

```bash
curl -s -X PUT \
  "https://bugbounty1.qe.optrostaging.ai/api/v1/users/230?token=<id:secret>" \
  -H "Content-Type: application/json" \
  -d '{"user":{"locale":null}}'
# → 200 (write accepted)
```

**3. Workflow plane via query parameter:**

```bash
curl -s "https://bugbounty1.qe.optrostaging.ai/api/v1/we_tasks?token=<id:secret>"
# → 200 {"we_tasks":[], ...}
```

**4. Param-name matrix (only `token` accepted — all others 401):**

```
token=...          → 200 (authenticated)
api_token=...      → 401
auth_token=...     → 401
access_token=...   → 401
user_token=...     → 401
session_token=...  → 401
```

**5. Control (no credentials):** `GET /api/v1/users/230` without token → `401 Missing authentication`.

## What this is NOT (honest scoping)

- Not claiming token brute-force feasibility (token space is large).
- Not claiming in-app Referer leakage was demonstrated — the exposure is the transport-level acceptance of the credential in URLs and its persistence in any URL-logging system the operator/tenants run.
- Not a bypass of the auth layer itself: valid token + valid user is still required.
- The `X-Optro-Bug-Bounty` / `X-Auditboard-Product` headers are **not** part of authentication (requests with only `?token=` and zero custom headers succeed) — noted to avoid confusion during triage; those headers were never security controls.

## Impact

- Any system that logs full URLs (origin access logs, CDN/WAF logs, OTel traces — `traceparent` confirmed on outbound AI-service calls — APM dashboards, log shippers) captures the permanent `id:secret` credential in plaintext.
- Downstream compromise is total for the token's account: the token grants full API read/write (proven with a mutation above, and per BUG-008 the user-record write surface enables account takeover chains).
- Exposure persists indefinitely because the token does not expire.

## Remediation

1. Remove the `params[:token]` fallback from the authentication filter chain (all three planes — Rails, Fastify file service, workflow service) and enforce header-only token transport.
2. Reject requests carrying credentials in query strings with a clear error, so clients fail loudly during migration.
3. Treat any tokens that may already appear in operator logs/traces as exposed and rotate them.
