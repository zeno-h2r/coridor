# Recon Coverage — cockpit.sumsub.com (sandbox)
Date: 2026-10-25 UTC

| Area | State | Evidence |
|------|-------|----------|
| SPA shell + HTML | COLLECTED | checkus.html 54KB, entry-et8x4no6.js |
| JS bundles (226 chunks, 13MB) | COLLECTED+ANALYZED | /js/, endpoint_inventory.{csv,json} |
| Endpoint inventory | ANALYZED | 796 method+path pairs |
| Unauthenticated GET sweep (341 normalized paths) | SECURITY-TESTED | 0× 200 — auth enforced |
| Login/signup/reset captcha gating | ANALYZED | userVerificationToken required on all 3 |
| Session IP-binding | CONFIRMED | error 2023 session-invalidated-mismatch on both ACCTs |
| api.sumsub.com edge | ANALYZED | CF Bot Fight Mode blocks curl (403 cfb) |
| SAML metadata endpoint | ANALYZED | public IdP descriptor, expected |
| Slack/TG placeholder creds in JS | ANALYZED | UI placeholder strings → P4/P5, discarded |
| X-Impersonate trust boundary | PENDING (needs session) | top cross-account target |
| appTokens mgmt authz | PENDING (needs session) | |
| Inspection/applicant IDOR between 2 orgs | PENDING (needs session) | |
| Webhook config SSRF (OAST) | PENDING (needs session) | |
| 2FA / webauthn flows | PENDING (needs session) | |
| temporaryAccess flows | PENDING (needs session) | |
