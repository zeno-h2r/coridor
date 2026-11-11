import json,subprocess,os
H=os.environ['H']; T=os.environ['T']; BB=os.environ['BB']
def req(path):
    cmd=['curl','-s','-m','30','-o','/tmp/b','-w','%{http_code}',H+path,'-H',BB]
    return subprocess.run(cmd,capture_output=True,text=True).stdout.strip(), open('/tmp/b',encoding='utf-8',errors='replace').read()
V="golden-leaf-3068@bugcrowdninja.com"
print("=== reset-token-info with email + reset_token ===")
for q in [f'reset_token=abc&email={V}', f'reset_token=abc&id=230',
          f'reset_token=1&email={V}', f'reset_token=&email={V}',
          f'reset_token=abc&identification={V}']:
    c,t=req(f'/api/v1/users/reset-token-info?{q}')
    print(f"  {q[:58]:60} -> {c}")
    print(f"      {t[:220].replace(chr(10),' ')}")
