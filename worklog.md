# Sumsub Managed Bug Bounty — Worklog
Researcher: zeno0 (Bugcrowd) | Target: https://cockpit.sumsub.com (sandbox: X-SNS-Env: sbx)
Started: 2026-10-25 UTC

## Accounts
- ACCT-A: zeno0+org@bugcrowdninja.com (fingerprint 9e713cca...)
- ACCT-B: zeno0@bugcrowdninja.com (fingerprint 8dec4f20...)

## Phase 0 — Recon (IN PROGRESS)
- [ ] Application map
- [ ] JavaScript inventory
- [ ] Endpoint inventory
- [ ] Feature-endpoint mapping
- [ ] Coverage report

## Tested / Findings
(none yet)

## Session findings (2026-10-25 UTC)
- [CRITICAL-CONTEXT] Dashboard sessions are IP-bound: error 2023 session-invalidated-mismatch ("network connection changed") when replaying operator cookies from this network. Both ACCT-A and ACCT-B cookies dead from sandbox egress.
- Auth surface requires reCAPTCHA v2 userVerificationToken (sitekey 6LdiyYcUAAAAAO_FEVcTbUOXqjhspAKdxV3rz3cp) on: loginViaForm, signup/clientAccount/request, auth/reset/resetPasswordLink.
- api.sumsub.com edge-blocked for curl: 403 "Unauthorized (cfb)" = Cloudflare Bot Fight Mode. Need browser TLS or app-token HMAC.
- Unauthenticated GET sweep of 341 cockpit endpoints: 0× 200. Auth layer solid at baseline.
- [HIGH-VALUE TARGET] X-Impersonate header (staff client-switcher feature) used on ~dozens of applicant/inspection endpoints. Cross-tenant trust in this header = P1. Test with own 2 orgs once session available.
- [TARGETS] /dashboard/appTokens* (API token mgmt), /dashboard/inspections/{id}/* (IDOR surface), /dashboard/applicants/{id}/*, media/image endpoints, /snsId/dashboard/profile/{id}/export.
- SSO: /auth/sso/login + /auth/sso/metadata (SAML) present on dashboard host.
