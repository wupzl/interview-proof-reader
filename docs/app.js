(() => {
  'use strict';
  const root=document.documentElement, prefix='interview-proof-', chapter=Number(document.body.dataset.chapter)||0;
  const read=(key,fallback)=>{try{const s=localStorage.getItem(prefix+key);return s===null?fallback:JSON.parse(s)}catch{return fallback}};
  let parsed=read('records',null);
  if(!parsed||typeof parsed!=='object'||parsed.version!==1)parsed={version:1};
  const state={version:1,progress:parsed.progress&&typeof parsed.progress==='object'?parsed.progress:{},bookmarks:Array.isArray(parsed.bookmarks)?parsed.bookmarks:[],training:parsed.training&&typeof parsed.training==='object'?parsed.training:{},last:Number(parsed.last)||0};
  let toastTimer,failed=false;
  function toast(message){const target=document.querySelector('#toast');target.textContent=message;target.classList.add('visible');clearTimeout(toastTimer);toastTimer=setTimeout(()=>target.classList.remove('visible'),3500)}
  function save(){try{localStorage.setItem(prefix+'records',JSON.stringify(state));return true}catch{if(!failed){failed=true;toast('当前浏览器无法保存记录，请及时导出。')}return false}}
  function element(tag,text,className){const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(className)e.className=className;return e}
  async function copy(value){try{if(navigator.clipboard&&isSecureContext)await navigator.clipboard.writeText(value);else{const area=element('textarea',value);area.style.cssText='position:fixed;opacity:0';document.body.append(area);area.select();const success=document.execCommand('copy');area.remove();if(!success)throw Error('Unavailable')}toast('已复制，可粘贴到你选择的工具。');return true}catch{toast('复制未获浏览器允许，请使用导出功能。');return false}}
  function download(text,name,type){const blob=new Blob([text],{type}),url=URL.createObjectURL(blob),link=element('a');link.href=url;link.download=name;document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000)}
  window.Reader={state,save,toast,element,copy,download};
  const themes=['light','white','dark'],names={light:'米白',white:'纯白',dark:'深色'};
  function theme(value){root.dataset.theme=themes.includes(value)?value:'light';const button=document.querySelector('#theme');button.textContent=names[root.dataset.theme];button.setAttribute('aria-label','切换阅读背景，当前'+button.textContent);try{localStorage.setItem(prefix+'theme',root.dataset.theme)}catch{}}
  theme(root.dataset.theme);document.querySelector('#theme').addEventListener('click',()=>theme(themes[(themes.indexOf(root.dataset.theme)+1)%3]));
  let size=19;try{size=Math.max(16,Math.min(26,Number(localStorage.getItem(prefix+'size'))||19))}catch{}
  function resize(delta){size=Math.max(16,Math.min(26,size+delta));root.style.setProperty('--reading-size',size+'px');document.querySelector('#smaller').disabled=size<=16;document.querySelector('#larger').disabled=size>=26;try{localStorage.setItem(prefix+'size',String(size))}catch{}}
  document.querySelector('#smaller').addEventListener('click',()=>resize(-1));document.querySelector('#larger').addEventListener('click',()=>resize(1));resize(0);
  // Search renders source text through textContent; manuscript text never becomes markup.
  const dialog=document.querySelector('#search-dialog'),query=document.querySelector('#query'),results=document.querySelector('#search-results'),status=document.querySelector('#search-status');
  let promise=null,searchTimer,generation=0;
  const index=()=>promise||(promise=fetch('search.json').then(r=>{if(!r.ok)throw Error();return r.json()}).catch(e=>{promise=null;throw e}));
  function highlight(parent,text,word){const at=text.toLocaleLowerCase().indexOf(word);if(at<0){parent.textContent=text;return}parent.append(document.createTextNode(text.slice(0,at)),element('mark',text.slice(at,at+word.length)),document.createTextNode(text.slice(at+word.length)))}
  async function search(){const current=++generation,words=query.value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);results.replaceChildren();if(!words.length){status.textContent='输入关键词开始搜索';return}status.textContent='正在搜索…';try{const rows=await index();if(current!==generation)return;const found=rows.filter(item=>words.every(word=>(item.title+' '+item.section+' '+item.text).toLocaleLowerCase().includes(word)));status.textContent=found.length?`找到 ${found.length} 处线索${found.length>40?'，显示前 40 处':''}`:'未找到匹配内容，试试更短的关键词。';for(const item of found.slice(0,40)){const link=element('a',undefined,'search-result'),title=element('strong'),snippet=element('p');link.href=item.url;highlight(title,`第 ${item.chapter} 章 · ${item.section}`,words[0]);const start=Math.max(0,item.text.toLocaleLowerCase().indexOf(words[0])-45);highlight(snippet,(start?'…':'')+item.text.slice(start,start+170)+'…',words[0]);link.append(title,snippet);results.append(link)}}catch{if(current===generation)status.textContent='索引加载失败，请检查连接后重新输入。'}}
  document.querySelector('#search-open').addEventListener('click',()=>{dialog.showModal();query.focus()});document.querySelector('#search-close').addEventListener('click',()=>dialog.close());query.addEventListener('input',()=>{clearTimeout(searchTimer);searchTimer=setTimeout(search,120)});
  results.addEventListener('click',event=>{if(event.target.closest('a'))dialog.close()});
  document.addEventListener('keydown',event=>{if(event.key==='Escape'&&dialog.open){event.preventDefault();dialog.close()}if(event.key==='/'&&!/INPUT|TEXTAREA|SELECT/.test(event.target.tagName)&&!event.ctrlKey&&!event.metaKey){event.preventDefault();if(!dialog.open)dialog.showModal();query.focus()}});
  const resume=document.querySelector('#resume');if(resume&&state.last>=1&&state.last<=7){resume.href=`chapter-${String(state.last).padStart(2,'0')}.html?resume=1`;resume.textContent=`继续上次案卷 · 第 ${state.last} 章 →`;resume.hidden=false}
  document.querySelectorAll('[data-chapter-progress]').forEach(e=>{const p=state.progress[e.dataset.chapterProgress];if(p)e.textContent=p.maxPercent>=98?'· 已读完':`· 已读 ${p.maxPercent}%`});
  if(chapter){
    let ready=false,timer;
    const button=document.querySelector('#bookmark'),headings=[...document.querySelectorAll('article h2[id],article h3[id]')];
    const fraction=()=>Math.max(0,Math.min(1,scrollY/Math.max(1,document.documentElement.scrollHeight-innerHeight)));
    function section(){let h=null;for(const item of headings){if(item.getBoundingClientRect().top<innerHeight*.35)h=item;else break}return h}
    const key=()=>`${chapter}:${section()?.id||'start'}`;
    function bookmarkStatus(){const exists=state.bookmarks.some(b=>b.key===key());button.setAttribute('aria-pressed',String(exists));button.textContent=exists?'取消此处书签':'收藏当前位置'}
    function persist(){if(!ready)return;const percent=Math.round(fraction()*100),old=state.progress[chapter];state.progress[chapter]={percent,maxPercent:Math.max(old?.maxPercent||0,percent),fraction:fraction(),updatedAt:Date.now()};state.last=chapter;save()}
    function update(){const percent=Math.round(fraction()*100);document.querySelector('#progress').style.width=percent+'%';document.querySelector('#read-status').textContent=`本章 ${percent}%`;bookmarkStatus();clearTimeout(timer);timer=setTimeout(persist,200)}
    button.addEventListener('click',()=>{const k=key(),at=state.bookmarks.findIndex(b=>b.key===k);if(at>=0){state.bookmarks.splice(at,1);toast('已移除此处书签')}else{state.bookmarks.push({key:k,id:Date.now().toString(36)+Math.random().toString(36).slice(2,7),chapter,label:section()?.textContent||document.querySelector('h1').textContent,fraction:fraction()});toast('已收藏当前位置')}save();bookmarkStatus()});
    requestAnimationFrame(()=>requestAnimationFrame(()=>{const params=new URLSearchParams(location.search);if(!location.hash){const id=params.get('bookmark'),p=id?state.bookmarks.find(b=>b.id===id&&b.chapter===chapter):params.has('resume')?state.progress[chapter]:null;if(p&&Number.isFinite(p.fraction))scrollTo({top:p.fraction*Math.max(0,document.documentElement.scrollHeight-innerHeight),behavior:'instant'})}ready=true;update()}));
    addEventListener('scroll',update,{passive:true});addEventListener('resize',update);addEventListener('pagehide',persist);document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='hidden')persist()});
  }
  if(document.querySelector('#reading-progress')){
    function show(){const progress=document.querySelector('#reading-progress'),bookmarks=document.querySelector('#bookmarks'),training=document.querySelector('#training-records');progress.replaceChildren();bookmarks.replaceChildren();training.replaceChildren();
      for(let n=1;n<=7;n++){const p=state.progress[n];if(!p)continue;const row=element('div',undefined,'reading-item'),link=element('a',`第 ${n} 章 · ${p.maxPercent>=98?'已读完':'已读 '+p.maxPercent+'%'}`);link.href=`chapter-${String(n).padStart(2,'0')}.html?resume=1`;row.append(link,element('span','继续上次位置 →'));progress.append(row)}
      for(const b of [...state.bookmarks].reverse()){const row=element('div',undefined,'reading-item'),link=element('a',`第 ${b.chapter} 章 · ${b.label}`),remove=element('button','移除');link.href=`chapter-${String(b.chapter).padStart(2,'0')}.html?bookmark=${encodeURIComponent(b.id)}`;remove.setAttribute('aria-label','移除书签：'+b.label);remove.addEventListener('click',()=>{state.bookmarks=state.bookmarks.filter(x=>x.id!==b.id);save();show()});row.append(link,remove);bookmarks.append(row)}
      const labels={evidence:'项目真实性',followup:'连续追问',metrics:'指标论证',pitch:'黄金九十秒',questions:'反问清单',advantage:'优势证据',pressure:'压力面试'};
      for(const [id,record] of Object.entries(state.training)){const count=Object.values(record.drafts||{}).filter(d=>Object.values(d.fields||{}).some(v=>String(v).trim())||(d.picked||[]).length).length;if(!count)continue;const row=element('div',undefined,'reading-item'),link=element('a',labels[id]||id);link.href='practice.html#'+id;row.append(link,element('span',`${count} 份情境记录 · 继续练习 →`));training.append(row)}
      if(!progress.children.length)progress.append(element('p','尚无阅读记录，打开第一份案卷开始吧。'));if(!bookmarks.children.length)bookmarks.append(element('p','阅读时点击“收藏当前位置”，线索会保存在这里。'));if(!training.children.length)training.append(element('p','在面试训练中填写回答后，可从这里继续。'));
    }
    document.querySelector('#clear-records').addEventListener('click',()=>document.querySelector('#clear-confirm').hidden=false);document.querySelector('#clear-no').addEventListener('click',()=>document.querySelector('#clear-confirm').hidden=true);document.querySelector('#clear-yes').addEventListener('click',()=>{Object.assign(state,{version:1,progress:{},bookmarks:[],training:{},last:0});save();show();document.querySelector('#clear-confirm').hidden=true;toast('本书阅读与训练记录已清除')});show();
  }
})();
