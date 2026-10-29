# BUG-005 — Unauthenticated Contentful Preview API Proxy Exposes Pre-Release Site Content

- Target: https://www.dutchbros.com/ (only in-scope asset)
- Researcher: zeno0 (zeno0@bugcrowdninja.com)
- Date: 2026-10-29
- Proposed severity: **P3** (honest range: P3, possible P4 triage — see Impact)
- VRT: Sensitive Data Exposure / Improper Access Control

## Summary
`https://www.dutchbros.com/api/contentful/preview` is a server-side proxy to the **Contentful Preview API** (space `tesk7a84db2g`, environment `master`). It requires **zero authentication** — no token, no session, no internal header, no IP restriction. The Contentful Preview API exists precisely because draft/preview access must be separated from the public Delivery API and gated by a secret token; this proxy negates that isolation on the production origin.

Entry IDs are trivially enumerable: every route's public `/_payload.json?_b=<buildId>` file embeds referenced entry IDs (1,722 IDs harvested from the sitemap routes alone; 1,103 resolved as valid entries through the proxy).

Demonstrated impact: the proxy serves **CMS-published content that has not been deployed to the production website** — including an unreleased Holiday product carousel ("Holiday Sprinkle Cookie" coffee bag, "Candy Cane Mocha" pods) and a batch of 9 updated product pages — while the live site still shows the old content. Pre-launch product/campaign/news content is readable by anyone days before public availability.

## Affected endpoint
```
GET /api/contentful/preview?entryId=<contentfulEntryId>
Host: www.dutchbros.com
```
- No auth of any kind (verified with a bare `curl` with no headers).
- `entryId` is strictly format-validated (regex-like: `[A-Za-z0-9_-]{20,23}`), so no injection — the issue is pure access control, not parsing.
- Other query params (`include`, `locale`, unknown) are ignored — the proxy forwards only `entryId`.
- Companion route `/preview?entry_id=<id>` (Nuxt page rendering preview entries) is present in the client router but returns the SPA 404 — the API route is the live exposure.

## Reproduction (all commands verified 2026-10-29 07:20-07:25 UTC)

**Step 1 — enumerate valid entry IDs from a public payload file:**
```bash
curl -s 'https://www.dutchbros.com/at-home/_payload.json?_b=bac26790-0c6c-43bd-9738-c409b7841561' \
  | grep -oE '"[A-Za-z0-9_-]{20,23}"' | sort -u | head
```

**Step 2 — fetch a full entry through the unauthenticated proxy (no headers needed):**
```bash
curl -s 'https://www.dutchbros.com/api/contentful/preview?entryId=2RC3a5rLcnm6s6KwhAVZbZ'
```
Response (truncated): full raw Contentful JSON — `sys` (contentType `page`, revision 8, **publishedAt 2026-10-27T22:28:07.293Z**) plus ALL `fields`, including nested `pageComponents`. At char offset ~21746 of `fields`, the response contains the unreleased marketing content: *"Dutch Bros Holiday Sprinkle Cookie coffee bag and Candy Cane Mocha pods displayed in a festive snowy scene with a red coffee maker."*

**Step 3 — prove the same content is NOT on the production site:**
```bash
curl -s 'https://www.dutchbros.com/at-home/' | grep -c "Holiday Sprinkle"   # -> 0
curl -s 'https://www.dutchbros.com/at-home/_payload.json?_b=bac26790-0c6c-43bd-9738-c409b7841561' | grep -c "Holiday Sprinkle"   # -> 0
```

**Step 4 — scale:** 11 entries (1 `page`, 8 `productDetail`, 1 `freeHtml`, 1 `contentGrid`) were published to the CMS on 2026-10-27 (after the last production build of 2026-10-26) and are served by the proxy but absent from production:
- Vanilla Caramel Ground Coffee, OG Medium Roast Ground Coffee, Caramel Mocha Ground Coffee, Mafia Dark Roast Ground Coffee, Chocolate Macadamia Nut Ground Coffee, Coconut Mocha Ground Coffee, Caramel Pumpkin Brûlée Pods, Irish Cream Ground Coffee, Epic Light Roast Ground Coffee (all `/at-home/products/...`), plus the at-home page with the Holiday carousel.
- Product names/slugs: `preview/1Vk8EchNWIgiTYiq9AjLR8.json` etc. via the proxy.

**Step 5 — browser-rendered preview (verified 2026-10-29 08:15 UTC):** the SPA route `https://www.dutchbros.com/preview?entry_id=2RC3a5rLcnm6s6KwhAVZbZ` (Nuxt route `preview`, component `xuN6gd0F.js`) fetches the same unauthenticated proxy and renders the entry as a full branded page. Although the server responds HTTP 404 (SPA fallback shell), client-side hydration matches the `/preview` route and displays the unreleased content: verified headless-render output includes "Candy Cane Mocha & Holiday Sprinkle Cookie", "LIMITED EDITION HOLIDAY FLAVORS", and the unreleased product imagery. This means anyone with just a browser — no API tooling, no entry-ID harvesting script — can view CMS content at a clean URL once an entry ID is known, and entry IDs are enumerable from public payloads (Step 2).

## Impact
- **Pre-release content disclosure (demonstrated)**: unreleased seasonal products, campaign banners, and news content are readable by anyone, days-to-weeks before the production site deploys them. Seasonal launches (e.g., Holiday menu) are embargoed marketing events; a competitor or leak site monitoring this endpoint gets the full launch catalog early — names, slugs, descriptions, pricing-adjacent metadata, and image assets, in structured JSON.
- **Full CMS entry disclosure (by ID)**: the proxy returns every field of any entry, including fields the site never renders (e.g., `css`, `accordionFields`, internal component metadata, raw `freeHtml`), with no field allow-listing.
- **Design flaw**: the endpoint is built for internal Contentful editors (the `/preview` page is the CMS preview integration) but is exposed unauthenticated on the public production origin. Contentful's own preview-token model assumes the token never reaches untrusted clients; a public proxy keyed to that token makes enumeration trivial once entry IDs leak (they do — public payloads).

## Honest limitations (stated up front)
- No PII, no credentials, no user data — exposure is marketing/product content only.
- The demonstrated delta is CMS-published-but-not-yet-deployed content (`revision == publishedVersion` for all 1,103 entries — no true Contentful *drafts* were observed). If the program considers "published in CMS, not yet deployed" intended-public content, the finding degrades to P4 (hardening). The unauthenticated preview-proxy access itself remains a misconfiguration either way.

## Remediation
1. Require an internal-only mechanism for preview rendering: session/SSO auth, a shared secret header, IP allow-listing, or serve `/api/contentful/preview` only from an internal origin.
2. If the preview route must stay public for the Contentful editor integration, validate a short-lived signed token issued to authenticated editors instead of accepting bare `entryId` lookups.
3. Add a field allow-list / strip `sys` internals in proxy responses.

## Evidence files
- `recon/draftdiff/evidence/poc4_preview_browser.png` — headless-browser screenshot of `/preview?entry_id=2RC3a5rLcnm6s6KwhAVZbZ` rendering the unreleased at-home page (holiday banner + unreleased products); DOM text extraction confirmed "Candy Cane Mocha & Holiday Sprinkle Cookie" + "LIMITED EDITION HOLIDAY FLAVORS"
- `recon/draftdiff/evidence/poc1_preview_response.json` — unauthenticated proxy response (Holiday content inside)
- `recon/draftdiff/evidence/poc2_live_athome.html` — live page (Holiday content absent)
- `recon/draftdiff/evidence/poc3_live_count.txt` — grep count 0
- `recon/draftdiff/{summary,diffs,draft_entries}.json` — 1,722 IDs harvested, 1,103 resolved, full diff corpus
- `scripts/draft_diff.py`, `scripts/draft_compare.py` — reproducible harvest/diff tooling
