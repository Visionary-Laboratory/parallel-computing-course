"""Visual introduction to actual reconstruction inputs and learned outputs."""
import json, math
from html import escape
from pathlib import Path
MEDIA=Path(__file__).parent/'media'
BASE='../../materials/lectures/3dgs/media/'

def photo(i):
    return f'<img src="{BASE}garden-{i}.jpg" alt="Garden 场景的输入照片 {chr(65+i)}，从另一个拍摄位置观察同一张桌子" loading="lazy">'

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
      <div class="io-photo-strip">'''+''.join(f'<figure>{photo(i)}<figcaption>照片 {chr(65+i)} · {json.loads((MEDIA/"garden-colmap.json").read_text())["views"][i]["name"]}</figcaption></figure>' for i in range(3))+'''
      </div>
      <p>三张照片里都有这张桌子，但桌面、花盆和背景的位置与可见部分不同。它们是<strong>训练时用来比较的真实图像</strong>，不是模型生成的结果。</p>
      <p class="io-caption">来自 Mip-NeRF 360 的 Garden 数据，经 Viser 示例分发。展示原始照片的缩小版本；完整重建包含 185 个拍摄视角。</p>
    </section>
    <section class="io-panel" id="io-colmap" role="tabpanel" aria-labelledby="io-tab-colmap" hidden>
      <h3>COLMAP 的结果：把照片的拍摄位置和稀疏三维点放进同一空间</h3>
      <div class="io-colmap-grid"><div>
        <div class="io-cloud-wrap"><img class="io-cloud-static" src="'''+BASE+'''garden-colmap.svg" alt="Garden 的真实 COLMAP 稀疏点云及相机视锥，照片 A 的相机用橙色标出"><canvas class="io-cloud" width="760" height="420" role="img" aria-label="Garden 的真实稀疏点云和相机视锥，可用下方控件改变观察方向" hidden></canvas></div>
        <div class="io-cloud-controls"><label>绕场景观察 <input data-orbit type="range" min="-180" max="180" value="25" aria-label="绕点云观察的角度"></label><button data-eye aria-pressed="false">从相机 A 看点云</button></div>
        <p class="io-caption">彩色点是稀疏三维位置；线框锥体表示拍摄相机。橙色为当前照片的相机。仅抽样显示 16,000 个点、部分相机，远处点已裁剪。</p>
      </div><div class="io-camera-card">
        <div class="io-camera-buttons" role="group" aria-label="选择照片及其相机"><button data-camera="0" aria-pressed="true">照片 A</button><button data-camera="1" aria-pressed="false">照片 B</button><button data-camera="2" aria-pressed="false">照片 C</button></div>
        <img class="io-selected-photo" src="'''+BASE+'''garden-0.jpg" alt="当前选中相机 A 拍到的 Garden 照片">
        <p class="io-camera-label">相机 A · 与左侧橙色视锥对应</p>
        <div class="io-camera-facts"><span><b>位置与朝向</b>：锥尖在哪里，锥体朝哪里。</span><span><b>焦距与成像范围</b>：锥口张角表示视野大小。</span></div>
        <p class="io-camera-values"></p>
      </div></div>
      <p>COLMAP 根据照片中的对应特征估计相机参数和<strong>稀疏点云</strong>。这些点提供高斯中心的初始位置；尚未包含训练后高斯的尺度、方向与不透明度。</p>
      <p class="io-load-status" role="status"></p>
    </section>
    <section class="io-panel" id="io-gaussians" role="tabpanel" aria-labelledby="io-tab-gaussians" hidden>
      <h3>训练输出：许多有位置、形状和外观的三维高斯</h3>
      <div class="io-output-grid"><figure><img src="../../materials/lectures/3dgs/gaussian-anatomy.svg" alt="单个三维高斯的参数示意：中心决定位置，三个尺度与旋转决定椭球形状，颜色与不透明度影响贡献"><figcaption>课程示意：椭球表示一个等值面，方便看形状；高斯本身没有硬边界。</figcaption></figure>
      <figure class="io-paper-figure"><img src="'''+BASE+'''gaussians-paper-fig3.png" alt="原论文图3：左侧为 Train 场景渲染图，中间为局部放大，右侧缩小高斯以显示其各向异性形状"><figcaption><strong>真实训练结果（原论文图 3）</strong>：左边是渲染图，中间是局部放大，右边缩小高斯以露出形状。这里用 Train 场景观察基元的形状。</figcaption></figure></div>
      <p>“学好的高斯参数”就是把这些基元的位置、三个方向的尺度、朝向、不透明度和颜色参数保存下来。训练会调整它们，也会增加或删除高斯，<strong>不是简单地给每个初始点套上同样大小的球</strong>。</p>
    </section>
    <section class="io-panel" id="io-render" role="tabpanel" aria-labelledby="io-tab-render" hidden>
      <h3>同一个渲染器，训练时用来比较，查看时用来生成新视角</h3>
      <div class="io-render-grid"><div class="io-flow">
        <div><b>训练</b><p>照片 + 已知相机 + 初始点</p><span>↓ 初始化高斯，再反复渲染</span><p>与该相机的照片比较 → 调整高斯</p><span>↓</span><p><strong>保存学好的三维高斯</strong></p></div>
        <div><b>渲染</b><p>学好的高斯 + 一个目标相机</p><span>↓ 投影、排序、合成</span><p><strong>该相机看到的一帧图像 →</strong></p></div>
      </div><figure><img src="'''+BASE+'''garden-render.png" alt="原论文中 3DGS 对 Garden 场景生成的一帧渲染图"><figcaption>原论文的 Garden 渲染结果。与前两步为同一场景，采用论文给定的另一相机视角；本页展示已生成的结果。</figcaption></figure></div>
      <p>接下来先固定学好的高斯，讲清楚<strong>一帧怎样算出来</strong>；再回到训练时如何利用渲染结果更新参数。</p>
    </section>
    <div class="io-step-footer"><span data-io-progress>1 / 4 · 多视角照片</span><button data-io-next>下一步：相机与初始点 →</button></div>
    <p class="io-sources">资料：<a href="https://jonbarron.info/mipnerf360/" target="_blank" rel="noreferrer">Garden 数据集</a> · <a href="https://viser.studio/main/examples/demos/colmap_visualizer/" target="_blank" rel="noreferrer">COLMAP 示例数据</a> · <a href="https://colmap.github.io/format.html" target="_blank" rel="noreferrer">相机参数定义</a> · <a href="https://arxiv.org/html/2308.04079v1#S4" target="_blank" rel="noreferrer">3DGS 原论文图 3（CC BY 4.0）</a></p>
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
