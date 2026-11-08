import {GAUSSIANS, tilePipeline, composite, gaussian2D} from './model.mjs';

const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
const body=document.body, slides=$$('.lecture-slide');
let mode='read',deep=false,index=0;
const visible=()=>slides.filter(s=>deep||!s.classList.contains('deep'));
const hashId=()=>{try{return decodeURIComponent(location.hash.slice(1));}catch{return '';}};
function readLocation(){
  const p=new URLSearchParams(location.search),m=p.get('mode');
  mode=m==='slides'||m==='present'?'present':m==='print'?'print':'read';
  deep=mode==='print'||p.get('path')==='all'||p.get('deep')==='1';
  const id=p.get('topic')||hashId(),target=slides.find(s=>s.id===id);
  if(target?.classList.contains('deep'))deep=true;
  index=Math.max(0,visible().indexOf(target));
}
readLocation();
const initialId=visible()[index].id;
function updateURL(s,push=false){
  if(mode==='print')return;
  const url=new URL(location.href);
  ['mode','topic','path','deep','answers'].forEach(key=>url.searchParams.delete(key));
  if(mode==='present'){url.searchParams.set('mode','slides');url.searchParams.set('topic',s.id);url.hash='';}
  else if(s)url.hash=s.id;
  if(deep)url.searchParams.set('path','all');
  if(url.href!==location.href)history[push?'pushState':'replaceState'](null,'',url);
}
function updateContents(keepInView=true){
  const list=visible(), current=list[index];
  $$('.toc-position').forEach(el=>el.textContent=`${index+1} / ${list.length}`);
  $$('.toc-entry').forEach(row=>{
    const at=list.findIndex(s=>s.id===row.dataset.slide),active=current?.id===row.dataset.slide;
    row.hidden=at<0;row.classList.toggle('is-current',active);
    const link=$('a',row),idea=$('.toc-page-idea',row);
    link.href=mode==='present'?`?mode=slides&topic=${row.dataset.slide}${deep?'&path=all':''}`:`#${row.dataset.slide}`;
    link.setAttribute('aria-expanded',String(active));
    if(active)link.setAttribute('aria-current','location');else link.removeAttribute('aria-current');
    $('.toc-page-number',row).textContent=String(at+1).padStart(2,'0');
    idea.hidden=!active;
  });
  if(keepInView)$$('.toc-page-list').forEach(nav=>{
    if(!nav.clientHeight)return;
    const active=$('.is-current',nav);if(!active)return;
    const nr=nav.getBoundingClientRect(),ar=active.getBoundingClientRect();
    if(ar.top<nr.top)nav.scrollTop+=ar.top-nr.top-6;
    else if(ar.bottom>nr.bottom)nav.scrollTop+=ar.bottom-nr.bottom+6;
  });
}
function trackReadingPosition(){
  if(mode!=='read')return;
  const list=visible(),line=Math.min(220,Math.max(110,innerHeight*.25));
  let active=0;
  for(let i=0;i<list.length;i++){if(list[i].getBoundingClientRect().top<=line)active=i;else break;}
  if(active!==index){index=active;updateContents();if(list[index].getBoundingClientRect().top<=line)updateURL(list[index]);}
}
let scrollQueued=false;
window.addEventListener('scroll',()=>{
  if(scrollQueued)return;scrollQueued=true;
  requestAnimationFrame(()=>{scrollQueued=false;trackReadingPosition();});
},{passive:true});
function syncAnswers(){
  $$('.answer').forEach(d=>$('summary',d).textContent=d.open?'收起参考答案':'显示参考答案');
  const current=visible()[index];
  $('#prev').disabled=index===0&&!$('.answer[open]',current);
  $('#next').disabled=index===visible().length-1&&!$('.answer:not([open])',current);
}
function render(focus=false){
  const list=visible();index=Math.max(0,Math.min(index,list.length-1));
  body.classList.toggle('hide-deep',!deep);body.classList.toggle('present',mode==='present');body.classList.toggle('print-mode',mode==='print');
  for(const id of ['read','present']){const selected=mode===id;$('#'+id).setAttribute('aria-selected',String(selected));$('#'+id).tabIndex=selected?0:-1;}
  $('#lecture-panel').setAttribute('aria-labelledby',mode==='present'?'present':'read');
  $('#depth').setAttribute('aria-pressed',String(deep));
  $('#depth').textContent=deep?'全部内容 · 切回主线':'主线 · 展开深入阅读 8 页';
  slides.forEach(s=>{
    const n=list.indexOf(s);s.classList.toggle('current',s===list[index]);
    $('.page-number',s).textContent=String(n+1).padStart(2,'0');
    $('.slide-page-count',s).textContent=`${String(n+1).padStart(2,'0')} / ${list.length}`;
    $('.start-page',s).setAttribute('aria-label',`从第 ${n+1} 页开始浏览`);
  });
  $$('video').forEach(v=>{if(mode==='print'||(mode==='present'&&!v.closest('.lecture-slide').classList.contains('current')))v.pause();});
  $('#reading-count').textContent=`${list.length} 页`;
  $('#progress').value=`${index+1} / ${list.length}`;
  $('#slide-progress').max=list.length;$('#slide-progress').value=index+1;
  $('#slide-status').textContent=`第 ${index+1} 页 · ${$('h2',list[index]).textContent}`;
  if(mode==='present'&&focus){$('.slide-body',list[index]).scrollTop=0;list[index].focus({preventScroll:true});}
  if(mode==='print')$$('.answer').forEach(d=>d.open=$('#print-answers').checked);
  syncAnswers();updateContents();
}
function goTo(at,focus=true){
  index=Math.max(0,Math.min(at,visible().length-1));
  if(mode==='present')$$('.answer',visible()[index]).forEach(d=>d.open=false);
  render(focus);updateURL(visible()[index]);
}
function setMode(next){
  if(next===mode)return;
  mode=next;body.classList.remove('menu-open');$('#menu').setAttribute('aria-expanded','false');
  if(next==='read'){setFocused(false);if(document.fullscreenElement)document.exitFullscreen();}
  render(true);updateURL(visible()[index],true);
  if(next==='read')visible()[index].scrollIntoView({behavior:'instant',block:'start'});
  else window.scrollTo({top:0,behavior:'instant'});
}
function next(){
  const a=$('.answer:not([open])',visible()[index]);
  if(a){a.open=true;syncAnswers();a.scrollIntoView({block:'nearest',behavior:'smooth'});return;}
  if(index<visible().length-1)goTo(index+1);
}
function prev(){
  const a=$$('.answer[open]',visible()[index]).at(-1);
  if(a){a.open=false;syncAnswers();return;}
  if(index>0)goTo(index-1);
}
$('#read').addEventListener('click',()=>setMode('read'));
$('#present').addEventListener('click',()=>setMode('present'));
$('.mode-switch').addEventListener('keydown',e=>{
  if(!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;
  e.preventDefault();const id=e.key==='Home'?'read':e.key==='End'?'present':e.target.id==='read'?'present':'read';
  setMode(id);$('#'+id).focus();
});
$('#browse').addEventListener('click',()=>{index=0;setMode('present');});
$$('[data-start]').forEach(b=>b.addEventListener('click',()=>{index=visible().findIndex(s=>s.id===b.dataset.start);setMode('present');}));
$('#prev').addEventListener('click',prev);$('#next').addEventListener('click',next);
$('#depth').addEventListener('click',()=>{
  const current=visible()[index];deep=!deep;const list=visible();let at=list.indexOf(current);
  if(at<0){const abs=slides.indexOf(current);at=list.filter(s=>slides.indexOf(s)<abs).length-1;}
  index=Math.max(0,at);render();updateURL(list[index]);
  if(mode==='read')list[index].scrollIntoView({behavior:'instant',block:'start'});
});
$$('a[data-target],.slide-label a').forEach(a=>a.addEventListener('click',e=>{
  if(e.button||e.metaKey||e.ctrlKey||e.shiftKey||e.altKey)return;
  const target=document.getElementById(a.dataset.target||a.hash.slice(1));if(!target)return;
  e.preventDefault();if(target.classList.contains('deep'))deep=true;
  if($('#contents-dialog').open)$('#contents-dialog').close();
  goTo(visible().indexOf(target),mode==='present');
  if(mode==='read')target.scrollIntoView({behavior:'instant',block:'start'});
}));
function restoreLocation(){readLocation();render();if(mode==='read')visible()[index].scrollIntoView({behavior:'instant',block:'start'});}
window.addEventListener('popstate',restoreLocation);window.addEventListener('hashchange',restoreLocation);
$('#menu').addEventListener('click',()=>{const open=body.classList.toggle('menu-open');$('#menu').setAttribute('aria-expanded',String(open));});
function openContents(){$('#contents-dialog').showModal();updateContents();$('.is-current a',$('#contents-dialog')).focus({preventScroll:true});}
for(const id of ['contents-open','presentation-contents','page-picker'])$('#'+id).addEventListener('click',openContents);
$('#contents-close').addEventListener('click',()=>$('#contents-dialog').close());
$('#contents-dialog').addEventListener('click',e=>{if(e.target===$('#contents-dialog'))$('#contents-dialog').close();});
function setFocused(on){
  body.classList.toggle('focused',on);
  $('#fullscreen').setAttribute('aria-label',on?'退出全屏演示':'全屏演示');
  if(on)window.scrollTo({top:0,behavior:'instant'});
}
async function fullScreen(){
  if(body.classList.contains('focused')){setFocused(false);if(document.fullscreenElement)await document.exitFullscreen();return;}
  setFocused(true);
  try{await document.documentElement.requestFullscreen();}
  catch{$('#status').textContent='已进入专注演示。浏览器未允许系统全屏，按 F 或 Escape 返回。';}
}
$('#fullscreen').addEventListener('click',fullScreen);
document.addEventListener('fullscreenchange',()=>{
  setFocused(!!document.fullscreenElement);
});
document.addEventListener('keydown',e=>{
  if($('#contents-dialog').open||e.altKey||e.metaKey||e.ctrlKey||e.target.closest('input,select,textarea,video,[role="tab"],[contenteditable]'))return;
  if(e.target.closest('button,a,summary')&&[' ','Enter'].includes(e.key))return;
  if(e.key==='Escape'&&body.classList.contains('menu-open')){body.classList.remove('menu-open');$('#menu').setAttribute('aria-expanded','false');return;}
  if(mode!=='present')return;
  if(['ArrowRight','PageDown',' ','ArrowLeft','PageUp','Home','End','Escape','f','F'].includes(e.key))e.preventDefault();
  if(['ArrowRight','PageDown',' '].includes(e.key))e.shiftKey?prev():next();
  if(['ArrowLeft','PageUp'].includes(e.key))prev();
  if(e.key==='Home')goTo(0);if(e.key==='End')goTo(visible().length-1);
  if(e.key.toLowerCase()==='f')fullScreen();
  if(e.key==='Escape'){if(body.classList.contains('focused'))fullScreen();else setMode('read');}
});
$('#print-answers').checked=new URLSearchParams(location.search).get('answers')==='1';
$('#print-answers').addEventListener('change',()=>{
  $$('.answer').forEach(d=>d.open=$('#print-answers').checked);
  const url=new URL(location.href);url.searchParams.set('answers',$('#print-answers').checked?'1':'0');history.replaceState(null,'',url);syncAnswers();
});
$('#print-now').addEventListener('click',()=>{ $('#print-status').textContent='请在打印窗口中选择“另存为 PDF”，使用 A4，并关闭页眉和页脚。';window.print();});
$$('.answer').forEach(d=>d.addEventListener('toggle',syncAnswers));
$$('.copy-code').forEach(b=>b.addEventListener('click',async()=>{
  try{await navigator.clipboard.writeText($('code',b.closest('.code-block')).textContent);b.textContent='已复制';}
  catch{b.textContent='复制失败，请手动选择';}
  setTimeout(()=>b.textContent='复制代码',2000);
}));
window.addEventListener('resize',trackReadingPosition);

// Original project videos play within the lecture; no third-party player scripts.
$$('.scene-video').forEach(figure=>{
  const video=$('video',figure), error=$('.scene-error',figure);
  function loadScene(){error.hidden=true;video.src=video.dataset.src;video.load();}
  if(mode!=='print')loadScene();
  video.addEventListener('error',()=>{error.hidden=false;});
  video.addEventListener('loadeddata',()=>{error.hidden=true;});
  $('.scene-retry',figure).addEventListener('click',loadScene);
  $$('[data-scene]',figure).forEach(button=>button.addEventListener('click',()=>{
    video.pause();
    video.dataset.src=`https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/content/videos/${button.dataset.scene}.mp4`;
    video.setAttribute('aria-label',`${button.dataset.scene==='bicycle'?'Bicycle':'Garden'} 场景：原论文渲染视频`);
    $$('[data-scene]',figure).forEach(b=>b.setAttribute('aria-pressed',String(b===button)));
    loadScene();
  }));
  new IntersectionObserver(entries=>{if(!entries[0].isIntersecting)video.pause();}).observe(video);
});
document.addEventListener('visibilitychange',()=>{if(document.hidden)$$('video').forEach(v=>v.pause());});
window.addEventListener('beforeprint',()=>$$('video').forEach(v=>v.pause()));
async function preparePrint(){
  const images=$$('img');images.forEach(img=>img.loading='eager');
  await Promise.allSettled([document.fonts.ready,...images.map(img=>img.decode())]);
  const failed=images.filter(img=>!img.naturalWidth).length;
  $('#print-now').disabled=failed>0;
  $('#print-now').textContent='打印 / 保存为 PDF';
  $('#print-status').textContent=failed?`${failed} 张图片未加载，请刷新页面后重试。`:'';
}

const fmt=n=>n.toFixed(4).replace(/0+$/,'').replace(/\.$/,'');
function ellipseDemo(el){
  el.innerHTML=`<div class="demo-grid"><canvas width="480" height="320" role="img" aria-label="按当前尺度和角度计算的二维高斯热度图"></canvas><div class="demo-controls">
  <label>主轴尺度 σ₁ <output data-out="sx"></output><input aria-label="主轴尺度" data-key="sx" type="range" min="10" max="90" value="65"></label>
  <label>次轴尺度 σ₂ <output data-out="sy"></output><input aria-label="次轴尺度" data-key="sy" type="range" min="10" max="70" value="25"></label>
  <label>旋转角度 <output data-out="angle"></output><input aria-label="旋转角度" data-key="angle" type="range" min="-90" max="90" value="-25"></label>
  <label>不透明度 o <output data-out="opacity"></output><input aria-label="不透明度" data-key="opacity" type="range" min="10" max="100" value="80"></label>
  <div class="demo-buttons"><button data-reset>重置</button></div><p>虚线：2σ 等值线<br>中心 alpha = o；向外平滑衰减</p></div></div>`;
  const canvas=$('canvas',el),ctx=canvas.getContext('2d');
  function draw(){
    const v={};$$('input',el).forEach(i=>{v[i.dataset.key]=Number(i.value);$(`[data-out="${i.dataset.key}"]`,el).textContent=i.dataset.key==='opacity'?fmt(Number(i.value)/100):i.value+(i.dataset.key==='angle'?'°':'');});
    const angle=v.angle*Math.PI/180,img=ctx.createImageData(480,320);
    for(let y=0;y<320;y++)for(let x=0;x<480;x++){
      const a=gaussian2D(x-240,y-160,v.sx,v.sy,angle,v.opacity/100),i=(y*480+x)*4;
      img.data[i]=255-(255-23)*a;img.data[i+1]=255-(255-102)*a;img.data[i+2]=255-(255-83)*a;img.data[i+3]=255;
    }
    ctx.putImageData(img,0,0);ctx.strokeStyle='#176653';ctx.setLineDash([5,5]);ctx.beginPath();ctx.ellipse(240,160,2*v.sx,2*v.sy,angle,0,Math.PI*2);ctx.stroke();ctx.setLineDash([]);
    ctx.fillStyle='#176653';ctx.beginPath();ctx.arc(240,160,3,0,Math.PI*2);ctx.fill();
    ctx.font='13px sans-serif';ctx.fillStyle='#718779';ctx.fillText('μ',249,153);ctx.fillText('g(p) × o',15,25);
  }
  $$('input',el).forEach(i=>i.addEventListener('input',draw));$('[data-reset]',el).addEventListener('click',()=>{$$('input',el).forEach(i=>i.value=i.defaultValue);draw();});draw();
}
function blendDemo(el){
  el.innerHTML=`<div class="demo-grid"><div><canvas width="500" height="270" role="img" aria-label="当前步骤的累计颜色与剩余透射率"></canvas><div class="demo-buttons"><button data-back>上一步</button><button data-step>下一步</button><button data-reset>重置</button><button data-reverse>反转顺序</button></div></div><div><div class="swatch" aria-label="累计像素颜色"></div><div class="demo-result" aria-live="polite"></div><p>背景为黑色。颜色按线性 RGB 数值演示，屏幕色块只作定性辅助。</p></div></div>`;
  const base=[{id:0,alpha:.5,color:[1,0,0]},{id:2,alpha:.25,color:[0,1,0]},{id:1,alpha:.5,color:[0,0,1]}];
  let order=[...base],step=mode==='print'?3:0;const ctx=$('canvas',el).getContext('2d');
  function draw(){
    const r=composite(order.slice(0,step));ctx.clearRect(0,0,500,270);ctx.font='16px sans-serif';
    order.forEach((g,i)=>{ctx.fillStyle=i<step?'#e4f1e9':'#f3f5f4';ctx.fillRect(25+i*160,30,140,92);ctx.fillStyle='#285b41';ctx.fillText(`G${g.id} · α=${g.alpha}`,40+i*160,63);ctx.fillStyle=['#d46a57','#5686bd','#398e70'][g.id];ctx.fillRect(45+i*160,80,95,12);});
    ctx.fillStyle='#edf2ee';ctx.fillRect(25,175,450,28);ctx.fillStyle='#176653';ctx.fillRect(25,175,450*r.T,28);ctx.fillStyle='#567360';ctx.fillText(`剩余透射率 T = ${fmt(r.T)}`,25,238);
    $('.swatch',el).style.background=`rgb(${r.C.map(x=>Math.round(x*255)).join(',')})`;
    $('.demo-result',el).textContent=`步骤 ${step} / 3\n顺序：${order.map(g=>'G'+g.id).join(' → ')}\nC = (${r.C.map(fmt).join(', ')})\nT = ${fmt(r.T)}`;
    $('[data-back]',el).disabled=step===0;$('[data-step]',el).disabled=step===3;
  }
  $('[data-step]',el).addEventListener('click',()=>{step=Math.min(3,step+1);draw();});
  $('[data-back]',el).addEventListener('click',()=>{step=Math.max(0,step-1);draw();});
  $('[data-reset]',el).addEventListener('click',()=>{order=[...base];step=0;draw();});
  $('[data-reverse]',el).addEventListener('click',()=>{order.reverse();step=0;draw();});draw();
}
function tilesDemo(el){
  el.innerHTML=`<div class="demo-grid"><canvas width="432" height="432" role="img" aria-label="四个高斯的包围框及 4×4 Tile 网格"></canvas><div><div class="tile-buttons" role="group" aria-label="选择 Tile">${Array.from({length:16},(_,i)=>`<button aria-pressed="${i===5}" data-tile="${i}">${i}</button>`).join('')}</div><div class="demo-result" aria-live="polite"></div><p>红 G₀ · 蓝 G₁ · 绿 G₂ · 黄 G₃<br>半开包围框；图示不表示真实深度排序误差。</p></div></div>`;
  let selected=5;const canvas=$('canvas',el),ctx=canvas.getContext('2d'),pipe=tilePipeline();
  function draw(){
    ctx.clearRect(0,0,432,432);ctx.fillStyle='#fff';ctx.fillRect(0,0,432,432);
    const off=24,scale=6,tile=96;
    ctx.fillStyle='#e4f0e8';ctx.fillRect(off+(selected%4)*tile,off+Math.floor(selected/4)*tile,tile,tile);
    GAUSSIANS.forEach(g=>{ctx.strokeStyle=g.color;ctx.fillStyle=g.color;ctx.globalAlpha=.16;ctx.beginPath();ctx.ellipse(off+g.x*scale,off+g.y*scale,g.radius*scale*.8,g.radius*scale*.5,-.35,0,Math.PI*2);ctx.fill();ctx.globalAlpha=1;ctx.setLineDash([5,4]);ctx.strokeRect(off+(g.x-g.radius)*scale,off+(g.y-g.radius)*scale,2*g.radius*scale,2*g.radius*scale);ctx.setLineDash([]);ctx.beginPath();ctx.arc(off+g.x*scale,off+g.y*scale,3,0,Math.PI*2);ctx.fill();ctx.font='bold 13px sans-serif';ctx.fillText('G'+g.id,off+g.x*scale+5,off+g.y*scale-6);});
    ctx.strokeStyle='#bbcec1';ctx.lineWidth=1;for(let i=0;i<=4;i++){ctx.beginPath();ctx.moveTo(off+i*tile,off);ctx.lineTo(off+i*tile,408);ctx.stroke();ctx.beginPath();ctx.moveTo(off,off+i*tile);ctx.lineTo(408,off+i*tile);ctx.stroke();}
    ctx.font='12px sans-serif';ctx.fillStyle='#8a9d90';for(let i=0;i<16;i++)ctx.fillText(String(i),off+(i%4)*tile+6,off+Math.floor(i/4)*tile+16);
    const records=pipe.sorted.filter(p=>p.tile===selected),range=pipe.ranges[selected];
    $('.demo-result',el).textContent=`Tile ${selected}\n候选数：${records.length}\n深度顺序：${records.length?records.map(p=>'G'+p.id+'(z='+p.depth+')').join(' → '):'空 → 背景'}\n范围：[${range.join(', ')})\n全图高斯–Tile 配对记录总数 M = ${pipe.total}`;
    $$('[data-tile]',el).forEach(b=>b.setAttribute('aria-pressed',String(Number(b.dataset.tile)===selected)));
  }
  $$('[data-tile]',el).forEach(b=>b.addEventListener('click',()=>{selected=Number(b.dataset.tile);draw();}));
  canvas.addEventListener('click',e=>{const r=canvas.getBoundingClientRect(),x=(e.clientX-r.left)*432/r.width-24,y=(e.clientY-r.top)*432/r.height-24;if(x>=0&&x<384&&y>=0&&y<384){selected=Math.floor(y/96)*4+Math.floor(x/96);draw();}});draw();
}
$$('[data-demo]').forEach(el=>({ellipse:ellipseDemo,blend:blendDemo,tiles:tilesDemo}[el.dataset.demo]?.(el)));
render();
if(mode==='print')preparePrint();
if(mode==='read'&&(location.hash||new URLSearchParams(location.search).has('topic')))requestAnimationFrame(()=>document.getElementById(initialId).scrollIntoView({behavior:'instant'}));
