// Small, original numerical models shared by the classroom demos and checks.
export const GAUSSIANS = [
  {id:0, x:20, y:20, radius:8, depth:2, color:'#d46a57'},
  {id:1, x:26, y:12, radius:6, depth:4, color:'#5686bd'},
  {id:2, x:30, y:26, radius:10, depth:3, color:'#398e70'},
  {id:3, x:54, y:54, radius:4, depth:5, color:'#c89b40'},
];
export function exclusiveScan(counts) {
  let sum=0;
  return {offsets:counts.map(n=>{const v=sum;sum+=n;return v;}),total:sum};
}
export function tilesFor(g, size=16, width=64, height=64) {
  const out=[], nx=Math.ceil(width/size), ny=Math.ceil(height/size);
  const x0=Math.max(0,Math.floor((g.x-g.radius)/size));
  const x1=Math.min(nx,Math.ceil((g.x+g.radius)/size));
  const y0=Math.max(0,Math.floor((g.y-g.radius)/size));
  const y1=Math.min(ny,Math.ceil((g.y+g.radius)/size));
  for(let y=y0;y<y1;y++) for(let x=x0;x<x1;x++)out.push(y*nx+x);
  return out;
}
export function tilePipeline(gs=GAUSSIANS) {
  const covers=gs.map(g=>tilesFor(g)), counts=covers.map(t=>t.length);
  const {offsets,total}=exclusiveScan(counts);
  const pairs=gs.flatMap((g,i)=>covers[i].map(tile=>({tile,id:g.id,depth:g.depth})));
  const sorted=[...pairs].sort((a,b)=>a.tile-b.tile||a.depth-b.depth||a.id-b.id);
  const ranges=Array.from({length:16},()=>[0,0]);
  sorted.forEach((p,i)=>{if(i===0||sorted[i-1].tile!==p.tile)ranges[p.tile][0]=i;if(i===sorted.length-1||sorted[i+1].tile!==p.tile)ranges[p.tile][1]=i+1;});
  return {counts,offsets,total,pairs,sorted,ranges};
}
export function composite(items, background=[0,0,0]) {
  let T=1,C=[0,0,0]; const history=[];
  for(const g of items){const weight=T*g.alpha;C=C.map((v,i)=>v+weight*g.color[i]);T*=1-g.alpha;history.push({C:[...C],T,weight});}
  return {C,T,color:C.map((v,i)=>v+T*background[i]),history};
}
export function gaussian2D(dx,dy,sx,sy,angle=0,opacity=1) {
  const c=Math.cos(angle),s=Math.sin(angle),u=c*dx+s*dy,v=-s*dx+c*dy;
  return opacity*Math.exp(-.5*((u/sx)**2+(v/sy)**2));
}
