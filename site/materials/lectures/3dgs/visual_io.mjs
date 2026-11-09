// A small Canvas viewer for real COLMAP outputs, not a 3DGS renderer.
const $=(s,r)=>r.querySelector(s), $$=(s,r)=>[...r.querySelectorAll(s)];
const dot=(a,b)=>a.reduce((s,v,i)=>s+v*b[i],0);
const add=(a,b)=>a.map((v,i)=>v+b[i]);
const mul=(a,k)=>a.map(v=>v*k);
const sub=(a,b)=>a.map((v,i)=>v-b[i]);
export function projectFromCamera(point,view,width,height){
  const p=sub(point,view.center),z=dot(p,view.forward);
  if(z<=.01)return null;
  const [fx,fy,cx,cy]=view.camera.params;
  return [(fx*dot(p,view.right)/z+cx)/view.camera.width*width,(fy*dot(p,view.down)/z+cy)/view.camera.height*height,z];
}
export function frustumCorners(view,depth=1.1){
  const [fx,fy,cx,cy]=view.camera.params,{width:w,height:h}=view.camera;
  return [[0,0],[w,0],[w,h],[0,h]].map(([u,v])=>add(view.center,mul(add(view.forward,add(mul(view.right,(u-cx)/fx),mul(view.down,(v-cy)/fy))),depth)));
}
export function mountVisualIO(root){
  const tabs=$$('[role=tab]',root), panels=$$('.io-panel',root),names=['多视角照片','相机与初始点','学好的高斯','渲染一帧'];
  let stage=0,data=null,selected=0,eye=false;
  const canvas=$('canvas',root),ctx=canvas.getContext('2d'),orbit=$('[data-orbit]',root),eyeButton=$('[data-eye]',root);
  function selectStage(i){
    stage=i;tabs.forEach((t,j)=>{t.setAttribute('aria-selected',String(i===j));t.tabIndex=i===j?0:-1;panels[j].hidden=i!==j;});
    $('[data-io-progress]',root).textContent=`${i+1} / 4 · ${names[i]}`;
    $('[data-io-next]',root).textContent=i===3?'回到输入照片 ↺':`下一步：${names[i+1]} →`;
    if(i===1)load();
  }
  tabs.forEach((t,i)=>{
    t.addEventListener('click',()=>selectStage(i));
    t.addEventListener('keydown',e=>{
      if(!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;
      e.preventDefault();e.stopPropagation();const n=e.key==='Home'?0:e.key==='End'?3:(i+(e.key==='ArrowRight'?1:3))%4;
      selectStage(n);tabs[n].focus();
    });
  });
  $('[data-io-next]',root).addEventListener('click',()=>selectStage((stage+1)%4));
  let representation='ellipsoids',printRepresentation='ellipsoids';
  function showRepresentation(mode){
    representation=mode;
    $$('[data-representation]',root).forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.representation===mode)));
    $$('[data-scene-image]',root).forEach((img,i)=>{
      img.setAttribute('href',new URL(`media/garden-${mode}.png`,import.meta.url).href);
      img.parentElement.setAttribute('aria-label',mode==='ellipsoids'?(i?'桌面局部放大，可分辨大小和方向不同的高斯椭球':'Garden 的桌子和花瓶由许多高斯椭球组成'):(i?'同一视角渲染结果的桌面局部放大':'同一视角下由高斯合成的 Garden 桌子与花瓶图像'));
    });
  }
  $$('[data-representation]',root).forEach(b=>b.addEventListener('click',()=>showRepresentation(b.dataset.representation)));
  let printSelection=0,printEye=false;
  window.addEventListener('beforeprint',()=>{printSelection=selected;printEye=eye;eye=false;chooseCamera(0);printRepresentation=representation;showRepresentation('ellipsoids');});
  window.addEventListener('afterprint',()=>{eye=printEye;chooseCamera(printSelection);showRepresentation(printRepresentation);});
  function orbitProject(p){
    const a=Number(orbit.value)*Math.PI/180,e=27*Math.PI/180,scale=420/(data.radius*1.05);
    const x=Math.cos(a)*p[0]+Math.sin(a)*p[2],z=-Math.sin(a)*p[0]+Math.cos(a)*p[2];
    return [380+scale*x,225-scale*(Math.cos(e)*p[1]-Math.sin(e)*z),Math.sin(e)*p[1]+Math.cos(e)*z];
  }
  function draw(){
    if(!data)return;
    const v=data.views[selected];ctx.fillStyle='#15231e';ctx.fillRect(0,0,760,420);
    const ratio=Math.min(760/v.camera.width,420/v.camera.height),fitW=v.camera.width*ratio,fitH=v.camera.height*ratio,padX=(760-fitW)/2,padY=(420-fitH)/2;
    const project=eye?p=>projectFromCamera(p,v,fitW,fitH):orbitProject;
    const points=data.points.map(p=>({p,q:project(p.slice(0,3))})).filter(v=>v.q).sort((a,b)=>b.q[2]-a.q[2]);
    // Fit the original camera aspect ratio inside the canvas without distortion.
    for(const {p,q} of points){
      const x=q[0]+(eye?padX:0),y=q[1]+(eye?padY:0);
      if(x<0||x>760||y<0||y>420)continue;
      if(eye&&(x<padX||x>padX+fitW||y<padY||y>padY+fitH))continue;
      ctx.fillStyle=`rgb(${p[3]},${p[4]},${p[5]})`;ctx.fillRect(x,y,eye?3.2:2,eye?3.2:2);
    }
    function camera(v,color,depth){
      const corners=frustumCorners(v,depth);ctx.strokeStyle=color;ctx.lineWidth=color==='#ffc06b'?2.5:1;
      for(const [p,q] of [...corners.map(c=>[v.center,c]),...corners.map((c,i)=>[c,corners[(i+1)%4]])]){
        const a=orbitProject(p),b=orbitProject(q);ctx.beginPath();ctx.moveTo(a[0],a[1]);ctx.lineTo(b[0],b[1]);ctx.stroke();
      }
    }
    if(!eye){data.cameras.forEach(c=>camera(c,'#77998a',.6));camera(v,'#ffc06b',1.1);const c=orbitProject(v.center);ctx.fillStyle='#ffc06b';ctx.font='bold 19px sans-serif';ctx.fillText(v.label,c[0]+9,c[1]-9);}
    ctx.fillStyle='#e0ede5';ctx.font='16px sans-serif';ctx.fillText(eye?`相机 ${v.label} 的视角 · 稀疏点不是完整图像`:'Garden · COLMAP 稀疏点云与相机',16,26);
  }
  function chooseCamera(i){
    selected=i;const label=String.fromCharCode(65+i),v=data?.views[i],photo=$('.io-selected-photo',root);
    photo.src=new URL(`media/garden-${i}.jpg`,import.meta.url).href;photo.alt=`相机 ${label} 的真实输入照片`;
    $('.io-camera-label',root).textContent=`相机 ${label}${eye?' · 左侧为该相机看到的稀疏点':' · 对应橙色视锥'}`;
    $$('[data-camera]',root).forEach((b,j)=>b.setAttribute('aria-pressed',String(i===j)));
    eyeButton.textContent=eye?'返回场景总览':`从相机 ${label} 看点云`;
    eyeButton.setAttribute('aria-pressed',String(eye));
    if(v){
      const {width,height,params:[fx,fy,cx,cy]}=v.camera;
      const fov=2*Math.atan(width/(2*fx))*180/Math.PI;
      $('.io-camera-values',root).textContent=`水平视野约 ${fov.toFixed(1)}°，表示相机从左到右能看到的角度范围。`;
    }
    draw();
  }
  $$('[data-camera]',root).forEach((b,i)=>b.addEventListener('click',()=>chooseCamera(i)));
  orbit.addEventListener('input',()=>{eye=false;eyeButton.setAttribute('aria-pressed','false');chooseCamera(selected);});
  eyeButton.addEventListener('click',()=>{eye=!eye;eyeButton.setAttribute('aria-pressed',String(eye));chooseCamera(selected);});
  let pending;
  async function load(){
    if(data){draw();return;}if(pending)return;
    const status=$('.io-load-status',root);status.textContent='正在载入本地点云…';
    pending=fetch(new URL('media/garden-colmap.json',import.meta.url)).then(r=>{if(!r.ok)throw Error('load');return r.json();}).then(d=>{
      data=d;canvas.hidden=false;$('.io-cloud-static',root).classList.add('io-static-print');chooseCamera(selected);status.textContent='';
    }).catch(()=>{status.textContent='交互点云未加载，仍可查看静态重建图。';pending=null;});
    await pending;
  }
  // Native print and PDF mode retain all four stages and the static reconstruction.
  if(document.body.classList.contains('print-mode'))return;
}
