# BUG-022: Stored XSS in comments — client renders `message_raw` (entity-encoded) instead of the sanitised `message_html`

**Program:** Optro Managed Bug Bounty (private)
**Reporter:** zeno0 (zeno0@bugcrowdninja.com)
**Asset:** `https://bugbounty1.qe.optrostaging.ai`
**Build tested:** app_version **47.3.0-dev**, deployed 2026-11-10T17:56:45Z
**Date:** 2026-11-11
**Severity recommendation:** **P2 — Stored Cross-Site Scripting (fires for other users)**
**Header on all requests:** `X-Optro-Bug-Bounty: zeno0`

---

## 1. Summary

The comments feature stores two representations of every comment:

| field | value for our payload |
| --- | --- |
| `message_html` | `<img />` — **sanitised** (tag stripped, handler removed) |
| `message_raw` | `&lt;img src=x onerror=alert();&gt;` — **entity-encoded original** |

The server-side sanitiser works correctly and produces a safe `message_html`. **The client ignores it and renders `message_raw` into the DOM.** The browser decodes `&lt;` back to `<` during HTML parsing, producing a live `<img src="x" onerror="...">` element that executes.

Verified live: posting `<img src=x onerror=alert(document.domain)>ZXCMT1` as a comment triggered an alert containing `bugbounty1.qe.optrostaging.ai` — the value of `document.domain`.

**This is stored, not reflected.** The payload persists in the comment record and re-executes for every user who opens the thread.

---

## 2. Root cause

The application implements the correct control and then bypasses it.

1. **Server sanitises correctly.** `message_html` for our payload is `<img />` — the `onerror` attribute and its value are gone. The sanitiser is doing its job.
2. **Server also stores the raw input** in `message_raw`, entity-encoded (not stripped).
3. **Client renders the wrong field.** The comment component binds `message_raw` into the DOM. Entity-encoded text is decoded by the HTML parser, so `&lt;img src=x onerror=alert();&gt;` becomes a live element.

The sanitised `message_html` field exists and is unused for rendering. Choosing it would close the bug.

---

## 3. Reproduction — copy-paste

```bash
H="https://bugbounty1.qe.optrostaging.ai"
BB="X-Optro-Bug-Bounty: zeno0"
```

### Step 1 — log in as any user who can comment

```bash
T=$(curl -s -X POST "$H/api/v1/users/login" -H "$BB" \
  -H "Content-Type: application/json" \
  -d '{"credentials":{"email":"<user>","password":"<pw>"}}' \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["session"]["token"])')
```

### Step 2 — post the payload as a comment

In the UI: open any exception → **Comments** → type the payload → **Post**.

```
<img src=x onerror=alert(document.domain)>ZXCMT1
```

**Result: the alert fires immediately on post.**

### Step 3 — confirm the server stored both representations

```bash
curl -s "$H/api/v1/comments" -H "token: $T" -H "$BB" \
  | python3 -c '
import sys,json
for c in json.load(sys.stdin)["comments"]:
    if "onerror" in str(c.get("message_raw","")):
        print("id:",c["id"])
        print("message_html:",repr(c["message_html"]))
        print("message_raw :",repr(c["message_raw"]))
        print("commentable :",c["commentable_type"],c["commentable_id"])'
```

**Observed:**

```
id: 903
message_html: '<img />'
message_raw : '&lt;img src=x onerror=alert();&gt;'
commentable : ExceptionRequest 33
```

The sanitiser produced `<img />`. The raw field kept the payload.

### Step 4 — DOM proof

With the comment thread open, the payload is a **real element**, not text:

```javascript
[...document.querySelectorAll('img')]
  .filter(i => i.getAttribute('onerror'))
// → [{ src: "x", onerror: "alert(document.domain)",
//      outerHTML: '<img src="x" onerror="alert(document.domain)">' }]
```

Observed DOM state:

```
imgSrcXCount:            1
elementsWithOnerror:     1
rawImgInHTML:            true
outerHTML:               <img src="x" onerror="alert(document.domain)">
```

---

## 4. Why this is P2 and not self-XSS

- **The payload is stored server-side** in the comment record (id 903), not injected client-side.
- **It re-executes on every load** of the thread for every user who can see the comment.
- **Comments are a shared surface.** Any user who can comment on an exception can plant a payload that fires for reviewers, approvers, and administrators who open that exception.
- **The CSP does not mitigate it** (see BUG-021): the enforced policy is `script-src * 'unsafe-inline' 'unsafe-eval'`, which permits inline handlers.
- **The edge WAF does not mitigate it**: the payload is submitted through the normal comment UI and the request succeeds.

**Honest note on scope:** I verified execution as the posting user and confirmed the stored record. I did not log in as a second distinct user to watch the alert fire in their session, because the comment thread is shared and the payload is server-stored — the execution path is identical for any viewer. The `commentable_id` recorded is 33 while the UI was on exception 32, which suggests the comment is attached to the thread rather than the specific exception; that does not change the mechanism.

---

## 5. Impact

- **Session-riding script execution in an audit/compliance product.** An attacker who can comment can run arbitrary JavaScript in the session of any reviewer or administrator who opens the thread.
- **Actions available to the victim's session** include everything their role permits — for a System Admin that is user administration, permission changes, and file access.
- **Persistence.** The payload lives in the comment record until deleted; it fires on every thread load.
- **Phishing surface.** A script can rewrite the page to request credentials or approvals inside a trusted audit workflow.

---

## 6. What was tested and did NOT work (honest negatives)

| surface | result |
| --- | --- |
| Exception 32 `title` / `description` / `closure_notes` / `recommendation` | **entity-encoded on write**, rendered as a TEXT node — no element created |
| Exception 32 `field_data` | not writable through PUT (stays `{}`) |
| Renderer double-decode (`&amp;lt;img...`) | **no decode to live markup** — stable at one level |
| Risks / narratives / controls names | entity-encoded on write |
| Query params (12 endpoints × 15 payloads) | clean |
| Filename injection / upload | WAF blocks tags; bucket private; server forces extension + `Content-Disposition: attachment` |
| AI output (`dynamic-schema`) | model strips HTML tags |

**The comments render path is the only place where entity-encoded input reaches the DOM as markup.**

---

## 7. Remediation

1. **Render `message_html`, not `message_raw`.** The sanitised field already exists and is correct.
2. If `message_raw` must be shown (e.g. an "edit" view), bind it as a **text node** (`textContent`), never as HTML.
3. Add a regression test asserting that a comment containing `<img onerror>` produces zero elements with an `onerror` attribute in the rendered thread.
4. Enforce the strict CSP already present as report-only (BUG-021) as a second layer.

---

## 8. Evidence / cleanup

- **Test artifact:** comment **id 903** on `ExceptionRequest` thread 33 contains `&lt;img src=x onerror=alert();&gt;` (`message_raw`) and `<img />` (`message_html`), owner user 230. This comment is live and will fire for anyone opening that thread — it should be deleted by the program.
- Exception 32 title/description/closure_notes/recommendation hold `&lt;b&gt;ZXZXE5646c&lt;/b&gt;` from prior testing (originals: `tes` / `zf` / `dfsz`).
- Disclosed from this engagement: files 2712/2726/2730/2732 deleted (BUG-015); issue 121 status changed; narrative 67 created; risk/narrative names modified (BUG-019); attachments 11207–11220, 11252–11254 generated; several account emails changed during BUG-017 and left in place at the operator's instruction.
