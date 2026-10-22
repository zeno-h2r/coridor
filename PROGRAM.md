# PROGRAM.md — OpenAI Bug Bounty (Bugcrowd)

## Program Metadata
- Platform: Bugcrowd | Status: public (since Sep 02, 2025) | Safe Harbor: Full
- Avg payout: $454.54 | Validation: ~13 months | 665 vulns rewarded
- Bounty tiers: P1 $100,000 | P2 $2,000–$6,500 | P3 $1,000–$2,000 | P4 $500–$1,000 | P5 $200–$500
- Test accounts: personal + signup via @bugcrowdninja.com email (preferred)

## Scope
- https://api.openai.com
- https://chat.openai.com
- *.openai.com
- https://openai.com/

## Focus Areas
- Cross-org (multi-tenant) isolation: Cross-Org IDOR, SQLi, RCE
- Unauthorized cross-org data access: IDOR, SQLi, Stored XSS, Auth Bypass
- Privilege escalation bypassing org isolation
- Stored/Reflected XSS
- Auth issues | Authz issues | Data exposure
- SSRF, RCE from misconfig, network-level access (internal port scan / internal services)

## Out of Scope (key exclusions)
- Model issues / weird model behavior / hallucination-class bugs
- DoS, brute force, password spraying, spam, API brute forcing
- Data destruction/corruption of others' data
- Stolen/leaked credentials as root cause
- Email security (SPF/DMARC/DKIM), missing headers w/o PoC, clickjacking
- Server errors w/o exploit, server version strings, EOL browsers
- ./well-known/ai-plugin.json verification tokens
- Internal package name baiting in public repos
- Code Interpreter sandbox / sending shell commands to Code Interpreter VM
- Dormant OSS projects (only actively maintained = rewardable)
- pay.openai.com (Stripe), community.openai.com (3rd-party) — unused subdomain takeover still in scope
- Known/accepted: password change token invalidation, member-add w/o permission, account deletion w/o password, broad API key perms, key count cap, cookie transfer, cross-domain image display, OpenGraph previews, model preset share links, intercom email change, billing lag, most rate-limit/quota issues unless complete bypass at scale (hundreds+ requests), IP/geoblock/VPN bypass, Cloudflare bypass on api.openai.com, capacity page bypass, captcha emulation
- Excessive-user-cooperation / self-XSS / browser-debug attacks

## Current Target (operator directive)
- https://platform.openai.com ONLY until operator switches
- Priority surfaces: all /settings/organization/* pages, /playground, /agents, /agent-builder, /codex, /batches, /logs, /storage, /tunnels, /webhooks, /evaluation, /decisions
- Method: full feature + JS bundle learning first, then deep testing

## Test Credentials (operator-provided sessions)
- Session A (zeno0+org): Bearer sess-tsToqILYlqVQjC89yfRnaTgtUUR8cv1UHbXVLqK3 / org-LmtLWdWHK1QRQgJAEPjqwv3U
- Session B (zeno0): Bearer sess-fwi5RQ2iz39mNicJ2o5FpmmqRlBsvfEYnGcGdK2W / org-2rdk3sogiNiOJ5rRdFhhGgpr
- Two orgs = cross-org isolation test rig (A↔B IDOR/authz probes)
