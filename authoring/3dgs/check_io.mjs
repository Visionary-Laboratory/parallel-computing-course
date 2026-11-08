import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {projectFromCamera,frustumCorners} from './visual_io.mjs';
const data=JSON.parse(readFileSync(new URL('./media/garden-colmap.json',import.meta.url),'utf8'));
const dot=(a,b)=>a.reduce((s,v,i)=>s+v*b[i],0),near=(a,b)=>assert.ok(Math.abs(a-b)<1e-7,`${a} != ${b}`);
assert.equal(data.views.length,3);assert.equal(data.points.length,data.displayPoints);
for(const v of data.views){
  for(const a of ['right','down','forward'])near(dot(v[a],v[a]),1);
  near(dot(v.right,v.down),0);near(dot(v.right,v.forward),0);near(dot(v.down,v.forward),0);
  const {width:w,height:h,params:[fx,fy,cx,cy]}=v.camera;
  const front=v.center.map((x,i)=>x+v.forward[i]);
  const p=projectFromCamera(front,v,w,h);near(p[0],cx);near(p[1],cy);
  assert.equal(projectFromCamera(v.center.map((x,i)=>x-v.forward[i]),v,w,h),null);
  const corners=frustumCorners(v);
  [[0,0],[w,0],[w,h],[0,h]].forEach((q,i)=>{const p=projectFromCamera(corners[i],v,w,h);near(p[0],q[0]);near(p[1],q[1]);});
  assert.ok(v.medianReprojectionError<3);
  assert.ok(readFileSync(new URL(`./media/${v.photo}`,import.meta.url)).length>1000);
}
console.log('PASS: real camera bases, view-frustum projection, image links, and recorded feature reprojection checks.');
