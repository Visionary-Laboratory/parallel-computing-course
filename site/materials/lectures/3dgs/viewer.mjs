import {GAUSSIANS, tilePipeline, composite, gaussian2D} from './model.mjs';

const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
const body=document.body, slides=$$('.lecture-slide'), params=new URLSearchParams(location.search);
let mode=['present','print'].includes(params.get('mode'))?params.get('mode'):'read';
let deep=params.get('deep')==='1', index=0;
const hashId=()=>{try{return decodeURIComponent(location.hash.slice(1));}catch{return '';}};
const visible=()=>slides.filter(s=>deep||!s.classList.contains('deep'));
if(slides.some(s=>s.id===hashId()&&s.classList.contains('deep')))deep=true;
const initial=visible().findIndex(s=>s.id===hashId()); if(initial>=0)index=initial;

function updateURL(s) {
  const url=new URL(location.href);
  if(mode==='read')url.searchParams.delete('mode');else url.searchParams.set('mode',mode);
  if(deep)url.searchParams.set('deep','1');else url.searchParams.delete('deep');
  if(s)url.hash=s.id;
  history.replaceState(null,'',url);
}
function fitSlide(){
  body.style.removeProperty('--slide-scale');
  if(mode!=='present'||window.innerWidth<900)return;
  const slide=visible()[index];
  const available=window.innerHeight-$('.toolbar').getBoundingClientRect().height-$('.presentation-controls').getBoundingClientRect().height-32;
  const natural=slide.getBoundingClientRect().height;
  if(natural>available)body.style.setProperty('--slide-scale',String(Math.max(.45,available/natural)));
}
function render(focus=false) {
  const list=visible();index=Math.max(0,Math.min(index,list.length-1));
  body.classList.toggle('hide-deep',!deep);
  body.classList.toggle('present',mode==='present');
  body.classList.toggle('print-mode',mode==='print');
  $('#read').setAttribute('aria-pressed',String(mode==='read'));
  $('#present').setAttribute('aria-pressed',String(mode==='present'));
  $('#depth').setAttribute('aria-pressed',String(deep));
  $('#depth').textContent=deep?'收起深入阅读 8 页':'展开深入阅读 8 页';
  slides.forEach(s=>s.classList.toggle('current',s===list[index]));
  $('#progress').value=`${index+1} / ${list.length}`;
  $('#prev').disabled=index===0;
  $('#next').disabled=index===list.length-1&&!$('details.answer:not([open])',list[index]);
  $('#page-select').replaceChildren(...list.map((s,i)=>{const o=document.createElement('option');o.value=i;o.textContent=s.dataset.label+' · '+$('h2',s).textContent;o.selected=i===index;return o;}));
  $('#export').href=`?mode=print${deep?'&deep=1':''}`;
  if(mode==='present'){
    updateURL(list[index]);
    if(focus){window.scrollTo(0,0);list[index].focus({preventScroll:true});}
  }
  if(mode==='print'){
    $$('.answer').forEach(d=>{d.open=$('#print-answers').checked;});
  }
  fitSlide();
}
function setMode(next) {
  const active=mode==='read'?slides.find(s=>s.getBoundingClientRect().bottom>155&&!s.matches('.hide-deep .deep')):visible()[index];
  if(active){const i=visible().indexOf(active);if(i>=0)index=i;}
  mode=next;render(true);updateURL(visible()[index]);
  if(next==='read')visible()[index].scrollIntoView({behavior:'instant',block:'start'});
}
function next(){const a=$('details.answer:not([open])',visible()[index]);if(a){a.open=true;render();return;}if(index<visible().length-1){index++;render(true);}}
function prev(){if(index>0){index--;render(true);}}
$('#read').addEventListener('click',()=>setMode('read'));
$('#present').addEventListener('click',()=>setMode('present'));
$('#prev').addEventListener('click',prev);$('#next').addEventListener('click',next);
$('#page-select').addEventListener('change',e=>{index=Number(e.target.value);render(true);});
$('#depth').addEventListener('click',()=>{
  const current=visible()[index];deep=!deep;
  const list=visible();let at=list.indexOf(current);
  if(at<0){const abs=slides.indexOf(current);at=list.filter(s=>slides.indexOf(s)<abs).length-1;}
  index=Math.max(0,at);render();updateURL(mode==='present'?visible()[index]:null);
});
$$('a[data-target],.slide-label a').forEach(a=>a.addEventListener('click',e=>{
  const id=a.dataset.target||a.hash.slice(1),target=document.getElementById(id);if(!target)return;
  if(target.classList.contains('deep')&&!deep)deep=true;
  index=visible().indexOf(target);render();
  if(mode==='present'){e.preventDefault();render(true);}else updateURL(target);
}));
window.addEventListener('hashchange',()=>{const target=slides.find(s=>s.id===hashId());if(!target)return;if(target.classList.contains('deep'))deep=true;index=visible().indexOf(target);render();});
$('#menu').addEventListener('click',()=>{const open=body.classList.toggle('menu-open');$('#menu').setAttribute('aria-expanded',String(open));});
async function fullScreen(){try{if(document.fullscreenElement)await document.exitFullscreen();else await document.documentElement.requestFullscreen();}catch{$('#status').textContent='当前浏览器未允许全屏，可继续使用演示模式。';}}
$('#fullscreen').addEventListener('click',fullScreen);
document.addEventListener('keydown',e=>{
  if(e.target.closest('input,select,textarea,button,a,summary,[contenteditable]'))return;
  if(mode==='present'&&e.key==='ArrowRight'){e.preventDefault();next();}
  if(mode==='present'&&e.key==='ArrowLeft'){e.preventDefault();prev();}
  if(mode==='present'&&e.key.toLowerCase()==='f'){e.preventDefault();fullScreen();}
  if(e.key==='Escape'){body.classList.remove('menu-open');$('#menu').setAttribute('aria-expanded','false');}
});
$('#print-answers').checked=params.get('answers')==='1';
$('#print-answers').addEventListener('change',()=>{
  $$('.answer').forEach(d=>{d.open=$('#print-answers').checked;});
  const url=new URL(location.href);url.searchParams.set('answers',$('#print-answers').checked?'1':'0');history.replaceState(null,'',url);
});
$('#print-now').addEventListener('click',()=>window.print());
$$('.answer').forEach(d=>d.addEventListener('toggle',()=>{if(mode==='present'){$('#next').disabled=index===visible().length-1&&!$('details.answer:not([open])',visible()[index]);fitSlide();}}));
window.addEventListener('resize',fitSlide);
$$('img').forEach(img=>img.addEventListener('load',fitSlide));

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
    $('.demo-result',el).textContent=`Tile ${selected}\n候选数：${records.length}\n深度顺序：${records.length?records.map(p=>'G'+p.id+'(z='+p.depth+')').join(' → '):'空 → 背景'}\n范围：[${range.join(', ')})\n全图引用总数 M = ${pipe.total}`;
    $$('[data-tile]',el).forEach(b=>b.setAttribute('aria-pressed',String(Number(b.dataset.tile)===selected)));
  }
  $$('[data-tile]',el).forEach(b=>b.addEventListener('click',()=>{selected=Number(b.dataset.tile);draw();}));
  canvas.addEventListener('click',e=>{const r=canvas.getBoundingClientRect(),x=(e.clientX-r.left)*432/r.width-24,y=(e.clientY-r.top)*432/r.height-24;if(x>=0&&x<384&&y>=0&&y<384){selected=Math.floor(y/96)*4+Math.floor(x/96);draw();}});draw();
}
$$('[data-demo]').forEach(el=>({ellipse:ellipseDemo,blend:blendDemo,tiles:tilesDemo}[el.dataset.demo]?.(el)));
render();
if(mode==='read'&&initial>=0)requestAnimationFrame(()=>visible()[index].scrollIntoView({behavior:'instant'}));
