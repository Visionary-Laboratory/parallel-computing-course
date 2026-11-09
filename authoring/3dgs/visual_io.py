"""Visual introduction to actual reconstruction inputs and learned outputs."""
import json, math
from html import escape
from pathlib import Path
MEDIA=Path(__file__).parent/'media'
BASE='../../materials/lectures/3dgs/media/'

def photo(i):
    return f'<img src="{BASE}garden-{i}.jpg" alt="Garden 场景的输入照片 {chr(65+i)}，从另一个拍摄位置观察同一张桌子" loading="lazy">'

def scene_frame(viewbox, label, switchable=False):
    x,y,w,h=viewbox.split(); clip='io-crop-'+x
    highlight='<rect x="390" y="475" width="265" height="190" fill="none" stroke="#ffc06b" stroke-width="3"/>' if x=='260' else ''
    return f'<svg class="io-scene-frame" viewBox="{viewbox}" role="img" aria-label="{label}"><defs><clipPath id="{clip}"><rect x="{x}" y="{y}" width="{w}" height="{h}"/></clipPath></defs><image {"data-scene-image" if switchable else ""} href="{BASE}garden-ellipsoids.png" width="1316" height="848" clip-path="url(#{clip})"/>{highlight}</svg>'

def camera_diagram():
    # Spatial relationship schematic. Both images are from the same stationary
    # camera in the official SIBR demo; the drawn camera pose is illustrative.
    return f'''<svg class="io-camera-diagram" viewBox="0 0 1200 440" role="img" aria-label="左侧相机朝向右侧的 Garden 高斯椭球场景，视锥中的成像平面显示该视角合成的桌子和花瓶图像">
    <defs><marker id="io-render-arrow" markerWidth="9" markerHeight="9" refX="7" refY="4.5" orient="auto"><path d="M0 0L8 4.5L0 9" fill="#176653"/></marker></defs>
    <g font-family="-apple-system,BlinkMacSystemFont,PingFang SC,Microsoft YaHei,sans-serif">
    <path d="M100 350L690 50L1150 80L1150 360L690 330Z" fill="#edf4ef" fill-opacity=".65"/>
    <g stroke="#9bb5a5" stroke-width="1.6" fill="none" stroke-dasharray="6 6"><path d="M100 350L690 50M100 350L1150 80M100 350L1150 360M100 350L690 330"/></g>
    <path d="M690 50L720 24L1180 54L1180 334L1150 360M1150 80L1180 54" stroke="#b7cbbc" fill="none" stroke-width="2"/>
    <g transform="matrix(1 .065217 0 1 690 50)"><svg width="460" height="280" viewBox="260 335 680 375" preserveAspectRatio="none"><image href="{BASE}garden-ellipsoids.png" width="1316" height="848"/></svg><rect width="460" height="280" fill="none" stroke="#61816d" stroke-width="2"/></g>
    <g transform="matrix(1 .065217 0 1 424.5 185)"><svg width="253" height="154" viewBox="260 335 680 375" preserveAspectRatio="none"><image href="{BASE}garden-splats.png" width="1316" height="848"/></svg><rect width="253" height="154" fill="none" stroke="#176653" stroke-width="4"/></g>
    <g fill="#284d3b" stroke="#284d3b" stroke-linejoin="round"><rect x="30" y="324" width="55" height="45" rx="6"/><path d="M85 335L105 325V365L85 355Z"/><path d="M54 369L40 395M64 369L80 395" fill="none" stroke-width="4"/></g>
    <circle cx="100" cy="350" r="4" fill="#cf8a42"/>
    <path d="M110 366L230 366" stroke="#61816d" stroke-width="2" marker-end="url(#io-render-arrow)"/>
    <text x="120" y="396" font-size="18" fill="#61796b">观察方向</text>
    <text x="25" y="297" font-size="23" fill="#253e2e">目标相机</text>
    <text x="430" y="150" font-size="23" fill="#176653">成像平面：这一帧图像</text>
    <text x="765" y="20" font-size="23" fill="#253e2e">三维场景：许多高斯椭球</text>
    <path d="M975 380C900 425 650 425 555 375" fill="none" stroke="#176653" stroke-width="2.5" marker-end="url(#io-render-arrow)"/>
    <text x="767" y="436" text-anchor="middle" font-size="20" fill="#176653">投影 → 排序 → 合成像素</text>
    </g></svg>'''

def walkthrough():
    return '''<div class="io-walkthrough" data-io>
    <div class="io-steps" role="tablist" aria-label="从训练输入到渲染输出">
      <button role="tab" id="io-tab-photos" aria-controls="io-photos" aria-selected="true">① 多视角照片</button>
      <button role="tab" id="io-tab-colmap" aria-controls="io-colmap" aria-selected="false" tabindex="-1">② 相机与初始点</button>
      <button role="tab" id="io-tab-gaussians" aria-controls="io-gaussians" aria-selected="false" tabindex="-1">③ 学好的高斯</button>
      <button role="tab" id="io-tab-render" aria-controls="io-render" aria-selected="false" tabindex="-1">④ 渲染一帧</button>
    </div>
    <section class="io-panel" id="io-photos" role="tabpanel" aria-labelledby="io-tab-photos">
      <h3>输入照片：同一个 Garden 场景，从不同位置拍摄</h3>
      <div class="io-photo-strip">'''+''.join(f'<figure>{photo(i)}<figcaption>照片 {chr(65+i)}</figcaption></figure>' for i in range(3))+'''
      </div>
      <p>三张照片里都有这张桌子，但桌面、花盆和背景的位置与可见部分不同。训练时，程序从各照片对应的相机位置渲染，再与这些<strong>真实照片</strong>比较。</p>
      <p class="io-caption">这里展示了其中三个拍摄视角；实际训练会使用更多视角的照片。</p>
    </section>
    <section class="io-panel" id="io-colmap" role="tabpanel" aria-labelledby="io-tab-colmap" hidden>
      <h3>COLMAP 的结果：把照片的拍摄位置和稀疏三维点放进同一空间</h3>
      <div class="io-colmap-grid"><div>
        <div class="io-cloud-wrap"><img class="io-cloud-static" src="'''+BASE+'''garden-colmap.svg" alt="Garden 的真实 COLMAP 稀疏点云及相机视锥，照片 A 的相机用橙色标出"><canvas class="io-cloud" width="760" height="420" role="img" aria-label="Garden 的真实稀疏点云和相机视锥，可用下方控件改变观察方向" hidden></canvas></div>
        <div class="io-cloud-controls"><label>绕场景观察 <input data-orbit type="range" min="-180" max="180" value="25" aria-label="绕点云观察的角度"></label><button data-eye aria-pressed="false">从相机 A 看点云</button></div>
        <p class="io-caption">彩色点标出估计出的三维位置；线框锥体表示相机的位置、朝向和视野范围。橙色相机与右侧选中的照片对应。</p>
      </div><div class="io-camera-card">
        <div class="io-camera-buttons" role="group" aria-label="选择照片及其相机"><button data-camera="0" aria-pressed="true">照片 A</button><button data-camera="1" aria-pressed="false">照片 B</button><button data-camera="2" aria-pressed="false">照片 C</button></div>
        <img class="io-selected-photo" src="'''+BASE+'''garden-0.jpg" alt="当前选中相机 A 拍到的 Garden 照片">
        <p class="io-camera-label">相机 A · 与左侧橙色视锥对应</p>
        <div class="io-camera-facts"><span><b>位置与朝向</b>：锥尖在哪里，锥体朝哪里。</span><span><b>焦距与成像范围</b>：锥口张角表示视野大小。</span></div>
        <p class="io-camera-values"></p>
      </div></div>
      <p>COLMAP 是从照片估计相机参数和三维点的软件。它匹配不同照片中的同一处细节，估计这些细节的三维位置；这些离散的三维点组成<strong>稀疏点云</strong>，为高斯中心提供初始位置。</p>
      <p class="io-load-status" role="status"></p>
    </section>
    <section class="io-panel" id="io-gaussians" role="tabpanel" aria-labelledby="io-tab-gaussians" hidden>
      <h3>还是这张桌子：许多高斯共同表示一个场景</h3>
      <div class="io-representation-controls" role="group" aria-label="查看高斯组成与渲染结果"><button data-representation="ellipsoids" aria-pressed="true">看组成场景的椭球</button><button data-representation="splats" aria-pressed="false">看同一视角的渲染结果</button></div>
      <div class="io-gaussian-scene"><figure>'''+scene_frame('260 335 680 375','Garden 的桌子和花瓶由许多高斯椭球组成',True)+'''<figcaption>场景中的桌子与花瓶 · 同一相机视角</figcaption></figure><figure>'''+scene_frame('390 475 265 190','桌面局部放大，可分辨大小和方向不同的高斯椭球',True)+'''<figcaption>桌面局部放大 · 对照形状与最终外观</figcaption></figure></div>
      <p>桌面、花瓶和地面由<strong>许多大小、方向不同的高斯共同表示</strong>。保存“学好的高斯参数”，就是保存这一整组高斯的位置、形状、不透明度和颜色参数。</p>
      <p class="io-caption">椭球轮廓连接高斯权重相同的位置，并不是硬外壳。切换到渲染结果，可以看到这些高斯的贡献如何共同形成场景外观。</p>
    </section>
    <section class="io-panel" id="io-render" role="tabpanel" aria-labelledby="io-tab-render" hidden>
      <h3>相机看向这组高斯，在成像平面上生成图像</h3>
      <figure>'''+camera_diagram()+'''<figcaption>同一场景、同一视角：右侧展示高斯的组成，成像平面展示合成结果。相机与视锥为空间关系示意，成像平面放在相机前方便于观察。</figcaption></figure>
      <p>给定相机，把高斯映射到表示图像的二维平面上，这一步称为<strong>投影</strong>。再将前后重叠的高斯按顺序合成像素颜色，就得到这一帧。训练时还要与对应照片比较、更新参数；渲染已学好的场景则到生成图像为止。</p>
    </section>
    <div class="io-step-footer"><span data-io-progress>1 / 4 · 多视角照片</span><button data-io-next>下一步：相机与初始点 →</button></div>
    <p class="io-sources">资料：<a href="https://jonbarron.info/mipnerf360/" target="_blank" rel="noreferrer">Garden 数据集</a> · <a href="https://viser.studio/main/examples/demos/colmap_visualizer/" target="_blank" rel="noreferrer">COLMAP 示例数据</a> · <a href="https://colmap.github.io/format.html" target="_blank" rel="noreferrer">相机参数定义</a> · <a href="https://github.com/graphdeco-inria/gaussian-splatting#running-the-real-time-viewer" target="_blank" rel="noreferrer">Kerbl 等：官方高斯可视化演示</a></p>
    </div>'''

def build_static(destination):
    """An offline/print view of the same real points and camera frusta."""
    data=json.loads((MEDIA/'garden-colmap.json').read_text());a=math.radians(25);e=math.radians(27);scale=420/(data['radius']*1.05)
    def project(p):
        x=math.cos(a)*p[0]+math.sin(a)*p[2];z=-math.sin(a)*p[0]+math.cos(a)*p[2]
        return [380+scale*x,225-scale*(math.cos(e)*p[1]-math.sin(e)*z)]
    svg=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 420"><rect width="760" height="420" fill="#15231e"/>']
    for p in data['points']:
        x,y=project(p[:3]);svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="1.2" fill="rgb({p[3]},{p[4]},{p[5]})"/>')
    for v,color,size in [(v,'#a4bcb0',.6) for v in data['cameras']]+[(data['views'][0],'#ffc06b',1.1)]:
        fx,fy,cx,cy=v['camera']['params'];w=v['camera']['width'];h=v['camera']['height'];c=v['center'];corners=[]
        for u,t in [(0,0),(w,0),(w,h),(0,h)]:
            corners.append([c[j]+size*(v['forward'][j]+(u-cx)/fx*v['right'][j]+(t-cy)/fy*v['down'][j]) for j in range(3)])
        for p,q in [(c,b) for b in corners]+[(corners[i],corners[(i+1)%4]) for i in range(4)]:
            x,y=project(p);xx,yy=project(q);svg.append(f'<path d="M{x:.1f},{y:.1f}L{xx:.1f},{yy:.1f}" fill="none" stroke="{color}" stroke-width="1.4"/>')
    svg.append('<text x="18" y="28" fill="#e1ede6" font-size="17" font-family="sans-serif">Garden · COLMAP 稀疏点云与相机</text></svg>')
    (Path(destination)/'garden-colmap.svg').write_text(''.join(svg))
