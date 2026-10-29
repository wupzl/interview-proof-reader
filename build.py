"""Build the complete static reader. No network or backend is required."""
from pathlib import Path
import html, json, re, shutil
import markdown

ROOT=Path(__file__).resolve().parent
DOCS=ROOT/'docs'
BOOK=json.loads((ROOT/'book.json').read_text(encoding='utf-8'))
CHAPTERS=BOOK['chapters']
PROJECTS=[('pytorch-apprentice','PyTorch：炼金术士的学徒'),('ai-era-reader','AI 纪元'),('data-empire-reader','数据帝国'),('rag-empire-reader','RAG 帝国'),('system-design-reader','系统设计'),('online-troubleshooting-reader','生产环境'),('coding-agent-reader','Agent 帝国'),('interview-proof-reader','面试官的审判'), ('langchain-empire-reader', 'LangChain 帝国')]

def page(title, body, chapter=0):
    menu=''.join(f'<a href="/{slug}/"'+(' aria-current="page"' if slug==BOOK['slug'] else '')+f'>{label}</a>' for slug,label in PROJECTS)
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light dark"><meta name="description" content="面试官的审判：七章技术面试小说，七组本地训练。从知道到讲清楚，让真实能力有据可循。"><title>{html.escape(title)} · 面试官的审判</title><script>try{{let t=localStorage.getItem('interview-proof-theme');document.documentElement.dataset.theme=['light','white','dark'].includes(t)?t:'light';document.documentElement.style.setProperty('--reading-size',Math.max(16,Math.min(26,Number(localStorage.getItem('interview-proof-size'))||19))+'px')}}catch(e){{}}</script><link rel="icon" href="favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="style.css"><script src="app.js" defer></script><script src="training.js" defer></script></head>
<body data-chapter="{chapter}"><a class="skip" href="#main">跳到正文</a><div id="progress" aria-hidden="true"></div><header class="site-header"><a class="brand" href="index.html"><span class="brand-seal" aria-hidden="true">证</span><span>面试官的审判<small>THE EVIDENCE OF UNDERSTANDING</small></span></a><nav class="shelf-nav" aria-label="学习项目导航"><a class="shelf-home" href="/">← 学习书架</a><details class="shelf-switch"><summary>切换项目</summary><div class="shelf-menu">{menu}</div></details></nav><div class="controls"><button id="search-open" title="搜索全书（/）">搜索</button><button id="smaller" aria-label="缩小字号">A−</button><button id="larger" aria-label="增大字号">A＋</button><button id="theme" aria-label="切换阅读背景">米白</button></div></header>
<nav class="section-nav" aria-label="本书导航"><a href="index.html">全书案卷</a><a href="practice.html">面试训练</a><a href="reading.html">我的阅读</a><a href="editorial.html">内容说明</a><span>连载 · 第八章待续</span></nav>
{body}
<footer><a class="footer-title" href="index.html">面试官的审判</a><p>让真实能力，有据可循。</p><div><a href="editorial.html">内容与技术说明</a><a href="https://github.com/wupzl/interview-proof-reader">GitHub ↗</a></div><small>七章正文 · 第八章预告 · 无需登录 · 记录保存在当前浏览器</small></footer>
<dialog id="search-dialog" aria-labelledby="search-title"><div class="dialog-heading"><h2 id="search-title">检索全书</h2><button id="search-close" aria-label="关闭搜索">×</button></div><label for="query">关键词</label><input id="query" type="search" placeholder="例如：个人贡献、Memory、评测" autocomplete="off"><p id="search-status" role="status">输入关键词开始搜索</p><div id="search-results"></div></dialog><div id="toast" role="status" aria-live="polite"></div></body></html>'''

def render(source):
    # Manuscript HTML is escaped. Generated HTML is owned exclusively by this builder.
    source=source.replace('<','&lt;').replace('>','&gt;') if re.search(r'<(?:script|iframe|style|img|svg|video)\b',source,re.I) else source
    md=markdown.Markdown(extensions=['fenced_code','tables','toc','sane_lists'],extension_configs={'toc':{'toc_depth':'2-3'}})
    return md.convert(source), md.toc

def main():
    DOCS.mkdir(exist_ok=True)
    search=[]; metadata=[]
    for i,item in enumerate(CHAPTERS):
        n=item['number']; source=(ROOT/'chapters'/f'{n:02}.md').read_text(encoding='utf-8').split('\n',1)[1]
        rendered,toc=render(source)
        minutes=max(5,round(len(re.sub(r'\s','',source))/430))
        url=f'chapter-{n:02}.html'
        metadata.append({**item,'url':url,'minutes':minutes})
        booknav=''.join(f'<a href="chapter-{c["number"]:02}.html"'+(' aria-current="page"' if c['number']==n else '')+f'><span>{c["number"]:02}</span> {html.escape(c["title"])}</a>' for c in CHAPTERS)
        prev=f'<a href="chapter-{n-1:02}.html">← 上一章</a>' if n>1 else '<a href="index.html">← 全书目录</a>'
        nxt=f'<a href="chapter-{n+1:02}.html">下一章 →</a>' if n<7 else '<a href="index.html">第八章待续 · 返回目录 →</a>'
        body=f'''<div class="reader-layout"><aside class="reader-aside"><a href="index.html">← 全书案卷</a><details class="book-toc"><summary>七章目录</summary><nav>{booknav}</nav></details><p class="eyebrow">本章线索</p>{toc}<a class="aside-training" href="practice.html#{['evidence','followup','metrics','pitch','questions','advantage','pressure'][i]}">进入本章训练 ↗</a></aside><main id="main" class="chapter-main"><div class="chapter-heading"><p class="eyebrow">CASE FILE {n:02} / 07 · 约 {minutes} 分钟</p><h1>{html.escape(item['title'])}</h1><p class="chapter-subtitle">{html.escape(item['topics'])}</p><div class="chapter-tools"><button id="bookmark" aria-pressed="false">收藏当前位置</button><span id="read-status" role="status"></span></div></div><details class="mobile-toc"><summary>章节与本章目录</summary><nav class="book-links">{booknav}</nav>{toc}</details><details class="editor-note"><summary>打开案卷前 · 阅读提示</summary><p>{html.escape(item['note'])}</p></details><article>{rendered}</article><section class="chapter-training"><p class="eyebrow">NOW, YOUR TURN</p><h2>把这一章，变成自己的表达。</h2><p>{html.escape(item['topics'])}。填写真实经历，查看考察点与参考思路，再带着证据复盘。</p><a class="button" href="practice.html#{['evidence','followup','metrics','pitch','questions','advantage','pressure'][i]}">进入第 {n} 组训练 →</a></section><nav class="chapter-nav" aria-label="上下章">{prev}{nxt}</nav></main></div>'''
        (DOCS/url).write_text(page(item['title'],body,n),encoding='utf-8')
        anchor='';heading=item['title']
        for part in re.split(r'(<h[23] id="[^"]+">.*?</h[23]>)',rendered,flags=re.S):
            m=re.fullmatch(r'<h[23] id="([^"]+)">(.*?)</h[23]>',part,flags=re.S)
            if m: anchor=m[1];heading=html.unescape(re.sub('<[^>]+>','',m[2]));continue
            text=html.unescape(re.sub('<[^>]+>',' ',part))
            if text.strip():search.append({'chapter':n,'title':item['title'],'section':heading,'url':url+('#'+anchor if anchor else ''),'text':re.sub(r'\s+',' ',text)})
    cards=''.join(f'<a class="case-card" href="{c["url"]}"><span class="case-number">{c["number"]:02}</span><div><h3>{html.escape(c["title"])}</h3><p>{c["topics"]}</p><small>约 {c["minutes"]} 分钟 <span data-chapter-progress="{c["number"]}"></span></small></div><span class="card-arrow" aria-hidden="true">↗</span></a>' for c in metadata)
    home=f'''<main id="main"><section class="hero"><div class="hero-copy"><p class="eyebrow"><span class="red-dot"></span> 一部关于技术、表达与信任的小说</p><h1>你知道。<br>但他<span>知道吗？</span></h1><p class="hero-intro">做过的项目，为什么讲起来像背过的答案？<br>跟随林远与周衡，在七场技术面试的审判里，<br class="desktop-break">把脑海中的理解，变成对方看得见的证据。</p><div class="hero-actions"><a class="button" href="chapter-01.html">打开第一份案卷 <span>→</span></a><a class="text-link" href="practice.html">直接进入训练 ↗</a></div><a id="resume" class="resume" href="chapter-01.html" hidden>继续上次阅读 →</a><div class="hero-stats"><span><strong>07</strong> 章故事</span><span><strong>07</strong> 组训练</span><span>连载中 · 第八章待续</span></div></div><div class="dossier" aria-label="面试官的审判书籍封面"><div class="dossier-top"><span>工程能力验证档案</span><span>VOL. 01</span></div><div class="dossier-title">面试官<br>的审判<span>THE INTERVIEW<br>TRIBUNAL</span></div><div class="dossier-rule"></div><p>陈述可以练习。<br>证据必须真实。</p><div class="evidence-stamp">有据可循<span>EXHIBIT / 001</span></div><div class="dossier-bottom"><span>问题 → 决策 → 验证</span><span>07 FILES</span></div></div></section><section class="thesis"><span class="eyebrow">本案核心</span><p>面试官看不见你的深夜。<br>但可以看见你的<span>判断、实现和验证。</span></p><a href="editorial.html">关于本书与训练 →</a></section><section class="catalog" id="catalog"><div class="section-title"><div><p class="eyebrow">THE CASE FILES</p><h2>七份案卷，一条证据链。</h2></div><span>按顺序读，也可以从困惑开始</span></div><div class="case-list">{cards}</div><div class="next-file"><span>08 / 待开启</span><p>思维透明化</p><small>第八章目前仅有预告，正文待续。</small></div></section><section class="training-invite"><p class="eyebrow">FROM UNDERSTANDING TO EVIDENCE</p><h2>读完之后，轮到你开口。</h2><p>从项目介绍到压力追问，把真实经历写成自己的证据卡。</p><a class="button" href="practice.html">开始七组面试训练 →</a><small>无需登录 · 浏览器本地保存 · 可导出 Markdown 与 JSON</small></section></main>'''
    (DOCS/'index.html').write_text(page('全书案卷',home),encoding='utf-8')
    bank=json.loads((ROOT/'assets/training.json').read_text(encoding='utf-8'))
    nav=''.join(f'<a href="#{t["id"]}"><span>{t["number"]:02}</span>{t["title"]}</a>' for t in bank)
    sections=''.join(f'<section class="training" id="{t["id"]}" data-training="{t["id"]}" aria-label="{t["title"]}"><div class="training-heading"><p class="eyebrow">EXERCISE {t["number"]:02} / 07</p><h2>{t["title"]}</h2><p>{t["subtitle"]}</p></div><div class="training-body"><p>正在打开训练材料…</p></div><a class="training-source" href="chapter-{t["number"]:02}.html">重读对应案卷 →</a></section>' for t in bank)
    practice=f'''<main id="main" class="practice-main"><div class="page-heading"><p class="eyebrow">THE PRACTICE DESK</p><h1>把理解，写成证据。</h1><p>七组训练，反复练习。先写自己的回答，再看考察点与参考思路。</p><p class="subtle">材料参考 Agent Runtime 与 RAG 检索项目；请按真实经历填写。自查清单用于复盘，不代表自动评分。</p><div class="export-actions"><button class="button" data-export="markdown">导出训练 Markdown ↓</button><button data-export="json">下载 JSON 备份</button></div></div><nav class="training-index" aria-label="训练导航">{nav}</nav><div id="training-status" role="status"></div>{sections}<noscript><p>训练填写与保存需要启用 JavaScript；七章正文可直接阅读。</p></noscript></main>'''
    (DOCS/'practice.html').write_text(page('面试训练',practice),encoding='utf-8')
    reading='''<main id="main" class="standalone"><div class="page-heading"><p class="eyebrow">YOUR EVIDENCE DESK</p><h1>我的阅读与记录</h1><p>继续上次的案卷，找回收藏的线索。</p></div><section class="reading-section"><h2>阅读进度</h2><div id="reading-progress"></div></section><section class="reading-section"><h2>我的书签</h2><div id="bookmarks"></div></section><section class="reading-section"><h2>训练记录</h2><div id="training-records"></div><div class="export-actions"><button data-export="markdown">导出训练 Markdown ↓</button><button data-export="json">下载全部 JSON 备份</button></div></section><details class="clear-records"><summary>管理本地记录</summary><p>清除会移除本书的阅读进度、书签和训练答案。请先导出需要保留的内容。</p><button id="clear-records">清除本书全部记录</button><div id="clear-confirm" hidden><p>确认清除？此操作无法撤销。</p><button id="clear-yes">确认清除</button><button id="clear-no">取消</button></div></details></main>'''
    (DOCS/'reading.html').write_text(page('我的阅读',reading),encoding='utf-8')
    editorial,_=render((ROOT/'EDITORIAL.md').read_text(encoding='utf-8'))
    (DOCS/'editorial.html').write_text(page('内容与技术说明','<main id="main" class="standalone"><article>'+editorial+'</article></main>'),encoding='utf-8')
    (DOCS/'chapters.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (DOCS/'search.json').write_text(json.dumps(search,ensure_ascii=False)+'\n',encoding='utf-8')
    for path in (ROOT/'assets').iterdir():
        if path.is_file():shutil.copyfile(path,DOCS/path.name)
    (DOCS/'.nojekyll').touch()
    nav='# 全书导航\n\n《面试官的审判》 · 七章正文 · 第八章待续\n\n'+ '\n'.join(f'- [第{c["number"]}章：{c["title"]}]({c["number"]:02}.md)' for c in CHAPTERS)+'\n'
    (ROOT/'chapters/00-全书导航.md').write_text(nav,encoding='utf-8')
    print(f'Built 11 static pages, {len(search)} search sections and seven training modules.')

if __name__=='__main__':main()
