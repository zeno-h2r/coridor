import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
TT=open('/tmp/bac_TESTER').read().strip()
def req(m,p,body=None,tok=None):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+(tok or TT),'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== can Tester WRITE another user's timesheet entry? ===")
tag='ZXT'+uuid.uuid4().hex[:5]
# entry 43 belongs to user 1
for body in [{"timesheet_entry":{"comment":f"ZX{tag} written by tester"}},
             {"timesheet_entry":{"hours":99}},
             {"timesheet_entry":{"user_id":170}}]:
    c,b=req('PUT','/api/v1/timesheet_entries/43',body)
    print(f"  PUT {list(body['timesheet_entry'].keys())} -> {c} {b[:110].replace(chr(10),' ')}")
print()
print("=== read back entry 43 to see if anything landed ===")
c,b=req('GET','/api/v1/timesheet_entries/43')
try:
    o=json.loads(b)['timesheet_entries'][0]
    print(f"  user_id={o.get('user_id')} hours={o.get('hours')} comment={str(o.get('comment'))[:80]!r}")
except Exception as e: print("  ",c,b[:150])
print()
print("=== can Tester DELETE another user's entry? ===")
c,b=req('DELETE','/api/v1/timesheet_entries/46')
print(f"  DELETE entry 46 (user 1) -> {c} {b[:110].replace(chr(10),' ')}")
