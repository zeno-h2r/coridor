# Sumsub Dashboard (cockpit.sumsub.com) — Application Map
Target: https://cockpit.sumsub.com | Env: sandbox (X-SNS-Env: sbx) | Region: prd-euc1
Collected: 2026-10-25 from 226 JS chunks (static.sumsub.com/checkus/assets/)

## Architecture
- SPA shell: cockpit.sumsub.com/checkus/ → Vue 3 app (entry-et8x4no6.js)
- API: same-origin /resources/* (session cookie `at`, ES256 JWT, kid at-cookie-2026-10-12, 3-day exp)
- Data plane: api.sumsub.com (app-token HMAC auth) — edge-gated by Cloudflare Bot Fight Mode
- Session binding: IP-bound ("session-invalidated-mismatch" = network change logout)
- Captcha: reCAPTCHA v2 sitekey 6LdiyYcUAAAAAO_FEVcTbUOXqjhspAKdxV3rz3cp on login/signup/reset

## Feature Areas (777 /dashboard endpoints)
1. Applicants & verification: /dashboard/applicants/{id}/*, /dashboard/inspections/{id}/*
   - docs/images, media, securityFeatures, documentTranslations, videoIdent moderator flows
2. Case management v2: /dashboard/caseManagement/v2/{canvas,blueprints,sources}
3. AML/KYT: /dashboard/kyt/{rules,cases,txns,settings}, amlCases, watchlistHitStatus
4. Tokens & integrations: /dashboard/appTokens{,/-;id,/createTokenDefault,/getTokenDefault,/permissions,/rotate}
   - marketplaces: okta-idv, okta-idp-auth, hubspot, ashby (+ /token, /config each)
5. Levels & flows: /dashboard/applicants/-/levels{,/{id}}, sdkIntegrations/flows, levelLinks
6. Impersonation (STAFF FEATURE): X-Impersonate header + SidebarClientSwitcher,
   impersonatedClientId/impersonatedSubjectName URL params, impersonationAccessDenied states
7. Sessions & auth: /dashboard/auth/me/{info/sessions,logoutOther,logout,critical-actions/precheck},
   webauthn login/setup, 2FA authenticator/webauthn, msdkQrPayload (QR login)
8. Signup: /dashboard/signup/clientAccount/{request,verify/{id}}, signup/dueDiligenceToken
9. Billing/licenses: /dashboard/{billing/invoices,licenses/{trials,mine,domains},selfPurchase,pricebooks}
10. Misc: clientLists, reusableIdentity, questionnaires, documentExamples, videoIdent,
    temporaryAccess/{me/presets,me/request}, experiments, companyNews, clientBranding, globalSettings

## Auth endpoints
POST /resources/dashboard/auth/login/loginViaForm (urlencoded: name,password,userVerificationToken[,last2Fa])
POST /resources/dashboard/auth/login/loginViaFormWith2fa | loginViaFormWithWebauthn | loginStartWebauthn
POST /resources/dashboard/auth/reset/resetPasswordLink(WithAuthContext) | resetPassword
GET  /resources/dashboard/auth/me/-/isLoggedIn (public)
GET  /resources/dashboard/auth/me/{sharedInfo,info/sessions,productDetails,oauthConfig}
POST /resources/dashboard/auth/me/{logout,logoutOther}
SAML: /resources/auth/sso/metadata (public, IdP descriptor), /resources/auth/sso/login

## Key IDs observed (own accounts only)
- ss_aid ACCT-A: 6ade7e74ec5dacc7d5379e36 | ACCT-B: 6ade7e6ed58933f93542c954
- JWT sub/sid differ per account; org IDs not yet extracted (need session)

## Cross-account attack surface (2 test orgs available)
- All {ID}-parameterized endpoints (applicants, inspections, images, media, reports, appTokens)
- X-Impersonate header trust boundary (if regular user can set it → P1)
- appTokens/* management, levelLinks, webhook configs (cross-org write)
- /snsId/dashboard/profile/{id}/export, /dashboard/reports/{id}/download
