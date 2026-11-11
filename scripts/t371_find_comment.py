import json,subprocess,os
H=os.environ['H']; BB=os.environ['BB']
TOK=open('/tmp/bac_SYSADMIN').read().strip()
cmd=['curl','-s','-m','25',H+'/api/v1/comments','-H','token: '+TOK,'-H',BB]
d=json.loads(subprocess.run(cmd,capture_output=True,text=True).stdout)
cs=d['comments']
print(f"total comments visible to SysAdmin: {len(cs)}")
for c in cs:
    body=json.dumps(c)
    if 'ZXCMT1' in body or 'onerror' in body:
        print("\n*** FOUND OUR COMMENT ***")
        for k,v in c.items():
            if isinstance(v,(str,int,bool,type(None))):
                print(f"  {k:26} = {str(v)[:160]!r}")
        open('/tmp/cmnt.json','w').write(json.dumps(c))
        break
else:
    print("not in list; dumping keys of first")
    print(sorted(cs[0].keys()))
