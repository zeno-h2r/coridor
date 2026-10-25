# Dynamic Labs Bug Bounty — Engagement Worklog
- Program: Dynamic Labs Managed Bug Bounty (Bugcrowd)
- Researcher: zeno0 (zeno0@bugcrowdninja.com)
- Scope: app.dynamic.xyz (dashboard + backend app.dynamicauth.com/api/v0)
- Started: 2026-10-25 22:40 UTC — Last updated: 2026-10-25 23:25 UTC

## Test Accounts
- Account A "victim zeno": zeno0+org@bugcrowdninja.com — user c8792188-3451-41ae-bab4-7b3725fac172
  - org e6be9ca6-0af0-49fc-a257-9c0efac1687f (owner), project ee8bf803-7dc5-443d-9e97-765fb84e5d3b, sandbox env 7dfe3b0c-c0db-4dfa-bba6-f72df97ccbd6
  - JWT ACTIVE (do not revoke)
- Account B "attacker zeno": zeno0@bugcrowdninja.com — user 80327e1e-25b9-4b52-bba4-d2a49498d5f3
  - org 06f46da7-b49a-4619-a85b-fbb4ded68d6f (owner), project 24ceb9dd-79f3-43d3-ba73-a3cc48fe0163
  - envs: sandbox 9a820c93-0abe-4abc-9a89-6ada66c5968c, live a1b8ad35-ad55-4f44-8a7c-7a767126e124
  - JWT REVOKED during session-invalidation testing (2026-10-25 ~23:23 UTC) — NEEDS RE-LOGIN
- Dashboard meta environment for both users: fb6dd9d1-09f5-43c3-8a8c-eab6e44c37f9

## API Tokens (attacker sandbox env 9a820c93, created for testing)
- dyn_lPS2FBaGhA2SFkzbuIDq7H0eYgwlb9hioqrtZugEB21mP4IiRb2XyLK0 — scopes [all.read] id 7267a552-9dbd-4d74-aa30-9f03256fd24b
- dyn_jmPdZLfdvmAeoT63xixDFzgxg6Zw086BSEl7XqPKidPSkoCh8j3YQaP9 — scopes [flow.write]

## Architecture Notes
- Dashboard: Angular SPA at app.dynamic.xyz; API same-origin /api/v0 proxy + https://app.dynamicauth.com/api/v0
- Backend: Fastify + zod; validation errors reveal expected schemas (param validation runs BEFORE authz on several routes)
- JWTs: RS256 kid 65aebd86, aud app.dynamicauth.com, iss auth.dynamicauth.com/{envId}, 24h access + 30d refreshExp, scope user:basic, carries session_public_key
- Full public OpenAPI spec EXPOSED: https://app.dynamic.xyz/api-docs/public-api.yaml (525 ops; Server tag = dyn_ token auth + x-dyn-server-signing-proof for sensitive ops)
- Device attestation: ECDSA P-256, client-generated key, signs ONLY the nonce string (headers x-dynamic-device-nonce/publickey/signed-nonce). Anti-bot layer only — accepts arbitrary self-generated keys (by design)
- Nonce endpoints: /nonce (SIWE), /nonces (device, "auth"-prefixed)
- Docs render as markdown: append .md to any docs.dynamic.xyz page; llms.txt index available
- SDK client @dynamic-labs/sdk-api-core@0.128.0 contains all request/response models
- SIWE builder: module in vendor-00152608 (DL export); no statement configured on own envs

## Tests Executed & Results (updated)
| # | Test | Result | Status |
|---|------|--------|--------|
| 1 | Cross-tenant IDOR sweep attacker(B) vs victim(A) ids: 20 endpoints (org/project/env/member/users/keys/origins/webhooks/exports/lookup/visitors/events) | ALL 403 opaque "not found" | NO ISSUE |
| 2 | Dashboard JWT on other envs' SDK endpoints (/session, /refresh, settings) | 403 "JWT environment has no access to requested environment" | NO ISSUE |
| 3 | getBAMutateAccessEnvIdsFromJWT | 60s scoped JWT, env list server-derived, no client input | NO ISSUE |
| 4 | SIWE signin message template hunt (12 variants: statements, domains, timestamps, resources, request-id, trailing newline) | All "Message validation failed"; nonce confirmed SINGLE-USE (reuse → "Could not validate nonce") | BLOCKED — need real captured request |
| 5 | wallets/verify without session | 401 auth required (link-flow, not anon) | BY DESIGN |
| 6 | users/check (email availability oracle) on dashboard env fb6dd9d1 with user JWT | {available:false} for registered email, true otherwise — user enumeration oracle for ANY authenticated dashboard user | P4/P5 — LOGGED, NOT SUBMITTING (below bar) |
| 7 | stepUp/check {scope:"wallet:export"} | Returns credentials list + isRequired:true — flow exists; OTP gated | NEEDS OTP INBOX |
| 8 | sessionKey with arbitrary ed25519 key | 422 invalid_session_public_key "Security verification failed" | NO ISSUE |
| 9 | V3 wallet create (waas/create) | SSE MPC ceremony starts, room created, requires client MPC join to complete | BLOCKED (needs WalletKit ceremony) |
| 10 | Env API token creation (own env) | Works: POST /environments/{env}/tokens returns plaintext dyn_ token; live env restricted ("Unauthorized: Live environment restricted" for origins + tokens on live) | BY DESIGN |
| 11 | dyn_ token cross-env use (sandbox token → live env /server/users) | 403 "Token does not have access to this environment" | NO ISSUE |
| 12 | dyn_ token scope enforcement (all.read → POST flow/payment) | 403 "Insufficient scope permissions" (validation runs first, but authz enforced) | NO ISSUE |
| 13 | Flow/Payment-links on own env | "Flow is not enabled for this environment. Please contact support" — feature-gated | BLOCKED |
| 14 | Server endpoints without x-dyn-server-signing-proof | 401 "Authentication through the x-dyn-server-signing-proof header is not enabled for this environment" (except flow/fees/balances which is bearer-only) | BY DESIGN |
| 15 | Device attestation implementation (ECDSA P-256 P1363, hex) + POST /sdk/env/refresh | 200 — refresh works with self-generated device key; same sid returned; 24h window; refreshExp unchanged | BY DESIGN (anti-bot only) |
| 16 | PUT /sessions/{sid}/revoke with own sid (dashboard env user) | 403 "This resource is unavailable or does not exist" (env-admin-only route) | NO ISSUE |
| 17 | POST /sdk/{env}/revoke (self) | 204; old JWT 401 immediately; refresh post-revoke → 401 "Session is no longer active" | NO ISSUE — invalidation solid |
| 18 | Cross-user session revoke (A→B sid) | 403, B session intact (pre-revoke-test) | NO ISSUE |
| 19 | globalWallets/settings with foreign Origin | 403 "Custom hostname does not belong to this project environment"; without Origin → 403 "No origin header present" | NO ISSUE |
| 20 | InternalUserFields endpoints (createUser/bulkCreateUser accept email+emailVerifiedAt+wallets+oauthAccounts) | bearerAuth env-admin; cross-env 403 confirmed; own-env use excluded by program | NO ISSUE (excluded) |
| 21 | testReadOnlyPrismaService, kms/reEncrypt, waas/backfill*, third-party webhook receivers (stripe/sendgrid/resend/turnkey/lithic/aiprise) | 404 at both /api/v0 bases | INTERNAL ONLY |
| 22 | zendesk/login | 404 "Zendesk SSO is not enabled for this organization" | ORG-GATED |
| 23 | authToken endpoint (type param) | no type → "Cannot GET" (different legacy layer); type=mpc → same; route half-migrated | ODDITY, no impact |

## Key Unresolved / Next
1. B needs re-login (session revoked during testing) — then: invite-flow role boundary test (A invites B as viewer/developer to victim org; test write-access as viewer, invite acceptance as existing user without email click)
2. OTP-dependent flows need inbox access: step-up (wallet:export), email change, emailVerifications
3. SIWE signin: needs one real captured wallets/signin request (user can capture in Burp from any dapp using Dynamic)
4. OAuth accessToken endpoint (/oauthAccounts/{id}/accessToken): needs OAuth-linked account — user to link Google on a test account
5. Waas MPC client ceremony: would enable full wallet-level IDOR testing
6. Lazy-loaded chunks not yet all downloaded (12 chunk ids pending) — low priority

## Findings
(none confirmed yet — no P1/P2/P3)
