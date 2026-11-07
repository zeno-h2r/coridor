## Title
API token accepted as URL query parameter (credential exposure in logs/traces/history) — all API planes

## Severity
P3 (recommended)

## Weakness
CWE-598 — Use of GET Request Method With Sensitive Query Strings (sensitive credential in query string)

## Summary
The QE API authenticates requests when the **long-term API token** (`id:secret`) is supplied as a **URL query parameter** (`?token=`), with no headers required. This works on every API plane: the Rails `/api/v1` API (reads AND writes), the Fastify file service, and the `we_*` workflow service. Only the param name `token` is accepted (5 other credential param names were tested and rejected).

Because the token is a permanent, non-expiring credential granting full API read/write to the account, accepting it in URLs places that credential in every URL-capturing system: web/proxy/CDN access logs, APM/OpenTelemetry traces (the app emits `traceparent`), browser history, `Referer` headers, log aggregation, and support tooling. Any capture = full account compromise via the token.

## Steps to reproduce

1. Authenticated read with **zero headers** — token only in URL:

```bash
curl -s "https://bugbounty1.qe.optrostaging.ai/api/v1/users/230?token=<id:secret>"
# → 200 full profile
```

2. Authenticated **write** via query token (no-op on own account):

```bash
curl -s -X PUT \
  "https://bugbounty1.qe.optrostaging.ai/api/v1/users/230?token=<id:secret>" \
  -H "Content-Type: application/json" \
  -d '{"user":{"locale":null}}'
# → 200
```

3. Workflow plane via query token:

```bash
curl -s "https://bugbounty1.qe.optrostaging.ai/api/v1/we_tasks?token=<id:secret>"
# → 200
```

4. Control without any token: → `401 Missing authentication`.

## Impact
- Permanent credential (`id:secret`, does not expire) persisted in plaintext across all URL-logging infrastructure (origin logs, CDN/WAF logs, OTel traces, SIEM/log shippers).
- Token grants full API read/write for the account — a captured URL equals full account compromise (the same write surface enables the account-takeover chain reported separately in BUG-008).
- Exposure window is unlimited until manual rotation.

## Remediation
1. Remove the `params[:token]` authentication fallback on all three API planes; enforce header-only transport.
2. Reject query-string credentials with an explicit error during migration.
3. Rotate tokens that may already be captured in logs/traces.
