import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_OWNER').read().strip()
BUCKET="https://auditboard-files-qa-us-west-2.s3-accelerate.amazonaws.com"
for ext in ['html','htm','svg']:
    try: key=open(f'/tmp/key_{ext}').read().strip()
    except: continue
    url=f"{BUCKET}/{key}"
    print(f"=== {ext}: {key}")
    cmd=['curl','-s','-m','30','-i','-o','/tmp/anon','-w','%{http_code}',url]
    c=subprocess.run(cmd,capture_output=True,text=True).stdout.strip()
    body=open('/tmp/anon',encoding='utf-8',errors='replace').read()
    ct=[l for l in body.splitlines() if l.lower().startswith('content-type')]
    print(f"  anonymous GET -> {c}  {ct[0] if ct else 'no content-type'}")
    print(f"  body head: {body.split(chr(10)+chr(10))[-1][:120]!r}")
    print()
