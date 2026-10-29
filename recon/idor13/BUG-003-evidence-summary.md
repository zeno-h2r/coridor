# BUG-003 (candidate) — emailVerifications verify: email-binding absent
## Attack chain (confirmed 2026-10-26 11:18–11:40 UTC)
1. UNAUTH POST /sdk/{env}/emailVerifications/create — arbitrary email + purpose (201)
2. Victim session JWT (stolen) — contains session_public_key claim in plaintext
3. POST /sdk/{env}/emailVerifications/verify with:
   - Authorization: Bearer <victim session minifiedJwt>
   - sessionPublicKey: <victim session public key — read from JWT claim, no private key needed>
   - verificationUUID + OTP delivered to ATTACKER-chosen email
   → 200 + fresh session for VICTIM user, attacker email attached as verified credential (signInEnabled: true)
## Control
- Same call with OTP for account's own email → 200, identical flow (own email re-attached)
## Key facts
- signin_credential_id in new session = original victim credential (added, not replaced)
- Check order: token-bound public-key match → UUID+OTP → mint. Private key possession never verified at this layer
- Rate limits: Cloudflare 1015 on verify bursts; OTP ~10 min validity
## Impact
Stolen-session-only attacker converts transient ≤24h session into persistent account control
via attacker-inbox OTP sign-in (persistence test in flight).
## Evidence files
- recon/idor11/vatk.full (attack 200 + session), vbase.full (control 200)
- recon/idor8/s1_spki.full (signin w/ own key), recon/idor10/* (ordering diagnostics)
