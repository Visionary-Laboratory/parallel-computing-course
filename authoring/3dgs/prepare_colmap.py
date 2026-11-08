"""Extract a small reproducible teaching subset of Viser's public COLMAP Garden example.
Usage: python3 authoring/3dgs/prepare_colmap.py /path/to/colmap_garden.zip
This reads existing reconstruction outputs; it does not run SfM or train 3DGS.
"""
import io, json, math, random, struct, sys, zipfile
from pathlib import Path

def read(f, fmt): return struct.unpack('<'+fmt, f.read(struct.calcsize('<'+fmt)))
def dot(a,b): return sum(x*y for x,y in zip(a,b))
def normalize(v):
    n=math.sqrt(dot(v,v));return [x/n for x in v]
def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def rotation(q):
    w,x,y,z=q
    return [[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)], [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)], [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]]
def main(path):
    z=zipfile.ZipFile(path);base='colmap_garden/';out=Path(__file__).parent/'media';out.mkdir(exist_ok=True)
    f=io.BytesIO(z.read(base+'sparse/0/cameras.bin'));cams={}
    for _ in range(read(f,'Q')[0]):
        cid,model,w,h=read(f,'iiQQ');assert model==1, 'This example expects PINHOLE cameras'
        cams[cid]={'width':w,'height':h,'params':read(f,'dddd')}
    f=io.BytesIO(z.read(base+'sparse/0/images.bin'));views=[]
    for _ in range(read(f,'Q')[0]):
        vals=read(f,'i7di');iid=vals[0];q=vals[1:5];t=vals[5:8];cid=vals[8];name=b''
        while True:
            c=f.read(1)
            if c==b'\0':break
            name+=c
        count=read(f,'Q')[0];obs=[read(f,'ddq') for _ in range(count)]
        R=rotation(q);C=[-sum(R[j][i]*t[j] for j in range(3)) for i in range(3)]
        views.append(dict(id=iid,name=name.decode(),center=C,right=R[0],down=R[1],forward=R[2],camera=cams[cid],obs=obs))
    f=io.BytesIO(z.read(base+'sparse/0/points3D.bin'));points=[];total=read(f,'Q')[0]
    for _ in range(total):
        pid,x,y0,z0,r,g,b,e=read(f,'QdddBBBd');track=read(f,'Q')[0];f.seek(track*8,1)
        points.append(dict(id=pid,xyz=[x,y0,z0],rgb=[r,g,b]))
    views.sort(key=lambda v:v['name']);chosen=[views[10]]
    def distance(a,b):return sum((x-y)**2 for x,y in zip(a['center'],b['center']))
    while len(chosen)<3:
        chosen.append(max(views,key=lambda v:min(distance(v,c) for c in chosen)))
    # A rigid reorientation keeps all geometry and camera/photo correspondences intact.
    up=normalize([-sum(v['down'][j] for v in views) for j in range(3)])
    right=normalize(cross([0,0,1] if abs(up[2])<.9 else [1,0,0],up));forward=cross(right,up)
    basis=[right,up,forward];origin=[sorted(p['xyz'][j] for p in points)[len(points)//2] for j in range(3)]
    def vector(v):return [dot(ax,v) for ax in basis]
    def pos(v):return vector([v[j]-origin[j] for j in range(3)])
    radial=sorted(math.sqrt(dot(pos(p['xyz']),pos(p['xyz']))) for p in points)
    radius=radial[int(.9*len(radial))]
    cropped=[p for p in points if dot(pos(p['xyz']),pos(p['xyz']))<=radius*radius]
    sample=random.Random(7).sample(cropped,min(16000,len(cropped)))
    positions={p['id']:p['xyz'] for p in points}
    result={'scene':'Garden','originalPoints':total,'originalImages':len(views),'displayPoints':len(sample),'radius':radius,'points':[[*[round(x,5) for x in pos(p['xyz'])],*p['rgb']] for p in sample],'views':[], 'cameras':[]}
    for v in views[::6]:result['cameras'].append({'center':pos(v['center']),'right':vector(v['right']),'down':vector(v['down']),'forward':vector(v['forward']),'camera':v['camera']})
    for i,v in enumerate(chosen):
        photo='garden-'+str(i)+'.jpg';(out/photo).write_bytes(z.read(base+'images_8/'+v['name']))
        # Check the real world-to-camera transform against measured feature observations.
        errors=[]
        fx,fy,cx,cy=v['camera']['params']
        for u,w,pid in v['obs']:
            if pid not in positions:continue
            delta=[positions[pid][j]-v['center'][j] for j in range(3)]
            a,b,c=[dot(v[k],delta) for k in ('right','down','forward')]
            if c>0:errors.append(math.hypot(fx*a/c+cx-u,fy*b/c+cy-w))
        errors.sort();assert errors[len(errors)//2]<3, 'Pose/intrinsics parsing failed reprojection check'
        result['views'].append(dict(label=chr(65+i),name=v['name'],photo=photo,center=pos(v['center']),right=vector(v['right']),down=vector(v['down']),forward=vector(v['forward']),camera=v['camera'],medianReprojectionError=errors[len(errors)//2]))
    (out/'garden-colmap.json').write_text(json.dumps(result,separators=(',',':')))
    print(json.dumps({k:result[k] for k in ('originalPoints','originalImages','displayPoints','radius')}))
    for v in result['views']:print(v['name'],v['camera'],'center',v['center'],'median error',v['medianReprojectionError'])
if __name__=='__main__':main(sys.argv[1])
