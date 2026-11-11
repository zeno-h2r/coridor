import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
def req(m,p,body=None,tok=None):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X',m,H+p,
         '-H','token: '+tok,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System']
    if body is not None: cmd+=['-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
TT=open('/tmp/bac_TPU').read().strip()
print("=== TPU: ticketing/tickets/bulk with a REAL payload ===")
tag='ZXT'+uuid.uuid4().hex[:5]
# first find a valid credential_id — earlier error said credential_id expected number
for body in [
  {"create_ticket_payloads":[{"title":f"ZX{tag}","description":"probe"}]},
  {"create_ticket_payloads":[{"title":f"ZX{tag}","description":"probe","credential_id":1}]},
  {"create_ticket_payloads":[]},
]:
    c,b=req('POST','/api/v1/ticketing/tickets/bulk',body,tok=TT)
    print(f"\n  {json.dumps(body)[:90]}")
    print(f"    -> {c} {b[:250].replace(chr(10),' ')}")
print()
print("=== and the single-create path for comparison ===")
for body in [{"ticket":{"title":f"ZX{tag}"}},{"credential_id":1,"title":f"ZX{tag}"}]:
    c,b=req('POST','/api/v1/ticketing/tickets',body,tok=TT)
    print(f"  {json.dumps(body)[:70]} -> {c} {b[:180].replace(chr(10),' ')}")
