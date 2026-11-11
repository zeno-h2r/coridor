import os,re,glob

H="https://bugbounty1.qe.optrostaging.ai"
ACCOUNTS = {
 'owner':   ("golden-snow-4771@bugcrowdninja.com",  "Zx9!Owner2026",   "5", "Owner"),
 'sysadmin':("zx-sysadm-66650c74@bugcrowdninja.com","TesterZx2026!",   "2", "System Admin"),
 'tester':  ("tester@soxhub.com",                   "Zx9!lower47",     "4", "Tester"),
 'tpu':     ("zx-6db21a8623@bugcrowdninja.com",     "TesterZx2026!",   "11","Third Party User (limited)"),
}

def block(acct, path, note=""):
    email,pw,uid,role = ACCOUNTS[acct]
    lines = [
      "## Access — how to reproduce",
      "",
      "```",
      f"Login to : {email}",
      f"Password  : {pw}",
      f"Role      : {role} (role_id {uid})",
      f"Navigate  : {H}{path}",
      "```",
      "",
      f"Header on every request: `X-Optro-Bug-Bounty: zeno0`",
    ]
    if note:
        lines += ["", note]
    return "\n".join(lines) + "\n\n---\n\n"

# per-report: (account, path, note)
PLAN = {
 'BUG-008-v2-submission-47.3.md':            ('owner','/sh/admin/settings','The `PUT /api/v1/users/{id}` endpoint is reachable from Settings → Users.'),
 'BUG-015-cross-user-file-delete.md':        ('owner','/workspace/5/issues/issues?config=all-active','Files attach to any record; the delete call is `DELETE /api/v1/files/{id}`.'),
 'BUG-016-ssrf-full-read-docx-embed.md':     ('owner','/workspace/5/issues/issues?config=all-active','The renderer is `POST /api/v1/attachments/html`; the artifact is downloaded via `GET /api/v1/files/{id}`.'),
 'BUG-017-lowest-role-email-hijack-ato.md':  ('tester','/sh/admin/settings','Log in as the Tester, then `PUT /api/v1/users/{victim_id}` with `{"user":{"email":"..."}}`.'),
 'BUG-018-rbac-matrix-disclosure.md':        ('tester','/sh/admin/settings','The leak is `GET /api/v1/role_permissions` and `?role_id=1`.'),
 'BUG-019-permission-inversion-owner-denied.md': ('owner','/workspace/7/risks/risk-list','Owner is denied `PUT /api/v1/risks/{id}`; Tester succeeds on the same object.'),
 'BUG-020-v2-assistant-bola-user-enumeration.md': ('tpu','/sh/narratives/38','Open the **Optro Assistant** button (top-right), type the prompt, press Send.'),
 'BUG-021-csp-no-effective-script-restriction.md': ('owner','/sh/my-dashboard/my-tasks','Header only — inspect any response with `curl -i`.'),
 'BUG-023-html-injection-comments-allowlist.md': ('sysadmin','/workspace/12/exceptions/33','Open **Comments**, post the payload, then inspect the DOM.'),
 'BUG-024-bfla-bulk-accept-control-implementation.md': ('sysadmin','/sh/narratives/38','Right-hand toolkit → **AI Suggested Controls** → **Accept**.'),
}

for fn,(acct,path,note) in PLAN.items():
    p=f'reports/{fn}'
    if not os.path.exists(p):
        print(f"  SKIP (missing) {fn}"); continue
    d=open(p,encoding='utf-8').read()
    if '## Access — how to reproduce' in d:
        print(f"  already has block: {fn}"); continue
    # insert after the header block (first '---' separator)
    idx=d.find('\n---\n')
    if idx<0:
        print(f"  no separator: {fn}"); continue
    ins = idx + len('\n---\n\n')
    d = d[:ins] + block(acct,path,note) + d[ins:]
    open(p,'w',encoding='utf-8').write(d)
    print(f"  ADDED {fn}  ({acct} -> {path})")
