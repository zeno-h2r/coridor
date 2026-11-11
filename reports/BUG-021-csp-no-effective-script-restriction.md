# BUG-021: Content-Security-Policy provides no effective script restriction (`script-src *` + `unsafe-inline` + `unsafe-eval`)

**Program:** Optro Managed Bug Bounty (private)
**Reporter:** zeno0 (zeno0@bugcrowdninja.com)
**Asset:** `https://bugbounty1.qe.optrostaging.ai`
**Build tested:** app_version **47.3.0-dev**, deployed 2026-11-10T17:56:45Z
**Date:** 2026-11-11
**Severity recommendation:** **P4 — defence-in-depth weakness (no standalone exploit demonstrated)**
**Header on all requests:** `X-Optro-Bug-Bounty: zeno0`

---

## 1. Summary

The enforced `Content-Security-Policy` header on every API and application response permits arbitrary script execution:

```
content-security-policy: default-src *; script-src * 'unsafe-inline' 'unsafe-eval' blob: data:;
  connect-src * data:; style-src * 'unsafe-inline'; img-src * file: data: blob:;
  font-src * data:; frame-src * blob:; frame-ancestors 'self'; media-src * data:;
  worker-src * blob:; report-uri https://abcsp.report-uri.com/r/t/csp/reportOnly;
```

`script-src *` combined with `'unsafe-inline'` and `'unsafe-eval'` means the policy blocks nothing: any origin can serve script, inline script runs, and `eval` works. `object-src` and `base-uri` are absent entirely.

A second, **report-only** policy exists and is far stricter (`script-src 'self' ...`). The strict policy is not enforced — only reported.

**This is a defence-in-depth finding.** I could not demonstrate an XSS that exploits it (see §4). It is reported because it removes the last line of defence for any future injection bug in a large application.

---

## 2. The two policies

| header | mode | script-src |
| --- | --- | --- |
| `content-security-policy` | **enforced** | `* 'unsafe-inline' 'unsafe-eval' blob: data:` |
| `content-security-policy-report-only` | report only | `'self' 'unsafe-inline' 'wasm-unsafe-eval' blob: <named CDNs>` |

The strict policy is correctly scoped — `default-src 'none'`, `base-uri 'self'`, `object-src 'none'`, a named allowlist of CDNs. **It is simply not the one being enforced.** The two appear to have been swapped, or the strict one was never promoted from report-only.

---

## 3. Verification

```bash
H="https://bugbounty1.qe.optrostaging.ai"

curl -s -i -X POST "$H/api/v1/risks" \
  -H "token: <token>" -H "Content-Type: application/json" \
  -H "X-Auditboard-Product: System" \
  -d '{"risk":{"name":"probe"}}' \
  | grep -i '^content-security-policy'
```

Observed (enforced policy):

```
content-security-policy: default-src *; script-src * 'unsafe-inline' 'unsafe-eval' blob: data:; ...
```

Programmatic checks against the enforced header:

```
script-src *                      True
'unsafe-inline' in script-src     True
'unsafe-eval' in script-src       True
object-src missing                True
base-uri missing                  True
default-src *                     True
```

---

## 4. What was tested and did NOT work (honest negatives)

I attempted to weaponise this and could not. The application has independent defences that hold:

| vector | result |
| --- | --- |
| Stored XSS via `controls` name/description/notes/custom_text | **entity-encoded on write** — stored as `&lt;img src=x onerror=...&gt;` |
| Stored XSS via `risks` name | **entity-encoded on write** — `&lt;b&gt;...&lt;/b&gt;` |
| Stored XSS via `narratives` name | **entity-encoded on write** |
| Browser DOM verification (controls tree, live app) | `rawImgTagInHtml=false`, `badImgs=0` — renders as literal text |
| AI output path (`generative/dynamic-schema`) emitting raw HTML | **model strips tags** — `<img>`, `<svg>`, `<script>` all removed |
| WAF bypass for `<svg>`, `<script>`, `{{` (14 encodings) | **all 403** — entity, hex-entity, null-byte, case, whitespace, comment, UTF-7, overlong |
| Reflected XSS in query params (12 endpoints × 15 payloads) | **clean** — no reflection, no status anomaly |

**No XSS was achieved.** The CSP weakness is latent.

---

## 5. Impact

- **No defence-in-depth for script injection.** The application currently escapes HTML on write, which is the primary control. If any future or undiscovered field skips that escaping — a new feature, a rich-text field, an import path, an admin-only field, a third-party widget — the CSP will not stop the resulting script from executing.
- **`unsafe-eval` permits string-to-code execution**, which widens the impact of any DOM-XSS or prototype-pollution primitive that reaches `eval`/`Function`.
- **`object-src` and `base-uri` absent** allows plugin-based and base-tag hijacking vectors that a correct policy blocks.
- **`connect-src * data:`** permits exfiltration to any origin from any script that runs.
- The strict policy already exists and is correctly written — this is a deployment/configuration gap, not a design gap.

**Honest ceiling:** this is **P4**. There is no demonstrated exploit chain. The program excludes "Missing HTTP security headers" as a standalone submission, and a weak-but-present CSP is close to that category. I am reporting it as a defence-in-depth observation, not as an exploitable vulnerability, and it should be triaged accordingly.

---

## 6. Remediation

1. Promote the report-only policy to enforced: swap the two headers so `content-security-policy` carries the strict policy.
2. Remove `'unsafe-inline'` from `script-src` (use nonces or hashes) and `'unsafe-eval'` (refactor the code paths that need it).
3. Add `object-src 'none'` and `base-uri 'self'` to the enforced policy.
4. Restrict `connect-src` and `img-src` to the named allowlist already present in the report-only policy.
5. Keep the permissive policy only as a report-only shadow during rollout, then remove it.

---

## 7. Evidence / cleanup

- Read-only header inspection plus the injection attempts documented in §4.
- Test objects created during the sweep are disclosed in the engagement worklog.
- Disclosed from this engagement: files 2712/2726/2730/2732 deleted (BUG-015); issue 121 status changed; narrative 67 created; risk/narrative names modified (BUG-019); attachments 11207–11220 generated; several account emails changed during BUG-017 and left in place at the operator's instruction; risks 306–312, 313, 367, 369 and narratives 68–69 created with test payloads.
