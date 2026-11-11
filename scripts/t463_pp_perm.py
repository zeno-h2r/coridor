import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
def req(m,p,body=None,tok=None):
    cmd=['curl','-s','-m','25','-o','/tmp/b','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+tok,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== exact 422 reason for Owner on plan 154 ===")
tok=open('/tmp/bac_OWNER').read().strip()
c,b=req('GET','/api/v1/project_plans/154',tok=tok)
print(f"  {c} {b[:250].replace(chr(10),' ')}")
print()
print("=== RBAC: project_plan perms per role ===")
for r,rid in [('OWNER',5),('TESTER',4),('SYSADMIN',2)]:
    tok=open(f'/tmp/bac_{r}').read().strip()
    c,b=req('GET',f'/api/v1/role_permissions?role_id={rid}',tok=tok)
    try:
        rp=json.loads(b)['role_permissions']
        hits=[x for x in rp if 'projectPlan' in str(x.get('key','')) or 'project_plan' in str(x.get('key','')).lower()]
        print(f"  role {rid} ({r}): {len(hits)} projectPlan perms")
        for x in hits[:8]: print(f"    {x.get('key'):34} {x.get('value')}")
    except Exception as e: print(f"  role {rid}: {c}")
print()
print("=== write side: can Tester edit plan 154? ===")
TT=open('/tmp/bac_TESTER').read().strip()
for body in [{"project_plan":{"title":"ZXEDIT"}},{"project_plan":{"budget_hours":1}}]:
    c,b=req('PUT','/api/v1/project_plans/154',body,tok=TT)
    print(f"  Tester PUT {list(body['project_plan'].keys())} -> {c} {b[:110].replace(chr(10),' ')}")
print()
print("=== can Owner edit plan 154? (control) ===")
c,b=req('PUT','/api/v1/project_plans/154',{"project_plan":{"title":"ZXOWNER"}},tok=tok)
print(f"  Owner PUT -> {c} {b[:110].replace(chr(10),' ')}")
