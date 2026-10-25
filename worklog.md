# Dynamic Labs Bug Bounty — Engagement Worklog
- Program: Dynamic Labs Managed Bug Bounty (Bugcrowd)
- Researcher: zeno0 (zeno0@bugcrowdninja.com)
- Scope: app.dynamic.xyz (dashboard + backend app.dynamicauth.com/api/v0)
- Started: 2026-10-25 22:40 UTC

## Test Accounts
- Account A "victim zeno": zeno0+org@bugcrowdninja.com
  - user: c8792188-3451-41ae-bab4-7b3725fac172
  - org: e6be9ca6-0af0-49fc-a257-9c0efac1687f ("victim zeno", role owner)
  - project: ee8bf803-7dc5-443d-9e97-765fb84e5d3b
  - sandbox env: 7dfe3b0c-c0db-4dfa-bba6-f72df97ccbd6
- Account B "attacker zeno": zeno0@bugcrowdninja.com
  - user: 80327e1e-25b9-4b52-bba4-d2a49498d5f3
  - org: 06f46da7-b49a-4619-a85b-fbb4ded68d6f ("attacker zeno", role owner)
  - project: 24ceb9dd-79f3-43d3-ba73-a3cc48fe0163
  - envs: sandbox 9a820c93-0abe-4abc-9a89-6ada66c5968c, live a1b8ad35-ad55-4f44-8a7c-7a767126e124
- Dashboard meta environment (both users): fb6dd9d1-09f5-43c3-8a8c-eab6e44c37f9

## Architecture Notes
- Dashboard SPA: Angular, served from app.dynamic.xyz; API base = same-origin /api/v0 (proxied), also reachable at https://app.dynamicauth.com/api/v0
- Backend: Fastify + zod validation (verbose validation errors leak expected schemas)
- JWT: RS256, kid 65aebd86 (dashboard users), aud https://app.dynamicauth.com, iss auth.dynamicauth.com/{envId}, 24h TTL, scope user:basic, carries session_public_key (PoP-capable)
- Second signing key kid c34abba9 used for short-TTL (60s) scoped tokens: token_use=ba-rbac-mutate-access-membership, minimum_role=developer
- robots.txt confirms /api/v0/sdk/ surface
- SDK base: https://app.dynamicauth.com + /api/v0/sdk/{environmentId}/...

## Endpoint Inventory (~450 route templates extracted from main.41bd437d6a9a8eaa.js)
Key groups: /organizations/*, /environments/*, /sdk/{envId}/*, /auth/*, /invites, /billing/*, /waas/*, businessAccounts, exchanges, yield vaults, webhooks (internal-only hosts), adminActions, KYB, device-grant flow (/auth/grant/peek + /auth/grant/approve for CLI/MCP)

## Tests Executed & Results
| # | Test | Result | Status |
|---|------|--------|--------|
| 1 | Cross-tenant IDOR sweep: attacker(B) token vs victim(A) org/project/env/member IDs on 20 endpoints | ALL 403 with opaque "Environment/Organization/Project not found" | NO ISSUE |
| 2 | GET /api/v0/sdk/{victim_env}/settings with attacker JWT | 200 — expected: SDK settings is intentionally public per program policy | NO ISSUE |
| 3 | Dashboard JWT on SDK endpoints of other envs (/session, /refresh) | 403 "JWT environment has no access to requested environment" | NO ISSUE |
| 4 | /getBAMutateAccessEnvIdsFromJWT | Returns 60s scoped JWT; env list derived server-side from caller memberships; no client-controllable input | NO ISSUE (so far) |
| 5 | /auth/grant/peek unauth | 401 (auth or cookie required) | NO ISSUE |
| 6 | Internal/diagnostic endpoints (testReadOnlyPrismaService, kms/reEncrypt, waas/backfill*, nonce/consume, third-party webhook receivers) | 404 at both /api/v0 bases — internal-only or different host | NO ISSUE |
| 7 | JWT signature verification (local JWKS check) | Both account JWTs verify RS256 correctly; env-scoped session check works | NO ISSUE |

## Coverage
- [x] Main bundle JS analysis (routes, base URLs, config)
- [ ] Lazy chunk download + analysis
- [ ] SDK email/passkey/WaaS flows deep test (own env only)
- [ ] Device grant flow deep test
- [ ] Invite flow
- [ ] Email change flow
- [ ] Business accounts (disabled in own envs)
- [ ] Exchanges/onramp flows
- [ ] Session revocation/step-up

## Findings
(none confirmed yet)
