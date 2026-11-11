import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_SYSADMIN').read().strip()
cmd=['curl','-s','-m','25',H+'/api/v1/comments','-H','token: '+TOK,'-H',BB]
d=json.loads(subprocess.run(cmd,capture_output=True,text=True).stdout)
for c in d['comments']:
    if str(c.get('id'))=='903':
        print(json.dumps(c,indent=1)[:1200])
        break
