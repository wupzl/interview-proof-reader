"""Connect the new book to seven readers, their generators and the bookshelf."""
from pathlib import Path
import json,re,subprocess

ROOT=Path(__file__).resolve().parents[2]
BOOK=ROOT/'interview-proof-reader'
SLUG=BOOK.name
READERS=['pytorch-apprentice','ai-era-reader','data-empire-reader','rag-empire-reader','system-design-reader','online-troubleshooting-reader','coding-agent-reader']
LINK=f'<a href="/{SLUG}/">面试官的审判</a>'
CHANGED={}

def edit(path,transform):
    old=path.read_text(encoding='utf-8');new=transform(old)
    if old!=new:
        path.write_text(new,encoding='utf-8')
        name=path.relative_to(ROOT).parts[0]
        CHANGED.setdefault(name,[]).append(str(path.relative_to(ROOT/name)).replace('\\','/'))

def menu(text):
    def add(match):return match[0] if f'/{SLUG}/' in match[1] else f'<div class="shelf-menu">{match[1]}{LINK}</div>'
    return re.sub(r'<div class="shelf-menu">(.*?)</div>',add,text,flags=re.S)

def generator(text):
    if f"('{SLUG}'" in text:return text
    for marker in ["('coding-agent-reader', 'Agent 帝国')","('coding-agent-reader','Agent 帝国')"]:
        if marker in text:return text.replace(marker,marker+f", ('{SLUG}', '面试官的审判')",1)
    raise AssertionError('Could not locate source generator project list')

def main():
    for slug in READERS:
        repo=ROOT/slug
        for page in (repo/'docs').glob('*.html'):edit(page,menu)
        if (repo/'build.py').exists():edit(repo/'build.py',menu if slug=='pytorch-apprentice' else generator)
        edit(repo/'README.md',lambda text:text if 'interview-proof-reader' in text else text+'\n\n项目切换菜单已接入 [面试官的审判](https://wupzl.github.io/interview-proof-reader/)，七章技术面试小说与七组本地训练，第八章待续。\n')
        if (repo/'verify.py').exists():
            edit(repo/'verify.py',lambda text:text.replace("page.locator('.shelf-menu a').count() == 7","page.locator('.shelf-menu a').count() == 8").replace("expect(page.locator('.shelf-menu a')).to_have_count(7)","expect(page.locator('.shelf-menu a')).to_have_count(8)"))
    shelf=ROOT/'bookshelf'
    card='''<a class="project tribunal" href="/interview-proof-reader/"><div class="cover" aria-hidden="true"><span class="volume">08 / THE INTERVIEW TRIBUNAL</span><strong>面试官<br>的审判</strong><span class="symbol">证</span><span class="cover-foot">陈述 · 决策 · 验证</span></div><div class="project-copy"><p class="category">技术面试 · 小说与训练</p><h3>面试官的审判</h3><p>跟随林远与周衡，把项目经历、技术判断和验证过程讲清楚，让面试官看见真实能力。七组本地训练，支持填写与导出。</p><div class="tags"><span>7 章 · 第八章待续</span><span class="project-status">连载</span><span>7 组训练 · 20 个情境</span></div><span class="enter">进入阅读 <span aria-hidden="true">↗</span></span></div></a>'''
    def home(text):
        if f'/{SLUG}/' not in text:
            marker='</div><div class="shelf-note">';assert marker in text
            text=text.replace(marker,card+marker,1)
        return text.replace('07 / 持续更新','08 / 持续更新')
    edit(shelf/'index.html',home)
    css='\n/* 面试官的审判：纸质卷宗与暗红证据印记。 */\n.project.tribunal .cover{background:#e6dece;color:#8c302b}.project.tribunal .symbol{font-family:SimSun,serif;opacity:.85}.project.tribunal .category{color:#8c302b}html[data-theme="dark"] .project.tribunal .category{color:#e49c8e}\n'
    edit(shelf/'bookshelf.css',lambda text:text if '.project.tribunal .cover' in text else text+css)
    def verifier(text):
        if f"'{SLUG}':" not in text:text=text.replace("    'coding-agent-reader': '第一卷完',","    'coding-agent-reader': '第一卷完',\n    'interview-proof-reader': '连载',")
        text=text.replace('seven','eight')
        marker="            assert '第十四章待续' in page.locator('.project[href=\"/pytorch-apprentice/\"] .tags').inner_text()"
        if "assert '第八章待续'" not in text:
            assert marker in text
            text=text.replace(marker,marker+"\n            assert '第八章待续' in page.locator('.project[href=\"/interview-proof-reader/\"] .tags').inner_text()")
        return text
    edit(shelf/'verify.py',verifier)
    def workflow(text):
        if f'repository: wupzl/{SLUG}' not in text:
            marker='      - uses: actions/setup-python@v5'
            assert marker in text
            text=text.replace(marker,f'      - uses: actions/checkout@v4\n        with:\n          repository: wupzl/{SLUG}\n          ref: main\n          path: {SLUG}\n'+marker,1)
            marker='      - name: Verify system design reader'
            text=text.replace(marker,'      - name: Verify interview reader features\n        run: python interview-proof-reader/verify.py\n'+marker,1)
            text=text.replace('            coding-agent-reader/test-results/','            coding-agent-reader/test-results/\n            interview-proof-reader/test-results/')
        return text.replace('all seven readers','all eight readers')
    edit(shelf/'.github/workflows/verify-readers.yml',workflow)
    edit(shelf/'README.md',lambda text:text.replace('Agent 帝国七个阅读项目','Agent 帝国和面试官的审判八个阅读项目').replace('其余七个仓库','其余八个仓库').replace('七项目切换菜单','八项目切换菜单').replace('七个阅读仓库','八个阅读仓库').replace('`coding-agent-reader/` 目录中','`coding-agent-reader/`、`interview-proof-reader/` 目录中').replace('Agent 帝国 9 章（第一卷完）。','Agent 帝国 9 章（第一卷完）、面试官的审判 7 章（连载，第八章待续）。')+ ('\n面试官的审判完整交互验收：`python interview-proof-reader/verify.py`。\n' if '面试官的审判完整交互验收' not in text else ''))
    manifest=BOOK/'integration-files.json'
    prior=json.loads(manifest.read_text(encoding='utf-8')) if manifest.exists() else {}
    for name,paths in CHANGED.items():prior[name]=sorted(set(prior.get(name,[])+paths))
    manifest.write_text(json.dumps(prior,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Integrated navigation; changed files: '+str(sum(map(len,CHANGED.values()))))

if __name__=='__main__':main()
