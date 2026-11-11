# BUG-023: HTML injection in comments — server allowlist permits `div`/`table`/`h1`/`img` and a cosmetic CSS subset

**Program:** Optro Managed Bug Bounty (private)
**Reporter:** zeno0 (zeno0@bugcrowdninja.com)
**Asset:** `https://bugbounty1.qe.optrostaging.ai`
**Build tested:** app_version **47.3.0-dev**, deployed 2026-11-10T17:56:45Z
**Date:** 2026-11-11
**Severity recommendation:** **P4 — HTML injection, no script execution, no UI redress**
**Header on all requests:** `X-Optro-Bug-Bounty: zeno0`

---

## Access — how to reproduce

```
Login to : zx-sysadm-66650c74@bugcrowdninja.com
Password  : TesterZx2026!
Role      : System Admin (role_id 2)
Navigate  : https://bugbounty1.qe.optrostaging.ai/workspace/12/exceptions/33
```

Header on every request: `X-Optro-Bug-Bounty: zeno0`

Open **Comments**, post the payload, then inspect the DOM.

---

## 1. Summary

`POST /api/v1/comments` accepts a caller-supplied `message_html`. The server re-sanitises it against an allowlist, but that allowlist is **much wider than the client's** and permits structural tags plus a subset of CSS.

Verified live: comment **967** renders a real `<div style="width:100%;height:100%;background:red">` in the thread (measured height 18.57px), and comment **968** a `<span style="font-family:x">`.

**This is HTML injection, not XSS.** Every script-execution vector is blocked at two layers, and every dangerous CSS layout property is stripped. Reported for completeness with an honest P4 rating.

---

## 2. What the server allowlist permits

Sent as `message_html`, read back after server sanitisation:

| tag | result |
| --- | --- |
| `b`, `i`, `u`, `strong`, `em` | kept |
| `span`, `div`, `p`, `br` | kept |
| `h1`, `table`/`tr`/`td`, `ul`/`li`, `code`, `pre`, `blockquote` | **kept** |
| `img` (src attribute) | kept as `<img />` — `src` stripped |
| `a` (href) | tag stripped, text kept |
| `form`, `input` | stripped entirely |

CSS properties that **survive** on `div`/`span`:

```
display:block        width:300px        height:100px
background:red       margin:-500px      font-family:x
width:9999px;height:9999px
```

CSS properties that are **stripped**:

```
position:absolute    z-index:99999      opacity:0
transform:...        visibility:hidden  overflow:hidden
pointer-events:none  mix-blend-mode     clip-path
filter:blur()        content:"x"        background-image:url()
```

---

## 3. Reproduction

```bash
H="https://bugbounty1.qe.optrostaging.ai"
BB="X-Optro-Bug-Bounty: zeno0"

T=$(curl -s -X POST "$H/api/v1/users/login" -H "$BB" \
  -H "Content-Type: application/json" \
  -d '{"credentials":{"email":"<user>","password":"<pw>"}}' \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["session"]["token"])')

curl -s -X POST "$H/api/v1/comments" -H "token: $T" -H "$BB" \
  -H "Content-Type: application/json" -H "X-Auditboard-Product: System" \
  -d '{"comment":{"type":"Comment","commentable_type":"ExceptionRequest",
       "commentable_id":33,
       "message_raw":"<div style=\"width:100%;height:100%;background:red\">ZX</div>",
       "message_html":"<div style=\"width:100%;height:100%;background:red\">ZX</div>"}}'
```

→ `200`, and the stored `message_html` is:

```
<div style="width:100%;height:100%;background:red">ZX</div>
```

**DOM proof** (comment 967 in the live thread):

```json
{"style":"width:100%;height:100%;background:red",
 "text":"ZXZXC2b956",
 "rect":18.5703125}
```

A real element with an attacker-controlled `style` attribute, rendered in the comment body.

---

## 4. What was tested and did NOT work (honest negatives)

| vector | result |
| --- | --- |
| `<img src=x onerror=...>` | **403** at the edge WAF |
| `<svg onload>`, `<script>`, `<iframe>`, `<style>`, `<math>`, `<base>`, `<meta>` | **403** WAF |
| `onerror` / `onload` / `onclick` / `onfocus` / `ontoggle` / `onstart` on any tag | **403** WAF |
| `<img/src=x/onerror=...>` (slash syntax, passes WAF) | server sanitizer strips to `<img />` |
| `javascript:` in href (plain, entity, `&colon;`, tab, newline, null, case) | WAF 403 or sanitizer strips the anchor |
| `position:absolute` / `z-index` / `opacity:0` / `transform` / `visibility:hidden` / `pointer-events:none` / `clip-path` / `filter` | **stripped** — no UI redress |
| `background-image:url(attacker)` | **stripped** — no CSS exfiltration |
| `width:expression(alert(1))` | **403** WAF |
| `message_raw` rendered as HTML | **no** — `commentParagraphs` splits it and renders as text |

**No script execution was achieved by any route.**

---

## 5. Impact

- **Cosmetic HTML injection in a shared comment thread.** An attacker who can comment can insert structural markup and a limited CSS subset: coloured blocks, oversized elements, arbitrary fonts.
- **Content spoofing.** A `div` with `background:red` and attacker text inside a comment can be styled to resemble a warning or system message.
- **No script execution, no UI redress, no data exfiltration.** `position`, `z-index`, `opacity`, `transform` and `background-image:url()` are all stripped, so an attacker cannot overlay the page, hide real content, or beacon out via CSS.

**Honest ceiling:** this is **P4**. The program excludes "Functional, UI, UX bugs" and HTML injection without script execution is close to that line. I am reporting it as an observation with the allowlist mapped, not as an exploitable vulnerability.

---

## 6. Remediation

1. Tighten the server allowlist to the same set the client uses: `a`, `span`, `br`, `strong`, `hr` (per the bundle's `ALLOWED_TAGS`).
2. Drop `style` from `ALLOWED_ATTR` entirely, or restrict it to a strict property allowlist (`color`, `font-weight`) with value validation.
3. Remove `img`, `table`, `h1`, `div`, `pre`, `blockquote` unless a product requirement justifies them — each widens the spoofing surface.
4. Keep the edge WAF as defence-in-depth, but do not rely on it: the slash-syntax bypass (`<img/src=x/onerror=>`) already defeats its tag matching.

---

## 7. Evidence / cleanup

- **Test artifacts:** comments 940–968 on `ExceptionRequest` 33 contain allowlist probes and the live CSS-injected divs (966, 967, 968). All inert; no script executes.
- Exception 33 title is `&lt;b&gt;ZXAUDITZXA19307&lt;/b&gt;` (encoded, from the audit-log test).
- Disclosed from this engagement: files 2712/2726/2730/2732 deleted (BUG-015); issue 121 status changed; narrative 67 created; risk/narrative names modified (BUG-019); attachments 11207–11220, 11252–11254 generated; several account emails changed during BUG-017 and left in place at the operator's instruction.
- **BUG-022 (stored XSS in comments) is RETRACTED** — that claim did not survive verification.
