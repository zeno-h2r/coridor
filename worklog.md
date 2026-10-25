# Dynamic Labs Bug Bounty — Engagement Worklog
- Program: Dynamic Labs Managed Bug Bounty (Bugcrowd)
- Researcher: zeno0 (zeno0@bugcrowdninja.com)
- Scope: app.dynamic.xyz (dashboard + backend app.dynamicauth.com/api/v0)
- Started: 2026-10-25 22:40 UTC — Last updated: 2026-10-25 23:50 UTC

## CONFIRMED FINDING #1 (P3, borderline P2)
### Step-up authentication NOT enforced on webhook signing secret reveal → signed webhook forgery chain
- Endpoint: GET /api/v0/environments/{environmentId}/webhooks/{webhookId}?includeSecret=true
- Host: app.dynamicauth.com (same via app.dynamic.xyz/api/v0)
- Spec (public-api.yaml, parameters/includeSecret): "Requires step-up authentication: a valid elevated access token with the `console:webhook_secret:reveal` scope, minted for the calling user, must be sent in the `x-dyn-elevated-access-token` header **or the request is rejected with 403**."
- Reality:
  1. GET with ONLY the regular session JWT → 200 + `"secret":"dyn_Qfvm49E4cdO0AewRTjk{PAGBhx2t[RNpVMqajPTaQaq4Yme[f12LQka9"`
  2. Same with `x-dyn-elevated-access-token: garbage-invalid-token` → 200 + secret (header completely unvalidated)
  3. Captured legit webhook delivery: x-dynamic-signature-256: sha256=38260fc64e8a6ade544387e47d7b27946b1dff9545516e0effcae1eae60339b9 over raw body
  4. HMAC-SHA256(leaked_secret, rawBody) == captured signature → EXACT MATCH → secret is the real signing key
  5. Forged payload signed with leaked secret produces a signature indistinguishable from genuine Dynamic webhooks
- Impact chain: stolen/compromised admin session (the exact threat step-up protects against) → secret reveal with NO re-auth → forge arbitrary user.created / wallet.linked / transaction events with valid HMAC → customer backends that verify signatures (the secret's entire purpose) trust forged events (auto-fulfillment, crediting, KYC hooks, access grants)
- Contrast proving unintended behavior: captcha secretKey is correctly masked (hasSecretKey:true, never returned); list endpoint ignores includeSecret — only the detail endpoint leaks
- Feature context: "Step-Up Auth for Key Export" shipped Apr 2026; console:webhook_secret:reveal scope exists in TokenScope enum specifically for this action
- Evidence artifacts: /home/z/my-project/recon/ (webhook.site inbox 72e683f6-959e-4264-8aa8-82f389ed746d, deliveries captured 2026-10-25T23:27:35Z ping + 23:27:51Z user.created)
- Test env (own): sandbox 7dfe3b0c-c0db-4dfa-bba6-f72df97ccbd6, webhook 721f79c5-572e-4d64-869d-680268d164b4
- Open sub-test: viewer/developer role → same includeSecret call (needs 2nd member; invite pending — B must re-login and accept invite 91e1b785-484e-4e8a-8512-afdfbbf2ba01)

## Test Accounts
- Account A "victim zeno": zeno0+org@bugcrowdninja.com — user c8792188-3451-41ae-bab4-7b3725fac172
  - org e6be9ca6-0af0-49fc-a257-9c0efac1687f (owner), project ee8bf803-7dc5-443d-9e97-765fb84e5d3b, sandbox env 7dfe3b0c-c0db-4dfa-bba6-f72df97ccbd6
  - JWT ACTIVE — do not revoke
- Account B "attacker zeno": zeno0@bugcrowdninja.com — user 80327e1e-25b9-4b52-bba4-d2a49498d5f3
  - org 06f46da7-b49a-4619-a85b-fbb4ded68d6f (owner), envs 9a820c93 (sandbox), a1b8ad35 (live)
  - JWT REVOKED during invalidation testing ~23:23 UTC — NEEDS RE-LOGIN
- Pending invite: 91e1b785-484e-4e8a-8512-afdfbbf2ba01 (B → viewer on victim org) awaiting B's acceptance
- Webhook on victim sandbox → https://webhook.site/72e683f6-959e-4264-8aa8-82f389ed746d
- Test user created on victim sandbox: eaacc556-2e96-4bcd-90cb-e183f83ed7aa (whtrigger+x1@example.com)

## API Tokens (attacker sandbox env 9a820c93)
- dyn_lPS2FBaGhA2SFkzbuIDq7H0eYgwlb9hioqrtZugEB21mP4IiRb2XyLK0 [all.read]
- dyn_jmPdZLfdvmAeoT63xixDFzgxg6Zw086BSEl7XqPKidPSkoCh8j3YQaP9 [flow.write]
- users.write token for victim sandbox stored in recon/users_write_token.txt

## Architecture Notes
- Dashboard: Angular SPA at app.dynamic.xyz; API same-origin /api/v0 + app.dynamicauth.com/api/v0; Fastify+zod
- Full public OpenAPI spec: https://app.dynamic.xyz/api-docs/public-api.yaml (525 ops); docs render as .md
- JWTs: RS256 kid 65aebd86, 24h access + 30d refreshExp, session_public_key carried
- Device attestation: ECDSA P-256 P1363 hex, signs ONLY nonce string; accepts self-generated keys (anti-bot only); implemented in scripts/device_auth.js
- Nonces: /nonce (SIWE, single-use confirmed), /nonces (device, "auth"-prefixed)
- Secrets handling: captcha secretKey write-only (correct); webhook secret plaintext via includeSecret (BROKEN gate)

## Completed Tests (summary — all NO ISSUE unless noted)
1. Cross-tenant IDOR sweep (20 endpoints, B vs A ids): all 403 opaque
2. Dashboard JWT cross-env SDK: 403 env-boundary
3. getBAMutateAccessEnvIdsFromJWT: server-derived, 60s TTL
4. SIWE signin template hunt (12 variants): blocked on message validation; nonce single-use confirmed
5. users/check email oracle on dashboard env: P4/P5, not submitting
6. stepUp/check {scope:wallet:export}: isRequired true, OTP-gated (needs inbox)
7. sessionKey arbitrary key: 422 rejected
8. V3 waas/create: SSE ceremony starts, needs client MPC join
9. dyn_ token: cross-env 403; all.read → flow create 403 scope enforced
10. Flow/Payment-links: support-gated on own env
11. /server/*: x-dyn-server-signing-proof gated (env-flagged)
12. Refresh rotation: same sid, 24h extension; post-revoke refresh 401 "Session is no longer active" — invalidation SOLID
13. Sessions: /sessions/{id}/revoke env-admin-only; cross-user 403; /sdk/revoke works + propagates
14. globalWallets: Origin + custom-hostname scoped
15. createUser/bulkCreate (InternalUserFields): env-admin bearerAuth only
16. Webhook receivers (stripe/sendgrid/etc.), testReadOnlyPrismaService, kms/reEncrypt: 404 internal-only
17. scan/websiteUrl: isMalicious bool (3rd-party lookup, no fetch evidence; OAST probe ssrf-probe-1 fired — user to check Collaborator)
18. Captcha settings: secret masked
19. Admin actions: list OK on victim org; approve flow needs 2nd member

## Next Actions
1. ✅ DONE (2026-10-25 23:50 UTC): BUG-001 report written → `reports/BUG-001-webhook-secret-stepup-bypass.md` in this repo; ready to paste into Bugcrowd submission form
2. After B re-login: accept invite → viewer-role includeSecret test (severity escalation path) + admin-action self-approve test + full write-access-as-viewer sweep
3. User-assisted: one real wallets/signin capture (Burp), OAuth link on test account (→ /oauthAccounts/{id}/accessToken test), step-up OTP for wallet:export chain
4. Deferred: full WalletKit MPC client ceremony; lazy chunks; exchange/onramp config secrets

## Report Log
- 2026-10-25 23:50 UTC — BUG-001 report authored and committed to repo (`reports/BUG-001-webhook-secret-stepup-bypass.md`). Re-verified live before writing: Test 1 plain-JWT reveal 200 (23:46:48Z), Test 2 garbage elevated-token 200 (23:46:57Z), control list endpoint omits secret, HMAC(rawBody) exact match vs captured x-dynamic-signature-256 + forged signature generated (hmac_verify_fresh.txt). Severity P3 (argued P2). Artifacts: recon/reverify_t1_234648.txt, recon/reverify_t2_234657.txt, recon/hmac_verify_fresh.txt.
