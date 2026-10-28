"""Publish authorized repositories using Git Credential Manager (memory only)."""
from pathlib import Path
import argparse,json,os,subprocess,urllib.request,urllib.error

ROOT=Path(__file__).resolve().parents[1]
OWNER='wupzl';SLUG='interview-proof-reader'

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['identity','publish-new','publish-navigation','status'])
    args=parser.parse_args()
    env={**os.environ,'GIT_TERMINAL_PROMPT':'0','GCM_INTERACTIVE':'never'}
    credential=subprocess.run(['git','credential','fill'],input='protocol=https\nhost=github.com\n\n',capture_output=True,text=True,env=env,check=True)
    fields=dict(line.split('=',1) for line in credential.stdout.splitlines() if '=' in line)
    token=fields.get('password')
    if not token:raise SystemExit('No existing GitHub credential available')
    def api(path,data=None,method=None):
        req=urllib.request.Request('https://api.github.com/'+path,data=json.dumps(data).encode('utf-8') if data is not None else None,method=method,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'interview-proof-reader-publisher'})
        try:
            with urllib.request.urlopen(req,timeout=40) as response:
                raw=response.read();return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as error:
            if error.code==404:return None
            raise RuntimeError(f'GitHub API {method or "GET"} {path}: HTTP {error.code}') from None
    def git(repo,*commands,capture=False):return subprocess.run(['git',*commands],cwd=repo,env=env,text=True,encoding='utf-8',capture_output=capture,check=True)
    user=api('user')
    if user['login']!=OWNER:raise SystemExit('Authenticated GitHub account does not match the intended owner')
    if args.action=='identity':
        repo=api(f'repos/{OWNER}/{SLUG}')
        print(json.dumps({'owner':user['login'],'new_repository_exists':repo is not None},ensure_ascii=False));return
    if args.action=='publish-new':
        repo=api(f'repos/{OWNER}/{SLUG}')
        if repo is None:
            repo=api('user/repos',{'name':SLUG,'private':False,'description':'面试官的审判 · 七章小说式技术面试阅读，七组本地训练与二十个情境','homepage':f'https://{OWNER}.github.io/{SLUG}/'})
            print('Created public repository: '+repo['html_url'],flush=True)
        if repo['private']:raise SystemExit('Unexpected existing private repository; refusing to change visibility')
        if not (ROOT/'.git').exists():
            if api(f'repos/{OWNER}/{SLUG}/branches'):raise SystemExit('Remote already has commits; inspect before attaching checkout')
            git(ROOT,'init','-b','main');git(ROOT,'remote','add','origin',f'https://github.com/{OWNER}/{SLUG}.git')
        if git(ROOT,'remote','get-url','origin',capture=True).stdout.strip()!=f'https://github.com/{OWNER}/{SLUG}.git':raise SystemExit('Unexpected origin')
        git(ROOT,'add','--all')
        if subprocess.run(['git','diff','--cached','--quiet'],cwd=ROOT).returncode:git(ROOT,'commit','-m','Build interview reader with seven evidence-based training modules')
        git(ROOT,'push','-u','origin','main')
        pages=api(f'repos/{OWNER}/{SLUG}/pages')
        if pages is None:pages=api(f'repos/{OWNER}/{SLUG}/pages',{'source':{'branch':'main','path':'/docs'}},'POST')
        if pages.get('source')!={'branch':'main','path':'/docs'}:raise SystemExit('Unexpected existing Pages source')
        print('Pages configured: '+pages['html_url'],flush=True)
    elif args.action=='publish-navigation':
        manifest=json.loads((ROOT/'integration-files.json').read_text(encoding='utf-8'))
        # Stage only enumerated navigation files; do not include unrelated local edits.
        for name,paths in manifest.items():
            path=ROOT.parent/name;expected='wupzl.github.io' if name=='bookshelf' else name
            if git(path,'remote','get-url','origin',capture=True).stdout.strip()!=f'https://github.com/{OWNER}/{expected}.git':raise SystemExit('Unexpected origin: '+name)
            git(path,'fetch','origin','--quiet')
            if git(path,'rev-list','--count','HEAD..@{u}',capture=True).stdout.strip()!='0':raise SystemExit(name+' has upstream changes; inspect before publishing')
            git(path,'add','--',*paths)
            if subprocess.run(['git','diff','--cached','--quiet'],cwd=path).returncode:git(path,'commit','-m','Connect Interview Tribunal to the learning bookshelf and reader navigation')
            git(path,'push');print('Published navigation: '+expected,flush=True)
    else:
        manifest=json.loads((ROOT/'integration-files.json').read_text(encoding='utf-8'))
        for name in [SLUG,*[('wupzl.github.io' if name=='bookshelf' else name) for name in manifest]]:
            pages=api(f'repos/{OWNER}/{name}/pages') or {};build=api(f'repos/{OWNER}/{name}/pages/builds/latest') or {};runs=api(f'repos/{OWNER}/{name}/actions/runs?per_page=2') or {}
            print(json.dumps({'repository':name,'pages_status':pages.get('status'),'url':pages.get('html_url'),'build_status':build.get('status'),'build_commit':build.get('commit'),'runs':[{'id':r['id'],'name':r['name'],'status':r['status'],'conclusion':r['conclusion'],'url':r['html_url']} for r in runs.get('workflow_runs',[])]},ensure_ascii=False),flush=True)

if __name__=='__main__':main()
