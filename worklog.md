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
