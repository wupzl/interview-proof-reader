"""Verify content integrity, real browser interactions and responsive layouts."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urljoin,urlsplit,unquote
import hashlib,json,mimetypes,re
from playwright.sync_api import sync_playwright,expect

ROOT=Path(__file__).resolve().parent
DOCS=ROOT/'docs'
OUT=ROOT/'test-results'
BASE='https://reader.test/interview-proof-reader/'

class Links(HTMLParser):
    def __init__(self,path):
        super().__init__();self.ids=[];self.links=[];self.headings=0;self.feed(path.read_text(encoding='utf-8'))
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if 'id' in attrs:self.ids.append(attrs['id'])
        if tag=='h1':self.headings+=1
        if tag in ('a','script','link','img'):
            value=attrs.get('href') or attrs.get('src')
            if value:self.links.append(value)

def main():
    OUT.mkdir(exist_ok=True)
    files=sorted(DOCS.glob('*.html'));assert len(files)==11
    parsed={path:Links(path) for path in files}
    for path,data in parsed.items():
        assert data.headings==1,('H1',path.name)
        assert len(data.ids)==len(set(data.ids)),('duplicate IDs',path.name)
        for value in data.links:
            u=urlsplit(urljoin(BASE+path.name,value))
            if u.netloc!='reader.test' or not u.path.startswith('/interview-proof-reader/'):continue
            target=DOCS/unquote(u.path.removeprefix('/interview-proof-reader/'))
            if target.is_dir():target=target/'index.html'
            assert target.is_file(),(path.name,value)
            if u.fragment and target.suffix=='.html':assert unquote(u.fragment) in parsed[target].ids,(path.name,value)
    audit=json.loads((ROOT/'CONTENT_REVIEW.json').read_text(encoding='utf-8'))
    assert hashlib.sha256((ROOT/'source/interviewdescription.md').read_bytes()).hexdigest()==audit['sha256']
    source=ROOT.parent/'interviewdescription.md'
    if source.exists():assert source.read_bytes()==(ROOT/'source/interviewdescription.md').read_bytes()
    for n in range(1,8):
        text=(ROOT/'chapters'/f'{n:02}.md').read_text(encoding='utf-8')
        assert text.count('## 第一幕')==1,(n,'opening')
        assert len(text)>8000,(n,'unexpected prose loss')
        assert '\\[' not in text and '&#x20;' not in text
    first=(ROOT/'chapters/01.md').read_text(encoding='utf-8')
    assert '## 第十幕：最后一场模拟面试' in first and '## 尾声：面试官看不见你的深夜' in first
    assert not (DOCS/'chapter-08.html').exists()
    # Resume identity and contact details must never enter the published materials.
    for path in [*DOCS.iterdir(),ROOT/'EDITORIAL.md']:
        if path.suffix in ('.html','.json','.js','.md'):
            text=path.read_text(encoding='utf-8')
            assert not re.search(r'(?<!\d)1[3-9]\d{9}(?!\d)|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}',text),('private contact data',path.name)
    assert not list(ROOT.rglob('*.pdf')), 'The reference resume must remain outside the repository'
    bank=json.loads((DOCS/'training.json').read_text(encoding='utf-8'));assert len(bank)==7
    errors=[];missing=[]
    with sync_playwright() as p:
        browser=p.chromium.launch()
        context=browser.new_context(viewport={'width':1440,'height':1000},permissions=['clipboard-read','clipboard-write'],reduced_motion='reduce')
        def serve(route):
            u=urlsplit(route.request.url)
            if u.netloc!='reader.test':route.abort();return
            if not u.path.startswith('/interview-proof-reader/'):
                route.fulfill(status=200,body='<!doctype html><title>Learning bookshelf</title>');return
            path=DOCS/(unquote(u.path.removeprefix('/interview-proof-reader/')) or 'index.html')
            if path.is_file():route.fulfill(path=str(path),content_type=mimetypes.guess_type(path)[0] or 'application/octet-stream')
            else:missing.append(u.path);route.fulfill(status=404,body='Missing file')
        context.route('**/*',serve);page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
        for width in (390,768,1440):
            page.set_viewport_size({'width':width,'height':1000})
            for path in files:
                page.goto(BASE+path.name)
                if path.name=='practice.html':expect(page.locator('.training textarea[data-field=answer]')).to_have_count(7)
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),('overflow',width,path.name)
                expect(page.locator('.shelf-menu a')).to_have_count(8)
                page.locator('.shelf-switch summary').click();box=page.locator('.shelf-menu').bounding_box();assert box and box['x']>=0 and box['x']+box['width']<=width,('menu',width,box);page.locator('.shelf-switch summary').click()
                if path.name in ('index.html','chapter-01.html','practice.html'):page.screenshot(path=str(OUT/f'{path.stem}-{width}.png'),full_page=path.name=='index.html')
            print(f'PASS: 11 pages and navigation at {width}px',flush=True)
        page.goto(BASE+'index.html');themes=set()
        for _ in range(3):
            page.locator('#theme').click();theme=page.locator('html').get_attribute('data-theme');themes.add(theme);page.reload();assert page.locator('html').get_attribute('data-theme')==theme
        assert themes=={'light','white','dark'}
        page.goto(BASE+'chapter-01.html');page.locator('#larger').click();size=page.evaluate('getComputedStyle(document.documentElement).getPropertyValue("--reading-size")');page.reload();assert page.evaluate('getComputedStyle(document.documentElement).getPropertyValue("--reading-size")')==size
        page.locator('#search-open').click();page.locator('#query').fill('BM25');link=page.locator('.search-result[href^="chapter-01.html#"]').first;expect(link).to_be_visible();link.click();assert 'chapter-01.html#' in page.url
        page.locator('#search-open').click();page.locator('#query').fill('not-a-real-term-4920');expect(page.locator('#search-status')).to_contain_text('未找到');page.keyboard.press('Escape');expect(page.locator('#search-dialog')).not_to_be_visible()
        page.goto(BASE+'chapter-01.html');page.evaluate('scrollTo({top:(document.documentElement.scrollHeight-innerHeight)*.34,behavior:"instant"})');page.wait_for_function('JSON.parse(localStorage.getItem("interview-proof-records"))?.progress?.[1]?.percent>=33');page.locator('#bookmark').click();expect(page.locator('#bookmark')).to_have_attribute('aria-pressed','true')
        page.goto(BASE+'reading.html');expect(page.locator('#bookmarks .reading-item')).to_have_count(1);page.locator('#bookmarks a').click();page.wait_for_function('scrollY/(document.documentElement.scrollHeight-innerHeight)>.30');assert abs(page.evaluate('scrollY/(document.documentElement.scrollHeight-innerHeight)')-.34)<.03
        page.goto(BASE+'index.html');page.locator('#resume').click();page.wait_for_function('scrollY/(document.documentElement.scrollHeight-innerHeight)>.30')
        print('PASS: themes, font size, search, reading progress, bookmark and resume',flush=True)
        page.goto(BASE+'practice.html');expect(page.locator('.training textarea[data-field=answer]')).to_have_count(7)
        # Every scenario has an independent draft and self-check, with restored review.
        for item in bank:
            host=page.locator('#'+item['id'])
            for i,variant in enumerate(item['variants']):
                host.locator('select[aria-label$="训练情境"]').select_option(str(i))
                host.locator('.training-actions .button').click();expect(host.locator('.save-status')).to_contain_text('先写下')
                value=f'{item["id"]} scenario {i}: 真实职责、方案取舍、实验记录与边界。'
                host.locator('[data-field=answer]').fill(value)
                host.locator('.checklist input').first.check();host.locator('.training-actions .button').click();expect(host.locator('.review')).to_contain_text('1 / 4')
                host.locator('.reference-details summary').click();expect(host.locator('.reference-details p')).to_have_text(variant['reference'])
            page.reload();expect(host.locator('[data-field=answer]')).to_have_value(f'{item["id"]} scenario {len(item["variants"])-1}: 真实职责、方案取舍、实验记录与边界。');expect(host.locator('.review')).to_be_visible()
        # Cross-scenario persistence, maximum three questions, timer and arithmetic.
        evidence=page.locator('#evidence');evidence.locator('select').select_option('0')
        expect(evidence.locator('[data-field=answer]')).to_have_value('evidence scenario 0: 真实职责、方案取舍、实验记录与边界。')
        questions=page.locator('#questions');choices=questions.locator('.question-choices input')
        for i in range(3):choices.nth(i).check()
        choices.nth(3).click();expect(choices.nth(3)).not_to_be_checked();expect(questions.locator('.save-status')).to_contain_text('最多选择三个')
        metrics=page.locator('#metrics');expect(metrics.locator('.calculator output')).to_contain_text('+16.0 个百分点');expect(metrics.locator('.calculator output')).to_contain_text('+33.3%');metrics.locator('.calculator input').first.fill('0');expect(metrics.locator('.calculator output')).to_contain_text('无法计算');metrics.locator('.calculator input').first.fill('-1');expect(metrics.locator('.calculator output')).to_contain_text('请输入')
        pitch=page.locator('#pitch');pitch.locator('select[aria-label="选择训练时长"]').select_option('30');pitch.get_by_role('button',name='开始计时',exact=True).click();page.wait_for_function('document.querySelector(".timer-panel output").textContent!=="00:30"');pitch.get_by_role('button',name='暂停',exact=True).click();paused=pitch.locator('.timer-panel output').inner_text();page.wait_for_timeout(1100);assert pitch.locator('.timer-panel output').inner_text()==paused;pitch.get_by_role('button',name='重置',exact=True).click();expect(pitch.locator('.timer-panel output')).to_have_text('00:30')
        attack='<img src=x onerror="window.injected=true">真实实现';evidence.locator('[data-field=answer]').fill(attack);page.reload();expect(page.locator('#evidence [data-field=answer]')).to_have_value(attack);assert page.evaluate('!window.injected')
        page.locator('#evidence').get_by_role('button',name='复制 AI 点评提示词').click();clipboard=page.evaluate('navigator.clipboard.readText()');assert attack in clipboard and '不要编造' in clipboard
        with page.expect_download() as event:page.locator('[data-export=markdown]').click()
        export=Path(event.value.path()).read_text(encoding='utf-8');assert attack in export and '选中的反问' in export and '0.48' in export
        with page.expect_download() as event:page.locator('[data-export=json]').click()
        backup=json.loads(Path(event.value.path()).read_text(encoding='utf-8'));assert backup['format']=='interview-proof-backup' and len(backup['records']['training'])==7 and len(backup['records']['bookmarks'])==1
        page.goto(BASE+'reading.html');expect(page.locator('#training-records .reading-item')).to_have_count(7)
        page.locator('.clear-records summary').click()
        page.locator('#clear-records').click();page.locator('#clear-no').click();expect(page.locator('#bookmarks .reading-item')).to_have_count(1);page.locator('#clear-records').click();page.locator('#clear-yes').click();expect(page.locator('#bookmarks .reading-item')).to_have_count(0);expect(page.locator('#training-records .reading-item')).to_have_count(0)
        page.goto(BASE+'practice.html');expect(page.locator('#evidence [data-field=answer]')).to_have_value('')
        print('PASS: all 20 scenarios, draft restoration, review, timer, calculations, clipboard, exports and record management',flush=True)
        # Handle disabled storage without preventing drafting or deleting records.
        isolated=browser.new_context(viewport={'width':390,'height':900});isolated.route('**/*',serve);isolated.add_init_script('Storage.prototype.setItem=function(){throw new Error("Storage blocked")}');blocked=isolated.new_page();blocked.on('pageerror',lambda e:errors.append(str(e)));blocked.goto(BASE+'practice.html');expect(blocked.locator('.training textarea[data-field=answer]')).to_have_count(7);blocked.locator('#evidence [data-field=answer]').fill('不能保存时仍然可以填写');expect(blocked.locator('#evidence .save-status')).to_contain_text('无法保存');isolated.close()
        assert not errors,errors;assert not missing,missing
        browser.close()
    print('PASS: content preservation, privacy, links, responsive layout and browser features; no script errors.',flush=True)

if __name__=='__main__':main()
