# Dynamic Labs Bug Bounty — Engagement Worklog
- Program: Dynamic Labs Managed Bug Bounty (Bugcrowd)
- Researcher: zeno0 (zeno0@bugcrowdninja.com)
- Scope: app.dynamic.xyz (dashboard + backend app.dynamicauth.com/api/v0)
- Started: 2026-10-25 22:40 UTC — Last updated: 2026-10-26 00:20 UTC

## CONFIRMED FINDING #1 (**P2** — escalated 2026-10-26)
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
1. ✅ DONE (2026-10-26 00:20 UTC): BUG-001 escalated to P2 (viewer-role reveal confirmed) — append §8 to Bugcrowd submission
2. User-assisted: one real wallets/signin capture (Burp), OAuth link on test account (→ /oauthAccounts/{id}/accessToken test), step-up OTP for wallet:export chain
3. Deferred: full WalletKit MPC client ceremony; lazy chunks; exchange/onramp config secrets
4. State note: B is currently viewer on victim org (e6be9ca6) — kept for further least-privilege sweeps

## Report Log
- 2026-10-25 23:50 UTC — BUG-001 report authored and committed to repo (`reports/BUG-001-webhook-secret-stepup-bypass.md`). Re-verified live before writing: Test 1 plain-JWT reveal 200 (23:46:48Z), Test 2 garbage elevated-token 200 (23:46:57Z), control list endpoint omits secret, HMAC(rawBody) exact match vs captured x-dynamic-signature-256 + forged signature generated (hmac_verify_fresh.txt). Severity P3 (argued P2). Artifacts: recon/reverify_t1_234648.txt, recon/reverify_t2_234657.txt, recon/hmac_verify_fresh.txt.
- 2026-10-26 00:20 UTC — BUG-001 **ESCALATED TO P2**. B (zeno0@bugcrowdninja.com) re-logged in (fresh sid fb51befb, JWT exp 2026-10-27T00:09Z, saved scripts/tok_b_new.txt). Old invite 91e1b785 dead (404; B pending invites count 0, recon/b_invites.txt). Invite d4a5e2e9-02c2-45eb-9696-b79f2fb1ca19 on victim org status=accepted role=admin (B accepted during re-login). KEY RESULT 1 (cross-account): B as member-admin with JWT roles claim containing ONLY its own org (stale token; authz is DB-membership-driven, step-up enforced for nobody) → victim env webhook includeSecret=true → 200 + plaintext secret. Downgraded B to viewer: PUT /members/b84845be-6965-46ef-ae45-4f1a5e861c4b {"role":"viewer"} → 200 (recon/b_downgrade.txt). KEY RESULT 2 (least-privilege): B as VIEWER → includeSecret=true → 200 + plaintext secret (recon/b_viewer_secret.txt). Viewer write sweep correctly 403 across PUT update / DELETE bogus-id / POST create — reveal gap is specific to the credential-reveal action. Report §8 added, severity revised P2. Member IDs: B=b84845be-6965-46ef-ae45-4f1a5e861c4b (viewer), A=a941506a-0799-4c36-8542-1e114cc889c0 (owner) on victim org e6be9ca6-0af0-49fc-a257-9c0efac1687f.
- 2026-10-26 00:50 UTC — **IDOR SESSION ROUND 2 (outsider B, post-removal)**. User removed B from victim org before test → B = full outsider w/ fresh session (tok_b_new.txt, sid fb51befb, exp 2026-10-27T00:09Z). T1 post-removal revocation: IMMEDIATE — B→victim webhook reveal 403 "Environment not found", B→victim org members 403 "Organization not found"; no authz-cache lag, removal enforcement SOLID. T2 fresh read sweep (15 targets): /users/{id} (incl. B's OWN id → uniform framework 403), /users/{id}/wallets, /users/{id}/sessions/{sid} (+wrong-pair), /users/{id}/mfa (405), /projects/{victim}, /environments/{victim}[/settings|/users|/webhooks], /organizations/{victim} — ALL 403/404-opaque. /membershipEnvironmentIds → 200 (B own envs only: 9a820c93-0abe-4abc-9a89-6ada66c5968c, a1b8ad35-ad55-4f44-8a7c-7a767126e124). T3 mutation sweep: PUT /members/{A|B-deleted} 403 fw; POST mfa/reset, POST sessions/revoke 403 fw; PUT /invites/d4a5e2e9 (victim ACCEPTED invite) → 422 "Cannot update a non-pending invite" + DELETE → 403 "Cannot remove invites other than pending" = business-logic responses, authz passed → probed deeper. T4 invite IDOR end-to-end: A created pending invite 6d2032be-06df-4f64-a45a-f80e95e6305d (zenovictim+x3@bugcrowdninja.com, viewer — email B does NOT control); outsider B PUT accept → 403 "No access to update invite via email" (email-ownership enforced, memberships unchanged); B DELETE → 403 "Cannot delete invite when not an admin" (org-admin enforced). RESIDUAL: invite STATUS ORACLE — differential errors on arbitrary invite UUIDs (422=non-pending vs 403-email=pending) leaks status of any invite object; v4 UUIDs unguessable → P5, not submittable per FP rules. T5 cross-env user-object pairs (B own env + victim end-user eaacc556): /users/{id}, /wallets, /sessions → 403 fw; /balances 405. POSITIVE CONTROL: B created user b8227b75-14bf-4883-9e09-a2c64c491797 on own env (POST /environments/9a820c93…/users → 200) then GET same route → 200 own vs 403 foreign — user↔env binding enforced, route logic healthy. T6 bogus-uuid route probes (allowlists, allowlistEntries, origins, user/tokens, oauthAccounts/{id}/accessToken, wallets, custom/fields, deeplinkUrls, auth/clients, settings/exchanges, settings/providers): all fw-403 or method-405. VERDICT: NO exploitable IDOR (technique SECURED this round; complements round-1 20-endpoint sweep). Artifacts: recon/idor2_roundA.txt, idor2_roundB.txt, crossenv.txt, invite_x3_create/list.txt, idor2_invite_accept.txt, idor2_invite_delete.txt. Cleanup notes: pending invite 6d2032be left on victim org (harmless, A can delete); ctrl user b8227b75 on B's own env.
- 2026-10-26 01:15 UTC — **BUG-001 EXTENDED IMPACT DEMONSTRATION**. (1) Blast-radius test: created WH2 2f87eb7c-58ed-4f59-9dc2-bc3cf49f757d on victim sandbox (201; create response correctly omits secret), repointed to working inbox 72e683f6 (old inbox d8382db7 dead), triggered 2 users via users.write token (31863d96, 1eb69fdd) → both webhooks delivered; HMAC cross-check: SECRET_1 signs WH1 delivery (MATCH) but NOT WH2 → secrets are PER-WEBHOOK (honest negative — blast radius per receiver, not per-env; report states this). (2) LIVE env scope: victim live env = 3d4562eb-c8d6-496c-a508-6ca4b49ce5ad; webhook creation on live → 403 "Unauthorized: Live environment restricted" even for owner (support-gated), live env has zero webhooks — demo confined to sandbox, code path env-agnostic. (3) B re-established as viewer: new invite f256ab5a-cb65-4d2b-832d-7532f00a2d3f (old member record dead after removal), accepted via API, downgraded via PUT /members/f5e1e726-9bb4-4735-ae27-f57b0b29c90b {"role":"viewer"} → 200. Viewer harvested BOTH secrets cookieless (Authorization header only, spoofed UA): SECRET_1=dyn_Qfvm49… (WH1) + SECRET_2=dyn_[9fGd9CrAv6VDeKwott7hATen2[Wfeo:QTGWnsh9zOHJiSPuBZ1OkBqF (WH2) — SECRET_2 HMAC-verified against genuine WH2 delivery (exact match 137a45b4…). (4) NO self-service rotation: 525-op spec has only 3 "rotate" mentions, none webhook-related → stolen secret persists until manual intervention. (5) No session binding: all PoCs are cookieless non-browser replays. Report BUG-001-submission-final.md updated (Step 6 + extended Impact). State: B=viewer on victim org (member f5e1e726), WH2 active on victim sandbox (url 72e683f6 inbox), users 31863d96/1eb69fdd exist on victim sandbox, stale pending invite 6d2032be (zenovictim+x3) still on org. Artifacts: recon/wh2_secret_verify.txt, scripts/blast_radius_test.js.
- 2026-10-26 01:30 UTC — **BUG-001 FULL E2E FORGERY PoC EXECUTED LIVE (Steps 4+5, request-by-request)**. Script scripts/poc_e2e_forgery.js ran the complete chain in one session: (0) baseline 5 genuine deliveries in receiver inbox 72e683f6; (1) TRIGGER genuine user.created via users.write token → POST /environments/7dfe3b0c…/users 201, user 7526c359-2f4f-46f3-9a2c-23c1f23a075e (whforge+poc56181@example.com); (2) CAPTURED fresh delivery 701cbc0c-c24e-4524-aa2c-584c1c47159e @01:27:37Z, 1912 bytes, sig sha256=5fb5c66ff01f0991c7db28cc106ddf57ec43779b1c8c935c3df1bfd7426cc3a4; (3) STEP 4: HMAC-SHA256(SECRET, rawBody) == captured → EXACT MATCH=true — second independent confirmation on a NEW delivery+signature (first was 38260fc6… 2026-10-25 23:27); (4) STEP 5: forged user.created (509 B, attacker-chosen user, kycStatus=verified) signed with leaked secret sig sha256=4b993f1b2f72a86f41276d6797f38655f655ef024d1cc062d0a6faae2b9545a1 → POST to customer receiver HTTP 200, landed as inbox item ef98d209-8dd2-4ebe-ad42-c05985682a53; (5) RECEIVER-SIDE VERIFICATION MATRIX (HMAC-SHA256 + timingSafeEqual, Dynamic-documented scheme): GENUINE=VALID ✓, FORGED=VALID ✓ (accepted as authentic — indistinguishable), TAMPERED genuine body user.created→user.deleted=INVALID ✗, forged body+wrong-secret sig=INVALID ✗ → negatives prove verifier sound; forged passes ONLY because attacker holds the real key. No timestamp mixing/canonicalization/replay protection in scheme → forged events are byte-indistinguishable from Dynamic infrastructure output. Full request-by-request PoC with curl+node and live responses written to download/BUG-001-full-poc-forgery-chain.md and PUSHED to repo reports/BUG-001-full-poc-forgery-chain.md (commit bfd30c1e70). Artifacts: recon/poc_e2e_forgery_transcript.txt, recon/poc_e2e_forgery_console.txt. State: victim sandbox users now 7526c359 (+ prior eaacc556/31863d96/1eb69fdd); B still viewer member f5e1e726; WH2 still active; stale pending invite 6d2032be on org.
