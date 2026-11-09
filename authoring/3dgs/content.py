"""Editable Chinese lecture. Original teaching text and examples; source links below.

Build with: python3 authoring/3dgs/build.py
No network, packages, or original private course generator required.
"""
from html import escape
from visual_io import walkthrough

TITLE = '3D Gaussian Splatting：从三维表示到 GPU 并行渲染'
SUBTITLE = '沿着一帧图像，理解高斯表示、透明合成、工作分组与 CUDA 协作。'
SOURCES = {
    'paper': ('Kerbl 等，3D Gaussian Splatting，SIGGRAPH 2023（CC BY 4.0）', 'https://arxiv.org/html/2308.04079v1'),
    'project': ('原论文项目：视频、场景与效果对照', 'https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/'),
    'forward': ('官方实现：forward.cu', 'https://github.com/graphdeco-inria/diff-gaussian-rasterization/blob/main/cuda_rasterizer/forward.cu'),
    'pipeline': ('官方实现：rasterizer_impl.cu', 'https://github.com/graphdeco-inria/diff-gaussian-rasterization/blob/main/cuda_rasterizer/rasterizer_impl.cu'),
    'backward': ('官方实现：backward.cu', 'https://github.com/graphdeco-inria/diff-gaussian-rasterization/blob/main/cuda_rasterizer/backward.cu'),
    'training': ('官方实现：train.py', 'https://github.com/graphdeco-inria/gaussian-splatting/blob/main/train.py'),
    'model': ('官方实现：gaussian_model.py', 'https://github.com/graphdeco-inria/gaussian-splatting/blob/main/scene/gaussian_model.py'),
}
TOPICS = [
    ('task', '从照片到新视角'), ('representation', '用高斯表示场景'),
    ('projection', '从三维到屏幕'), ('compositing', '从覆盖到颜色'),
    ('tiles', '把工作组织成 Tile'), ('execution', 'GPU 怎样执行'),
    ('learning', '场景怎样学出来'), ('performance', '性能、质量与总结'),
]
SLIDES = []

def p(text): return '<p>' + text + '</p>'
def note(text): return '<div class="takeaway">' + text + '</div>'
def flow(text): return '<div class="equation">' + text + '</div>'
def math_eq(body, label):
    return '<div class="equation"><math xmlns="http://www.w3.org/1998/Math/MathML" display="block" aria-label="'+escape(label,quote=True)+'">'+body+'</math></div>'
def math_inline(body):
    return '<math xmlns="http://www.w3.org/1998/Math/MathML">'+body+'</math>'
def mi(value): return '<mi>'+escape(value)+'</mi>'
def mn(value): return '<mn>'+str(value)+'</mn>'
def mo(value): return '<mo>'+escape(value)+'</mo>'
def mr(*parts): return '<mrow>'+''.join(parts)+'</mrow>'
def sub(base, index): return '<msub>'+base+'<mi mathvariant="normal">'+escape(index)+'</mi></msub>'
def sup(base, exponent): return '<msup>'+base+'<mn>'+str(exponent)+'</mn></msup>'
def tr(base): return '<msup>'+base+'<mi mathvariant="normal">T</mi></msup>'
def frac(numerator, denominator): return '<mfrac>'+mr(numerator)+mr(denominator)+'</mfrac>'
def par(body): return mr(mo('('),body,mo(')'))
def matrix(rows):
    return mr(mo('['),'<mtable>'+''.join('<mtr>'+''.join('<mtd>'+cell+'</mtd>' for cell in row)+'</mtr>' for row in rows)+'</mtable>',mo(']'))
GAP='<mspace width="1.5em"/>'
def math_matrix(rows):
    return '<mrow><mo>[</mo><mtable>'+''.join('<mtr>'+''.join('<mtd><mn>'+str(v)+'</mn></mtd>' for v in row)+'</mtr>' for row in rows)+'</mtable><mo>]</mo></mrow>'
def table(head, rows):
    return '<div class="table-scroll"><table><thead><tr>' + ''.join('<th scope="col">'+c+'</th>' for c in head) + '</tr></thead><tbody>' + ''.join('<tr>'+''.join('<td>'+str(c)+'</td>' for c in row)+'</tr>' for row in rows) + '</tbody></table></div>'
def code(text): return '<div class="code-block"><div class="code-label"><span>教学伪代码</span><button class="copy-code">复制代码</button></div><pre><code>' + escape(text.strip()) + '</code></pre></div>'
def columns(*items): return '<div class="teaching-columns">' + ''.join('<div>'+item+'</div>' for item in items) + '</div>'
FIGURE_HEIGHTS = dict(scene=300, pipeline=195, **{'point-splat':285,'covariance-rotation':260}, camera=265, projection=310, ownership=340, shared=345, barriers=235, imbalance=330, training=225, gradients=340, density=235)
def fig(name, caption): return f'<figure><a href="../../materials/lectures/3dgs/{name}.svg" target="_blank" rel="noopener" title="打开原图"><img src="../../materials/lectures/3dgs/{name}.svg" width="800" height="{FIGURE_HEIGHTS[name]}" alt="{escape(caption, quote=True)}" loading="lazy"></a><figcaption>{caption}</figcaption></figure>'
def demo(name, caption): return f'<div class="demo" data-demo="{name}"></div><p class="caption">{caption}</p>'
def answer(text): return '<details class="answer"><summary>显示参考答案</summary><div><h3 class="answer-print-title">参考答案</h3>'+text+'</div></details>'
def add(id, topic, title, *body, refs=(), deep=False):
    SLIDES.append(dict(id=id, topic=topic, title=title, html='\n'.join(body), refs=list(refs), deep=deep))

add('novel-view', 'task', '拍过的照片，怎样变成没有拍过的视角？',
    '''<div class="scene-intro"><figure class="scene-video">
      <div class="scene-player"><video controls muted playsinline preload="metadata" aria-label="Bicycle 场景：原论文渲染视频" data-src="https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/content/videos/bicycle.mp4"></video></div>
      <div class="scene-controls" role="group" aria-label="选择真实场景">
        <button type="button" data-scene="bicycle" aria-pressed="true">Bicycle · 自行车</button>
        <button type="button" data-scene="garden" aria-pressed="false">Garden · 花园</button>
      </div>
      <div class="scene-error" hidden role="status">视频暂未加载成功，请检查网络后<button type="button" class="scene-retry">重新加载</button>。</div>
      <figcaption>Kerbl 等，SIGGRAPH 2023 · <a href="https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/" target="_blank" rel="noreferrer">原论文场景视频</a>。点击播放，可拖动进度条或全屏观看；视频需联网加载。</figcaption>
    </figure><div class="scene-observe">
      <p><strong>新视角合成</strong>是指根据已有视角的图像，生成场景在新相机位置和朝向下的图像的过程。</p>
      <p>视频中的场景保持不变，移动的是观察它的相机。随着相机移动，近处物体与远处背景的相对位置发生变化，一些原本被挡住的部分也会显露出来。</p>
      <p>为了生成这些画面，3DGS 渲染器需要确定<strong>每个高斯投影到屏幕的什么位置</strong>，以及<strong>前后重叠的高斯如何共同决定像素颜色</strong>。接下来，我们沿着一帧图像解释这个过程，并说明 GPU 如何分工完成计算。</p>
    </div></div>''',
    '<div class="scene-print">'+fig('scene', '同一个场景，从已知相机视角到待生成的新视角；后续课程解释高斯的屏幕投影与像素颜色合成。此图为课程原创相机示意，并非视频截图。')+p('视频来源：<a href="https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/">Kerbl 等，3D Gaussian Splatting，SIGGRAPH 2023 项目页</a>。')+'</div>')
add('train-vs-render', 'task', '先分清两件事：学习场景与渲染场景',
    walkthrough())
add('route', 'task', '沿一帧图像，串起前面学过的并行思想',
    p('把图像划分成小块，每块称为一个 <strong>Tile</strong>。同一块里的像素共用一份可能影响它们的高斯列表，避免每个像素检查整个场景。'),
    fig('pipeline', '一帧的计算流程：先为每个高斯求屏幕信息，再为各个图像块组织候选列表，最后计算像素颜色。'),
    table(['已有知识','在本讲解决什么问题'], [
        ['第三讲：计数、前缀和、唯一地址','一个高斯对应多个 Tile，怎样并行写出可变数量的记录？'],
        ['第五讲：线程索引与输出所有权','由哪个线程写一个像素？'],
        ['第六讲：shared、同步与复用','相邻像素怎样共用一批高斯参数？']]),
    note('不同高斯的投影可以并行；同一像素的前后遮挡需要保持顺序。分组能减少无关检查，但也需要生成列表和排序。'))

add('point-to-splat', 'representation', '一个点的位置，还不足以覆盖一块表面',
    fig('point-splat', '左：只有中心的稀疏点；右：中心带有大小与方向，形成彼此重叠的柔和覆盖。'),
    p('一个点只告诉我们“在哪里”。为它增加空间尺度与方向，就能描述一个有范围的局部贡献：中心附近强，离中心越远越弱。'),
    p('把高斯权重相同的位置连起来，二维中得到<strong>等值线</strong>，三维中得到<strong>等值面</strong>。图中轮廓只是其中一条等值线，轮廓外仍有逐渐减弱的贡献。多个高斯重叠后，可以共同表示一片表面。'), refs=('paper',))
add('gaussian-falloff', 'representation', '从一维开始：距离怎样改变贡献？',
    p('x 表示一维位置，μ 表示中心；正数 σ 称为标准差，用来描述宽度。用 g(x) 表示该位置的相对权重，中心的权重取为 1：'),
    math_eq('''<mrow><mrow><mi>g</mi><mo>(</mo><mi>x</mi><mo>)</mo></mrow><mo>=</mo>
      <mi mathvariant="normal">exp</mi><mo>\u2061</mo><mrow><mo stretchy="true">[</mo>
      <mo>−</mo><mfrac><mn>1</mn><mn>2</mn></mfrac>
      <msup><mrow><mo stretchy="true">(</mo><mfrac><mrow><mi>x</mi><mo>−</mo><mi>μ</mi></mrow><mi>σ</mi></mfrac><mo stretchy="true">)</mo></mrow><mn>2</mn></msup>
      <mo stretchy="true">]</mo></mrow></mrow>''', 'g(x) 等于 exp，指数为负二分之一乘以 x 减 μ 除以 σ 的平方'),
    table(['离中心的距离','0','σ','2σ','3σ'], [['相对权重','1.000','0.607','0.135','0.011']]),
    p('exp 是指数函数。先把离中心的距离除以 σ，再计算权重：离中心一个标准差时约为 0.607，三个标准差时只剩约 0.011。σ 越大，同样的实际距离对应的权重就越大。'),
    note('数学上高斯没有有限边界；程序为了节省计算，需要选定有限的处理范围。'))
add('ellipse', 'representation', '二维高斯：拉长、旋转，改变覆盖形状',
    p('二维高斯有两个互相垂直的主轴，每个轴都有一个标准差。两个标准差相同，等值线是圆；不同则是椭圆。旋转改变两个轴的朝向。'),
    demo('ellipse', '两个尺度控制宽度，角度控制朝向，不透明度控制颜色贡献的强弱。虚线在两个主轴上分别经过离中心两倍标准差的位置。'),
    p('先把两个尺度调成相同的值，再只增大主轴尺度，最后转动椭圆。观察：离中心同样远的两个点，沿长轴方向的贡献可以更大。'),
    note('只调不透明度时，虚线轮廓不变，颜色深浅改变：贡献强弱与几何形状是不同的参数。'),
    '''<section class="gaussian-film" aria-labelledby="gaussian-film-title">
      <h3 id="gaussian-film-title">从一个高斯，到许多高斯组成的图像</h3>
      <div class="gaussian-film-player"><video controls playsinline preload="metadata" poster="../../materials/lectures/3dgs/media/gaussian-build-poster.jpg" src="../../materials/lectures/3dgs/media/gaussian-build.mp4" aria-label="44秒动画：依次改变一个高斯的主轴尺度、次轴尺度、旋转和不透明度，再逐步叠加高斯，拟合 Garden 照片"></video></div>
      <div class="gaussian-film-controls" role="group" aria-label="跳转到动画阶段">
        <button data-film-time="0">主轴尺度 · 0:00</button><button data-film-time="4">次轴尺度 · 0:04</button><button data-film-time="8">旋转 · 0:08</button><button data-film-time="12">不透明度 · 0:12</button><button data-film-time="18">叠加成图 · 0:18</button><button data-film-time="40">最终结果 · 0:40</button>
      </div>
      <p class="gaussian-film-error" role="status" hidden>动画未能加载，请刷新本地页面后重试。</p>
      <figure class="gaussian-film-print"><img src="../../materials/lectures/3dgs/media/gaussian-build-stages.jpg" alt="动画关键帧：一个高斯、128个高斯、3000个高斯、最终高斯合成图像" loading="lazy"><figcaption>从局部柔和覆盖，到许多高斯共同组成图像。</figcaption></figure>
      <p class="caption">前半段每次只改变一个属性；后半段持续加入带有不同位置、形状与颜色的高斯。左侧为实际合成结果，右侧为目标照片。这是二维图像拟合演示；三维高斯需要先投影到成像平面，再进行合成。</p>
    </section>''')
add('gaussian-record', 'representation', '一个三维高斯，需要保存哪些参数？',
    table(['参数','含义','影响图像的方式'], [
        ['中心 μ ∈ ℝ³','3 个分量，表示场景中的位置','投影位置与离相机的深度'],
        ['尺度 s ∈ ℝ³','3 个正数，表示三个主轴上的标准差','屏幕上覆盖形状的大小与长短比例'],
        ['旋转四元数 q ∈ ℝ⁴','4 个分量，用来表示三维朝向','屏幕上覆盖形状的方向'],
        ['不透明度 o ∈ ℝ（标量，1 个分量）','取值范围 [0,1]，控制贡献的强弱','有效不透明度 α 与遮挡'],
        ['球谐（SH）系数，3B 个分量','每个颜色通道 B 个系数，B 由选用的阶数决定','根据观察方向算出 RGB，共 3 个分量']]),
    p('旋转用四元数存储，共有 4 个分量；使用时归一化为单位四元数。归一化后的四元数满足单位长度约束，描述的三维旋转仍只有 3 个自由度。'),
    p('例如使用到三阶球谐函数时，每个颜色通道保存 16 个系数，RGB 共 48 个。渲染时读取这些参数；训练时根据照片调整它们。'),
    note('每个高斯都是一条参数记录。参数分量的数量决定存储量，以及 GPU 处理一个高斯时需要读取多少数据。'), refs=('paper','model'))
add('covariance', 'representation', '协方差：把三个方向的宽度和朝向记下来',
    p('协方差 '+math_inline(mi('Σ'))+' 是一个 3×3 矩阵，用来同时表示三维高斯的宽度和朝向。'),
    p('尺度决定高斯沿自身三个主轴的宽度。先把尺度平方放到对角线上，再用旋转矩阵 R 把这些主轴转到世界坐标系中的朝向。R 是 3×3 矩阵，由上一页的四元数 q 归一化后转换得到。'),
    math_eq('''<mrow><mi>Σ</mi><mo>=</mo><mi>R</mi><mi mathvariant="normal">diag</mi><mo>\u2061</mo>
      <mrow><mo>(</mo><msubsup><mi>s</mi><mi>x</mi><mn>2</mn></msubsup><mo>,</mo><msubsup><mi>s</mi><mi>y</mi><mn>2</mn></msubsup><mo>,</mo><msubsup><mi>s</mi><mi>z</mi><mn>2</mn></msubsup><mo>)</mo></mrow>
      <msup><mi>R</mi><mi mathvariant="normal">T</mi></msup><mo>=</mo><mi>R</mi><mi>S</mi><msup><mi>S</mi><mi mathvariant="normal">T</mi></msup><msup><mi>R</mi><mi mathvariant="normal">T</mi></msup></mrow>''', '协方差等于 R 乘主轴尺度平方的对角矩阵再乘 R 的转置，也等于 R S S转置 R转置'),
    p('S 是由三个尺度组成的对角矩阵。R 的三列给出旋转后的三个主轴方向；协方差需要<strong>左乘 R、右乘 R 的转置</strong>，将两个坐标分量的关系一起变换。'),
    fig('covariance-rotation', '固定尺度 (2,1,1)，绕 z 轴逆时针旋转 45°。图示为经过中心的 x–y 截面，z 方向不变；虚线为固定坐标轴，彩色实线为高斯主轴。'),
    math_eq('<mrow><msub><mi>Σ</mi><mn>0</mn></msub><mo>=</mo>'+math_matrix([[4,0,0],[0,1,0],[0,0,1]])+'<mspace width="1em"/><mo>→</mo><mspace width="1em"/><msub><mi>Σ</mi><mn>45°</mn></msub><mo>=</mo>'+math_matrix([[2.5,1.5,0],[1.5,2.5,0],[0,0,1]])+'</mrow>', '未旋转的协方差是对角矩阵4、1、1；绕z轴旋转45度后，对角项为2.5、2.5、1，xy与yx项均为1.5'),
    p('旋转后，主轴宽度仍为 (2,1,1)，但相对于固定 x、y 轴，协方差出现了非零的非对角项 1.5，记录了倾斜的朝向。此时不能再把对角项直接当作原来的主轴尺度平方。'),
    note('尺度决定沿主轴有多宽，旋转决定主轴朝哪里。三个尺度完全相同时，各方向一样宽，旋转不会改变协方差。'), refs=('paper','model'))
add('opacity', 'representation', '不透明度与高斯权重，是两个不同的量',
    p('用 i 编号一个高斯，用 p 表示图像中的一个像素位置。这个高斯对不同像素的遮挡强弱，由一个固定参数与一个随位置变化的权重共同决定：'),
    math_eq('<mrow><msub><mi>α</mi><mi>i</mi></msub><mo>(</mo><mi>p</mi><mo>)</mo><mo>=</mo><msub><mi>o</mi><mi>i</mi></msub><mo>·</mo><msub><mi>g</mi><mi>i</mi></msub><mo>(</mo><mi>p</mi><mo>)</mo></mrow>', '高斯 i 在像素 p 处的有效不透明度，等于其不透明度参数乘以该像素处的高斯权重'),
    p('oᵢ 是每个高斯保存的一个不透明度参数，取值在 [0,1] 内；gᵢ(p) 是投影后的高斯在像素 p 处的权重，中心为 1，远离中心逐渐减小。两者相乘得到 <strong>αᵢ(p)，即该高斯在像素 p 处的有效不透明度</strong>：它决定这个位置上，该高斯的颜色与后方颜色按什么比例混合。'),
    p('例如 αᵢ(p)=0.2 时，将这个高斯与它后方已经合成的颜色混合，结果是 <strong>20% 的该高斯颜色 + 80% 的后方颜色</strong>。α=0 表示完全透过后方颜色；α=1 表示完全挡住后方颜色。若前面还有其他高斯，它们还会进一步遮挡这里的颜色贡献。'),
    table(['假设 o = 0.8','中心 g=1','较远处 g=0.25'], [['有效不透明度 α','0.8','0.2'], ['后方颜色的透过比例 1−α','20%','80%']]),
    note('同一个高斯的 o 不随像素位置变化，但有效不透明度 α 会变化：中心遮挡强，边缘遮挡弱。不同高斯的 α 不需要加起来等于 1，因为它们描述的是各自的遮挡比例。'), refs=('paper','model'))
add('appearance', 'representation', '为什么颜色可以随观察方向变化？',
    p('同一位置从不同方向看，可能有不同亮度或高光。只保存固定 RGB 会限制这种外观的表达。原始 3DGS 用球谐函数（SH）的系数表达方向相关颜色。'),
    p('每个高斯保存一组 SH 系数，作为描述外观的参数。渲染时，将观察方向代入球谐函数，再用这组系数加权求和，得到该方向下的 RGB 颜色。相机位置改变后，同一组 SH 系数可以根据新的观察方向算出不同的颜色。'),
    note('对当前相机，每个高斯只求一次 RGB。它覆盖的各个像素共用这一颜色，但各像素处的有效不透明度不同，因此颜色贡献也不同。'), refs=('paper','forward'))

add('camera-coordinates', 'projection', '先把中心变换到相机坐标系',
    p('世界坐标系固定在场景中；相机坐标系以相机位置为原点，坐标轴随相机转动。本讲取相机前方为正 Z 方向，X、Y 分别表示横向和纵向位置，Z 表示深度。'),
    fig('camera', '图中的旋转和平移由目标相机的参数决定。'),
    p('μ（希腊字母 mu）表示高斯中心。下标 w 表示世界坐标系，c 表示相机坐标系。'+math_inline(sub(mi('μ'),'w'))+' 和 '+math_inline(mr(sub(mi('μ'),'c'),mo('='),tr(par(sub(mi('X'),'c')+mo(',')+sub(mi('Y'),'c')+mo(',')+sub(mi('Z'),'c')))))+' 都是三维列向量。'),
    math_eq(mr(sub(mi('μ'),'c'),mo('='),sub(mi('R'),'c'),sub(mi('μ'),'w'),mo('+'),sub(mi('t'),'c')), '相机坐标下的中心等于相机旋转乘世界坐标中心再加平移'),
    p(math_inline(sub(mi('R'),'c'))+' 是把世界坐标方向转换到相机坐标方向的 3×3 旋转矩阵；'+math_inline(sub(mi('t'),'c'))+' 是该坐标变换的三维平移向量。先旋转，再加上平移，就得到中心的相机坐标。'),
    p('例如，相机位于世界坐标 (1,0,0)，且两套坐标轴方向相同。高斯中心的世界坐标为 (3,1,4) 时，减去相机位置，得到相机坐标 (2,1,4)：中心在相机横向 2、纵向 1、前方 4 的位置。'),
    note('同一帧的所有高斯共用相同的相机变换，每个中心的计算互不依赖，可以按高斯并行。这里的 '+math_inline(sub(mi('R'),'c'))+' 用于变换坐标，与描述高斯自身朝向的旋转 R 不同。'))
add('perspective', 'projection', '透视投影：计算中心的像素位置',
    p('已知中心的相机坐标，现在求它在图像中的像素坐标 (u,v)：u 表示横向位置，v 表示纵向位置。'),
    p('从相机位置沿正前方延伸的轴线称为<strong>光轴</strong>；用来表示图像的二维平面称为<strong>成像平面</strong>，光轴与它的交点称为<strong>主点</strong>，其像素坐标是 (cₓ,cᵧ)。fₓ、fᵧ 是以像素为单位的焦距，分别把横向、纵向位置与深度的比值换算成离主点的像素距离。'),
    math_eq(mr(mi('u'),mo('='),frac(sub(mi('f'),'x')+sub(mi('X'),'c'),sub(mi('Z'),'c')),mo('+'),sub(mi('c'),'x'),GAP,mi('v'),mo('='),frac(sub(mi('f'),'y')+sub(mi('Y'),'c'),sub(mi('Z'),'c')),mo('+'),sub(mi('c'),'y')), 'u 等于 fx Xc 除以 Zc 加 cx；v 等于 fy Yc 除以 Zc 加 cy'),
    p('当高斯中心位于光轴上时，'+math_inline(mr(sub(mi('X'),'c'),mo('='),sub(mi('Y'),'c'),mo('='),mn(0)))+'，公式中的两个分式都为 0，因此它投影到 (cₓ,cᵧ)。下例取 fₓ=fᵧ=100，并将主点设为 (32,32)：'),
    table(['相机坐标 '+math_inline(par(sub(mi('X'),'c')+mo(',')+sub(mi('Y'),'c')+mo(',')+sub(mi('Z'),'c'))),'像素坐标 (u,v)','横向偏离主点 u−cₓ'], [['(0, 0, 2)','(32, 32)','0 像素'],['(0.2, 0, 2)','(42, 32)','10 像素'],['(0.2, 0, 4)','(37, 32)','5 像素']]),
    p('后两行的横向位置相同，深度从 2 增到 4，横向偏离主点的距离就从 10 像素减为 5 像素。焦距保持不变时，离相机越远，同样的横向距离在图像上占的像素越少。'),
    note('投影前需要判断中心是否在相机前方，并避开深度接近 0 的位置，否则除以深度会产生无效或过大的结果。'))
add('project-shape', 'projection', '投影一个高斯，不能只投影中心',
    p('投影中心只告诉我们高斯落在哪里，还不能确定它对周围各个像素的影响有多大。我们还需要这个高斯在屏幕上的二维形状；这里将它形成的覆盖形状称为<strong>屏幕足迹</strong>。'),
    fig('projection', '同一投影中心的二维算例。右图用深浅表示高斯权重，越深表示越大。虚线是相同权重的轮廓线，线外权重仍逐渐衰减，并不是硬边界。'),
    p('投影需要输出两份数据：二维中心 '+math_inline(sub(mi('μ'),'2D'))+'（2 个分量）确定位置；二维协方差 '+math_inline(sub(mi('Σ'),'2D'))+'（2×2 矩阵）确定沿各方向的宽度和朝向。有了两者，才能计算任意像素相对中心的高斯权重，再乘以不透明度参数得到该像素处的有效不透明度。'),
    p('二维形状由三维高斯的尺度、朝向和相机共同决定。例如，细长高斯的长轴朝向相机时，看起来更紧凑；长轴横在相机前方时，投影会更长。用固定大小的圆代替所有高斯，会丢掉这些差别。'),
    note('透视投影对不同深度的缩放不同。3DGS 在高斯中心附近估计“三维位置改变一点，像素位置会改变多少”，用这一局部关系把三维协方差转换成二维协方差。因此，屏幕上的二维高斯是局部近似。'), refs=('paper',))
add('project-covariance', 'projection', '同一个高斯，移远后屏幕足迹怎样缩小？',
    p('取一个各方向一样宽的三维高斯，中心位于相机光轴上。焦距 f=100 像素，三维标准差 σ=0.04；深度 Z 与 σ 使用相同长度单位。局部投影近似给出：'),
    math_eq(mr('<mtext>屏幕标准差</mtext>',mo('≈'),frac(mi('f')+mi('σ'),mi('Z'))), '屏幕标准差约等于焦距乘三维标准差除以深度'),
    table(['深度 Z','屏幕标准差','二维协方差的对角值'], [['2','2 像素','4 像素²'],['4','1 像素','1 像素²']]),
    p('移远一倍，屏幕宽度减半，方差变为四分之一。一般椭球还要考虑朝向，不能都套用这个圆形特例。'),
    note('程序还会计算二维协方差的逆矩阵 '+math_inline(mr(mi('Q'),mo('='),sup(sub(mi('Σ'),'2D'),'−1')))+'。Q 把像素到中心的位移换算成相对于高斯宽度的距离，供各像素求权重时重复使用。'), refs=('paper','forward'))
add('jacobian', 'projection', '深入：透视雅可比的每一项从哪里来？',
    math_eq(mr(mi('S'),mo('='),'<mi mathvariant="normal">diag</mi>',par(sub(mi('s'),'x')+mo(',')+sub(mi('s'),'y')+mo(',')+sub(mi('s'),'z')),GAP,mi('Σ'),mo('='),mi('R'),mi('S'),tr(mi('S')),tr(mi('R'))), 'S 是主轴尺度的对角矩阵，协方差为 R S S转置 R转置'),
    p('正尺度与有效旋转 R 给出正定协方差。R 可由归一化四元数得到。'),
    math_eq(mr(sub(mi('Σ'),'c'),mo('='),sub(mi('R'),'c'),mi('Σ'),tr(sub(mi('R'),'c')),GAP,sub(mi('Σ'),'2D'),mo('≈'),mi('J'),sub(mi('Σ'),'c'),tr(mi('J'))), '相机协方差为 Rc Σ Rc转置；屏幕协方差约为 J Σc J转置'),
    p('J 称为投影的雅可比矩阵：它把三维坐标的小变化映射成二维像素位置的小变化，因此有 2 行、3 列。先用相机旋转把协方差变到相机坐标系，再用 J 得到 2×2 的屏幕协方差。'),
    math_eq(mr(mi('J'),mo('='),matrix([[frac(sub(mi('f'),'x'),mi('Z')),mn(0),mo('−')+frac(sub(mi('f'),'x')+mi('X'),sup(mi('Z'),2))],[mn(0),frac(sub(mi('f'),'y'),mi('Z')),mo('−')+frac(sub(mi('f'),'y')+mi('Y'),sup(mi('Z'),2))]])), 'J 是两行三列矩阵，第一行为 fx/Z、0、负fxX/Z平方；第二行为0、fy/Z、负fyY/Z平方'),
    p('对透视投影公式中的 u 分别求 X、Y、Z 的偏导，得到第一行；v 的偏导给出第二行。这里 X、Y、Z 均为相机坐标。靠近主轴时 X、Y 较小，深度扰动对屏幕位置的横向影响较弱。'),
    p('例如 X=Y=0，fₓ=fᵧ=f，三维各向同性 '+math_inline(mr(mi('Σ'),mo('='),sup(mi('σ'),2),mi('I')))+'，则：'),
    math_eq(mr(sub(mi('Σ'),'2D'),mo('='),sup(par(frac(mi('f')+mi('σ'),mi('Z'))),2),mi('I')), '二维协方差等于焦距乘标准差除以深度的平方，再乘单位矩阵'),
    p('深度加倍，屏幕标准差减半，协方差对角元变为四分之一。'),
    math_eq(mr(mr(mi('g'),par(mi('p'))),mo('='),'<mi mathvariant="normal">exp</mi>',mr(mo('['),mo('−'),frac(mn(1),mn(2)),tr(mi('δ')),mi('Q'),mi('δ'),mo(']')),GAP,mi('δ'),mo('='),mi('p'),mo('−'),sub(mi('μ'),'2D'),GAP,mi('Q'),mo('='),sup(sub(mi('Σ'),'2D'),'−1')), '高斯权重为 exp 负二分之一 δ转置Qδ；δ为像素减屏幕中心，Q为屏幕协方差的逆矩阵'),
    p('二维对称 Q 只需保存 Qₓₓ、Qₓᵧ、Qᵧᵧ。展开二次型得到 '+math_inline(mr(sub(mi('Q'),'xx'),sup(sub(mi('δ'),'x'),2),mo('+'),mn(2),sub(mi('Q'),'xy'),sub(mi('δ'),'x'),sub(mi('δ'),'y'),mo('+'),sub(mi('Q'),'yy'),sup(sub(mi('δ'),'y'),2)))+'；交叉项不能漏掉系数 2。'),
    note('Q 是对称矩阵，两个非对角元素相同。因此每个高斯只需保存 3 个数来描述 Q，各像素可以直接用它们求二次型。'), deep=True, refs=('paper',))
add('finite-footprint', 'projection', '无限的高斯，有限的候选区域',
    p('高斯的权重没有硬边界，但离中心足够远时很小。为减少检查，取屏幕椭圆最宽方向约 3 倍标准差作为候选半径，再用一个与屏幕坐标轴对齐的方框围住这个范围，这个方框称为<strong>包围框</strong>。'),
    p('与包围框相交的图像块称为这个高斯的<strong>候选 Tile</strong>。先检查矩形是否相交，可以快速排除远处的图像块；真正计算像素颜色时，仍按高斯公式求该像素处的有效不透明度。'),
    table(['屏幕标准差（圆形例子）','3 倍标准差的半径','包围框边长'], [['2 像素','6 像素','12 像素'],['1 像素','3 像素','6 像素']]),
    note('包围框内的像素只是候选，权重可能很小；框外权重也不是严格为零。截取有限范围用少量精度换取更少的计算。表中未计滤波与取整，实际程序还要处理屏幕边界。'), refs=('forward',))
add('preprocess', 'projection', '每高斯预处理：先做一次，供后面反复使用',
    table(['输入 / 步骤','输出'], [['中心与当前相机','可见性判断、屏幕中心、深度'],['尺度、旋转、相机','二维协方差与逆矩阵'],['方向与 SH 系数','当前视角颜色'],['屏幕足迹','包围框、候选 Tile 数']]),
    p('不同高斯的这些计算大体独立，可以按高斯并行。后续每个像素无需重新计算这个高斯的三维投影。不可见或没有候选 Tile 的高斯产生零条配对记录。'),
    note('例如，一个高斯覆盖 100 个像素，三维投影和颜色只需为该相机算一次；100 个像素分别读取结果，计算各自的权重。'), refs=('forward','pipeline'))

add('evaluate-alpha', 'compositing', '算一次有效不透明度 α：同样离中心 2 像素，为何不同？',
    p('取一个未旋转的二维高斯，横向标准差为 2 像素，纵向为 1 像素，不透明度 o=0.8。δₓ、δᵧ 是像素相对中心的横向、纵向位移；d² 是分别按两个标准差缩放后，再平方相加得到的距离量。'),
    math_eq(mr(sup(mi('d'),2),mo('='),sup(par(frac(sub(mi('δ'),'x'),mn(2))),2),mo('+'),sup(sub(mi('δ'),'y'),2),GAP,mi('g'),mo('='),'<mi mathvariant="normal">exp</mi>',par(mo('−')+frac(sup(mi('d'),2),mn(2))),GAP,mi('α'),mo('='),mn('0.8'),mi('g')), 'd平方等于δx除以2的平方加δy平方；g为exp负d平方除以2；有效不透明度为0.8g'),
    table(['相对位置 δ','按宽度缩放后的 d²','高斯权重 g','有效不透明度 α'], [['(0,0)','0','1','0.8'],['(2,0)','1','≈0.6065','≈0.4852'],['(0,2)','4','≈0.1353','≈0.1083']]),
    p('沿横轴走 2 像素只走了一个标准差，沿纵轴却走了两个。'+math_inline(mr(mi('Q'),mo('='),'<mi mathvariant="normal">diag</mi>',par(frac(mn(1),mn(4))+mo(',')+mn(1))))+' 正是在记录这两个方向的缩放；旋转椭圆需要再计入方向关系。'),
    note('即使与中心的像素距离相同，沿不同主轴方向算出的有效不透明度 α 也可能不同。它由不透明度参数和该像素处的高斯权重共同决定。'), refs=('forward',))
add('transmittance', 'compositing', '前面的覆盖，决定后面还能贡献多少',
    p('固定一个像素，从离相机近的高斯开始合成。C 是已经累计的 RGB 颜色；<strong>剩余透射率 T</strong> 是经过前面所有高斯后，还允许后方颜色透过的比例。例如 T=0.2，后方颜色的贡献最多只剩原来的 20%。'),
    p('开始时 C=(0,0,0)、T=1。当前高斯的 RGB 颜色为 cᵢ，在该像素处的有效不透明度为 αᵢ。先累加颜色，再更新 T：'),
    math_eq(mr(mi('C'),mo('←'),mi('C'),mo('+'),mi('T'),sub(mi('α'),'i'),sub(mi('c'),'i'),GAP,mi('T'),mo('←'),mi('T'),par(mn(1)+mo('−')+sub(mi('α'),'i'))), '先累计 T乘alpha乘颜色，再将T乘以一减alpha'),
    p('遍历结束后，若还有剩余透射率，就用背景颜色 '+math_inline(sub(mi('c'),'bg'))+' 补上：'),
    math_eq(mr(sub(mi('C'),'final'),mo('='),mi('C'),mo('+'),mi('T'),sub(mi('c'),'bg')), '最终颜色等于累计颜色加剩余透射率乘背景颜色'),
    note('T 必须先用于本次颜色贡献，再更新给下一个高斯。颜色为 RGB 向量，T 与 α 是标量。'), refs=('paper',))
add('blend-demo', 'compositing', '追踪一个像素：红、绿、蓝怎样叠加？',
    p('给定一个像素，前后顺序为 G₀（红）→ G₂（绿）→ G₁（蓝）。RGB 分别为 (1,0,0)、(0,1,0)、(0,0,1)，有效不透明度分别为 0.5、0.25、0.5，背景为黑色。G 的下标是编号，不是深度顺序。'),
    demo('blend', '点击“下一步”，对照本次权重 Tα、累计颜色 C 与剩余透射率 T；再反转顺序，比较最终颜色。'),
    note('红色先占 0.5；绿色的权重是 0.5×0.25=0.125；蓝色的权重是 0.375×0.5=0.1875。最终 RGB=(0.5,0.125,0.1875)，剩余 0.1875 分给黑色背景。'))
add('order-matters', 'compositing', '交换深度顺序，为什么颜色变了？',
    p('只比较红、蓝两个高斯，有效不透明度都为 0.5，背景为黑色。排在前面的颜色先贡献 0.5，排在后面的颜色再乘上剩余透射率 0.5，只贡献 0.25。'),
    table(['前后顺序','红色分量','蓝色分量','剩余 T'], [
        ['红在前、蓝在后','0.5','0.25','0.25'],['蓝在前、红在后','0.25','0.5','0.25']]),
    p('剩余透射率相同，但颜色不同。普通颜色相加可以交换次序；有遮挡的 alpha 合成不能随意交换前后次序。'),
    note('atomicAdd 可以避免并发加法丢失更新，却不能保证前面的高斯先合成。若每个高斯同时向同一像素累加颜色，仍需解决前后遮挡的顺序。'))
add('blend-code', 'compositing', '把像素合成写成一段短循环',
    code('''// 教学伪代码：list 已按前到后排序；无阈值近似
Color C = {0, 0, 0};
float T = 1;
for (int id : list) {
    float alpha = opacity[id] * gaussian_weight(id, pixel);
    C += T * alpha * color[id];
    T *= 1 - alpha;
}
image[pixel] = C + T * background;'''),
    p('不同像素可以同时执行自己的循环；同一像素在这个实现中沿排序列表依次更新 C 与 T。输入已经排序是这段代码的前提。'))
add('exercise-blend', 'compositing', '随堂填空 ①：只补两行，保持前后关系',
    p('约 2 分钟。初始 C=(0,0,0)、T=1；红色 (1,0,0) 在前，蓝色 (0,0,1) 在后，两者 α 都为 0.5，背景为黑色。g.color 是当前高斯的 RGB，alpha_at 返回它在 pixel 处的有效不透明度。'),
    code('''for (Gaussian g : front_to_back) {
    float a = alpha_at(g, pixel);
    C += __________;
    T  = __________;
}'''),
    p('补全表达式，并给出最终 RGB 与 T。若先更新 T 再计算 C，会发生什么？'),
    answer(p('<code>C += T * a * g.color;</code>，<code>T = T * (1-a);</code>。结果 RGB=(0.5,0,0.25)，T=0.25。先更新 T 会把当前高斯也当成其自身前方的遮挡，低估本次贡献。')))
add('composite-scan', 'compositing', '深入：像素内的合成能否使用 Scan？',
    p('把有序高斯列表分成前后相邻的两段 A、B。每段从 C=0、T=1 开始，独立求出颜色与透射率，再把 A 放在 B 前面组合：'),
    math_eq(mr(par(sub(mi('C'),'A')+mo(',')+sub(mi('T'),'A')),mo('⊗'),par(sub(mi('C'),'B')+mo(',')+sub(mi('T'),'B')),mo('='),par(sub(mi('C'),'A')+mo('+')+sub(mi('T'),'A')+sub(mi('C'),'B')+mo(',')+sub(mi('T'),'A')+sub(mi('T'),'B'))), '两段组合的颜色为 CA加TA乘CB，透射率为TA乘TB'),
    p('⊗ 表示上述组合操作。它在精确算术下满足结合律：可以改变括号位置，用树形归约或前缀扫描（Scan）计算；但不能交换 A、B 的前后位置。'),
    p('原始 3DGS 的 Tile 渲染器选择每像素顺序遍历：像素间已有大量并行，还能自然利用提前结束。额外的像素内并行会带来中间状态、通信和调度成本。浮点运算重新分组也可能改变舍入。'),
    note('像素内并行增加了需要保存和传递的中间结果；是否值得，取决于列表长度、可用像素并行度和提前结束的收益。'), deep=True)

add('naive-cost', 'tiles', '最直接的方法，为什么会做太多无用工作？',
    code('''parallel_for pixel in image:
    for gaussian in all_gaussians_in_depth_order:
        evaluate_and_blend(pixel, gaussian)'''),
    p('设有 P 个像素、N 个高斯，最直接的候选检查量为 P×N。1920×1080 像素与 100 万个高斯，对应约 2.07×10¹² 对组合；其中很多在屏幕上相距很远。'),
    note('如果先排除屏幕上相距很远的像素–高斯组合，就能减少每个线程的循环次数。建立候选列表的目的就是省掉这些检查。'))
add('pixel-ownership', 'tiles', '选择输出所有者：每个像素交给一个线程',
    table(['方案','方便之处','还需要解决'], [
        ['按高斯散射到像素','直接遍历自己的覆盖范围','多个高斯写同一像素，还要满足深度顺序'],
        ['按像素聚集高斯','一个线程持有 C、T，唯一写出像素','怎样快速得到这个像素的候选列表？']]),
    p('原始 3DGS 实现选择后者。若为每个像素建立独立列表，管理与存储可能很贵。相邻像素的候选通常相似，于是让一小块屏幕共用一个列表。'),
    note('每个像素只由一个线程写出最终颜色，就不需要多个线程争用这个输出位置。高斯参数仍可被许多像素线程共同读取。'), refs=('paper',))
add('tile-demo', 'tiles', '把屏幕分成 Tile，共用一份候选列表',
    p('将 64×64 像素的图像划成 16×16 像素的小块，得到 4×4 个 Tile。编号按从左到右、从上到下排列。一个高斯的包围框与某块相交，就加入该块的候选列表。'),
    demo('tiles', '64×64 教学屏幕，16×16 像素一个 Tile，共 4×4 个 Tile。点击或用键盘选择 Tile，查看候选及深度顺序。虚线框是候选包围框。'),
    p('同一 Tile 的像素遍历同一份高斯编号（ID）列表。高斯的颜色已经求好，各像素分别计算自己的有效不透明度和颜色累加结果。'),
    note('点击 Tile 5 可以看到 G₀、G₂、G₁ 三个候选；点击 Tile 2 则为空列表，只需要输出背景。'), refs=('paper','forward'))
add('toy-records', 'tiles', '贯穿算例：四个高斯产生多少条配对记录？',
    table(['高斯 / 颜色','中心 (u,v)','候选半径 r','深度 z','覆盖的 Tile ID'], [
        ['G₀ / 红','(20,20)',8,2,'0, 1, 4, 5'],
        ['G₁ / 蓝','(26,12)',6,4,'1, 5'],
        ['G₂ / 绿','(30,26)',10,3,'5, 6, 9, 10'],
        ['G₃ / 黄','(54,54)',4,5,'15']]),
    p('tile_x 是块的列号，tile_y 是行号，都从 0 开始。编号为 <code>tile_id = tile_y * 4 + tile_x</code>。本例中心、半径与深度直接给定，包围框采用左闭右开的区间 [u−r,u+r)×[v−r,v+r)，即包含左、上边界，不包含右、下边界。'),
    p('例如 G₀ 的包围框是 [12,28)×[12,28)，跨过横向和纵向的第 16 像素分界，因而与 Tile 0、1、4、5 相交。'),
    p('一个高斯的候选包围框与一个 Tile 相交，就生成一条高斯–Tile 配对记录。本例共 4+2+4+1=11 条；同一个高斯 ID 可以出现在多个 Tile 的列表中。'),
    note('一条记录保存 Tile 编号、深度和高斯 ID。多个记录可以指向同一份高斯参数，无需把整个参数结构复制多份。'))
add('scan-offsets', 'tiles', '数量不一样，先用前缀和分配写出位置',
    p('count[g] 是高斯 g 要写出的记录数，offset[g] 是它在输出数组中的起点。起点等于它之前所有高斯的记录数之和，这种不包含自身的前缀求和称为<strong>独占前缀和</strong>。'),
    code('count  = [4, 2, 4, 1]\noffset = [0, 4, 6, 10]\ntotal  = 11'),
    table(['高斯','写出区间（左闭右开）'], [['G₀','[0,4)'],['G₁','[4,6)'],['G₂','[6,10)'],['G₃','[10,11)']]),
    p('offset 是独占前缀和，每个高斯提前知道自己专属的输出区域。即使 G₂ 最早执行，也只写 [6,10)，不会抢占 G₀ 的位置。'),
    note('计数和写出可以分别按高斯并行；前缀和把每个高斯的数量变成互不重叠的地址区间，避免写出时再争抢空间。'), refs=('pipeline',))
add('exercise-offset', 'tiles', '随堂填空 ②：给每个高斯一段独占空间',
    p('约 2 分钟。换一组覆盖数量 <code>count=[2,0,3,1]</code>，依次对应 G₀…G₃。its_tiles[g] 是高斯 g 的候选 Tile 列表，pair(g,tile) 生成一条配对记录。数量为 0 的高斯不写记录。'),
    code('''offset = [0, __, __, __]
total  = __
parallel_for g in gaussians:
    for j in range(count[g]):
        output[__________] = pair(g, its_tiles[g][j])'''),
    p('哪两个高斯可以具有相同的 offset？为什么不会产生写冲突？'),
    answer(p('offset=[0,2,2,5]，total=6，写入地址为 <code>offset[g]+j</code>。G₁ 和 G₂ 起点同为 2，但 G₁ 的数量为零，不执行写入；G₂ 写 [2,5)。')))
add('emit-pairs', 'tiles', '并行写出：从每高斯列表变成一串记录',
    table(['输出位置','高斯','(Tile, depth)'], [
        ['0–3','G₀','(0,2), (1,2), (4,2), (5,2)'],
        ['4–5','G₁','(1,4), (5,4)'],
        ['6–9','G₂','(5,3), (6,3), (9,3), (10,3)'],
        ['10','G₃','(15,5)']]),
    p('现在记录按“从哪个高斯写出”放在一起。渲染时需要的却是“同一个 Tile 有哪些高斯，而且前后顺序是什么”。接下来必须重新组织顺序。'),
    note('写出时，每个高斯读取自己的 Tile 列表；渲染时，每个 Tile 要读取自己的高斯列表。排序将记录按读取者重新分组。'), refs=('pipeline',))
add('sort-pairs', 'tiles', '一次排序，先按 Tile，再按深度',
    table(['Tile','排序后高斯 ID','对应深度'], [
        [0,'G₀',2],[1,'G₀, G₁','2,4'],[4,'G₀',2],[5,'G₀, G₂, G₁','2,3,4'],[6,'G₂',3],[9,'G₂',3],[10,'G₂',3],[15,'G₃',5]]),
    p('先比较 Tile ID，ID 小的在前；ID 相同时再比较高斯中心的相机深度，深度小的在前。这样同一 Tile 的记录连续存放，组内又保持从近到远的顺序。'),
    p('Tile 5 最能说明问题：写出时 G₁ 在 G₂ 前，排序后 G₂ 必须移到 G₁ 前。'),
    note('同一 Tile 的所有像素共用按高斯中心深度确定的顺序。较大的高斯可能在不同像素处交错重叠，这个共享顺序是一种近似。'), refs=('paper','pipeline'))
add('tile-ranges', 'tiles', '找到每个 Tile 的起止位置，交给渲染器',
    p('排序后的记录放在一个连续数组中。对每个 Tile 保存起点 begin 和终点 end，就能直接读取它的列表；end 对应的位置不包含在列表内。'),
    table(['记录下标','0','1','2','3','4','5','6','7','8','9','10'], [['Tile ID',0,1,1,4,5,5,5,6,9,10,15],['高斯 ID','G₀','G₀','G₁','G₀','G₀','G₂','G₁','G₂','G₂','G₂','G₃']]),
    table(['Tile','范围 [begin,end)','列表长度'], [[0,'[0,1)',1],[1,'[1,3)',2],[4,'[3,4)',1],[5,'[4,7)',3],[6,'[7,8)',1],[9,'[8,9)',1],[10,'[9,10)',1],[15,'[10,11)',1]]),
    p('比较相邻排序记录的 Tile ID，边界处写出范围。没有记录的 Tile 保持空范围，渲染时输出背景。'),
    p('例如，下标 4 的 Tile ID 与前一项不同，是 Tile 5 的起点；下标 7 已属于 Tile 6，所以 Tile 5 的范围为 [4,7)。比较不同相邻位置的工作可以并行完成。'),
    note('阶段之间存在数据依赖。同一 CUDA stream 中按顺序提交这些操作即可建立执行顺序；无需在每一阶段都让 CPU 等待。'), refs=('pipeline',))
add('sort-key', 'tiles', '深入：64 位排序 Key 包含什么？',
    p('排序键（key）是供排序算法比较的数。用高 32 位保存 Tile ID、低 32 位保存深度编码，就能通过一次整数比较实现“先 Tile、后深度”的规则：'),
    code('uint64 key = (uint64(tile_id) << 32) | depth_bits;'),
    p('Tile ID 占高位，深度编码占低位。原始实现把通过可见性检查的正有限浮点深度按位解释为无符号整数；在这个范围内，位模式顺序与数值顺序一致。'),
    p('不能直接把相同做法用于任意带负号浮点数、NaN 或不一致的深度约定。位打包不是把深度数值强制转换成整数。'),
    note('记录的值是高斯 ID，排序时随 key 一起移动。一个 key 占 8 字节，一个 32 位 ID 占 4 字节；配对记录越多，排序搬运的数据也越多。'), deep=True, refs=('pipeline',))

add('block-mapping', 'execution', '一个 Tile 一个 Block，一个像素一个线程',
    fig('ownership', '64×64 屏幕对应 4×4 个 Block；每个 Block 的 16×16 个线程负责一个 Tile 的 256 个像素。'),
    code('''// 本讲采用 x 对应列、y 对应行，Block=(16,16)
int t = threadIdx.y * 16 + threadIdx.x; // 块内编号 0..255
int tile_id = blockIdx.y * gridDim.x + blockIdx.x;
int x = blockIdx.x * 16 + threadIdx.x;
int y = blockIdx.y * 16 + threadIdx.y;
bool inside = x < width && y < height;'''),
    p('接着追 Tile 5：grid=(4,4)，所以它对应 blockIdx=(1,1)。threadIdx=(1,2) 的块内编号 t=33，负责像素 (x=17,y=18)，行主序地址为 18×64+17=1169。'),
    note('每个线程保存自己的累计颜色 C 和透射率 T，并写出自己的像素。inside 表示这个像素是否在图像内；边缘 Block 中可能存在没有有效像素的线程。'), refs=('forward',))

add('shared-load', 'execution', '追踪 Tile 5：谁把 G₀、G₂、G₁ 装入 Shared？',
    p('Shared 是同一线程块内共享的存储空间。Tile 5 的范围为 [4,7)，记录下标 4、5、6 对应 G₀、G₂、G₁。用 base 表示本批起点，valid 表示本批有效记录数：这里 base=4、valid=3，缓冲区最多装 256 条。'),
    columns(code('''// t 是块内编号 0..255
int valid = min(256, end - base);
if (t < valid) {
    int id = sorted_ids[base + t];
    shared[t] = projected[id];
}
__syncthreads(); // 全部 256 线程参加'''),
    table(['加载者','记录下标 → 高斯','写入槽'], [['t=0','4 → G₀','shared[0]'],['t=1','5 → G₂','shared[1]'],['t=2','6 → G₁','shared[2]'],['t=3…255','不加载','仍参加同步']])),
    '<p class="caption">projected[id] 保存预处理后的屏幕中心、Q、不透明度与 RGB；这里搬运参数，不重复投影。</p>',
    note('t=33 本批不用加载，却要依次读取三个槽，为像素 (17,18) 计算有效不透明度并更新 C、T。加载由线程分担，合成由每个像素线程各自完成。'), refs=('forward',))

add('batch-lifetime', 'execution', '换成 258 条候选：最后两条由谁加载？',
    fig('barriers', '批次循环：所有参与者完成装入 → 同步 → 读取并合成 → 同步 → 下一批覆盖相同 shared 缓冲区。'),
    p('Tile 5 只有三条候选，一批就够。另设一个边界测试 Tile，范围为 [4,262)，共 258 条候选；假设第一批后仍有像素需要继续。'),
    table(['批次','base / valid','负责加载的线程','消费者读取哪些槽'], [['第一批','4 / 256','t=0…255，读记录下标 4…259','j=0…255'],['第二批','260 / 2','t=0、1，读记录下标 260、261','只读 j=0、1']]),
    p('<strong>装入后同步</strong>避免读到尚未写好的新数据；<strong>覆盖前同步</strong>避免快线程用第二批覆盖慢线程仍在读取的第一批。第二批的 shared[2…255] 无须清零，因为 valid=2 保证不再读取旧槽。'),
    note('C、T 跨批次保留，base 只是推进有序候选的位置。批次边界不重新开始颜色合成，也不改变候选的深度顺序。'))

add('render-pseudocode', 'execution', '把加载、顺序合成与两次交接接起来',
    p('当剩余透射率 T 小到阈值 epsilon 以下时，这个像素可以停止合成，把剩余部分当作背景。done 记录该像素是否已经结束；但线程仍需协助其他像素加载数据。'),
    p('Block=(16,16)，pixel=(x,y)，[begin,end) 是本块的候选范围。shared 有 256 个参数槽；alpha_at 根据屏幕中心、Q 和不透明度参数求有效不透明度 α，结果在 [0,1] 内。'),
    code('''// 教学伪代码：保留 CUDA 的索引与块内同步，省略类型声明
bool done = !inside;
C = 0; T = 1;
for (int base = begin; base < end; base += 256) {
    if (__syncthreads_count(done) == 256) break;
    int valid = min(256, end - base);
    if (t < valid)
        shared[t] = projected[sorted_ids[base + t]];
    __syncthreads();
    if (!done) {
        for (int j = 0; j < valid; ++j) {
            g = shared[j];
            a = alpha_at(g, pixel);
            C += T * a * g.color;
            T *= (1 - a);
            if (T < epsilon) { done = true; break; }
        }
    }
    __syncthreads(); // 所有线程读完后，下一批才可覆盖
}
if (inside) image[pixel] = C + T * background;'''),
    p('__syncthreads_count(done) 是全块同步并统计 done 的人数，所有线程得到同一个计数。只有 256 人都结束才统一退出；空范围直接跳过循环，输出背景。'),
    note('这个简化循环先加入当前高斯，再判断是否结束。提前结束减少了候选检查，也忽略了一部分后方颜色，因此阈值会影响图像精度。'), refs=('forward',))

add('pixel-done', 'execution', '线程 1 的像素结束了，为什么还得加载第二批？',
    p('继续 [4,262) 的边界测试。第一批后，t=1 的像素已达到终止阈值，但 t=33 的像素还没结束。全块 done 数小于 256，必须进入第二批。'),
    table(['线程','第二批的加载职责','第二批的像素职责'], [['t=0','按记录下标 260 取参 → shared[0]','未 done 才继续合成'],['t=1，已 done','仍按记录下标 261 取参 → shared[1]','不再更新自己的 C、T'],['t=33，未 done','不加载；参加同步','依次消费 shared[0]、shared[1]']]),
    p('若 t=1 自行 return，shared[1] 就没有第二批的新数据，t=33 会读到上一批留下的值。done 只控制自己的颜色合成，不能取消共享加载任务或绕开这段算法的统一同步流程。'),
    note('边缘 Tile 同理：以 18×18 图像为例，右下 Tile 只有 4 个有效像素，却仍有 256 个协作线程。inside 控制像素读写，t&lt;valid 控制候选加载，二者不能互相替代。'), refs=('forward',))

add('exercise-sync', 'execution', '随堂填空 ③：把同步放在所有参与者都会经过的位置',
    p('约 3 分钟。所有线程执行同一组批次，shared 会被反复覆盖。blend_pixel 更新当前线程的 C、T，并在达到阈值时设置 done。补出两处操作；再用“t=1 已 done、t=33 未 done”的第二批说明为什么不能自行 return。'),
    code('''for (int base = begin; base < end; base += 256) {
    int valid = min(256, end - base);
    if (t < valid)
        shared[t] = projected[sorted_ids[base + t]];
    __________;              // 开始读之前
    if (!done) blend_pixel(shared, valid); // 只消费有效槽
    __________;              // 下一轮覆盖之前
}'''),
    answer(p('两处都填 <code>__syncthreads()</code>，并放在 <code>if (!done)</code> 外。第一处交接新数据，第二处保护旧数据的读取。t=1 仍需按记录下标 261 加载参数，供 t=33 等未完成像素读取；done 只结束自己的合成，不能取消加载职责。全块统一提前退出需要前页的集体投票。')))

add('uneven-work', 'execution', '相同的线程数，不代表相同的工作量',
    fig('imbalance', '不同 Tile 的候选数与各像素结束位置不同；少量繁忙 Tile 可能成为整帧尾部。'),
    p('空背景 Tile 很快结束，复杂边缘可能覆盖很多高斯。即使同一 Tile 内，一些像素早已不透明，另一些仍在处理后方内容。'),
    p('同一 Warp（32 个线程组成的执行组）内，部分线程停止合成后，其他线程仍可能继续循环；停止合成的线程还可能需要加载和同步。线程块只有在所有像素都结束，或候选读完后，才能结束。'),
    note('如果大部分 Tile 已完成，少数 Tile 还在处理很长的列表，整帧就要等待它们。应同时观察平均工作量和最繁忙的 Tile。'))
add('implementation-map', 'execution', 'Tile 5 的复用账：768 次参数读取怎样变成 3 次？',
    p('回到只有三条候选的 Tile 5。假设 256 个像素都检查全部三条候选，没有提前结束。只数一个字段：每个候选的屏幕中心 x，一个 FP32。'),
    table(['方案','global 字段读取次数','新增的 shared 字段访问'], [['每像素独立取参数','256×3=768','无'],['合作装入，再按像素读取','3','写 3 次；读 256×3=768 次']]),
    math_eq(mr(mn(768),mo('×'),mn(4),mo('='),mn(3072),'<mtext> 字节</mtext>',mo('→'),mn(3),mo('×'),mn(4),mo('='),mn(12),'<mtext> 字节</mtext>'), '全局字段读取请求对应字节由3072减少到12'),
    p('像素仍需各自计算三次局部贡献；我们减少的是重复的 global 取参请求。代价是 shared 访问、容量和同步。对 256 槽、每槽 9 个 FP32 的教学记录（中心2、Q3、不透明度1、RGB3），shared 容量为 256×9×4=9216 字节，即 9 KiB。这里按分字段数组存储，不计额外缓冲区。'),
    note('768÷3=256 表示源码层面的读取次数比。多个读取可能已经被缓存合并，因此显存实际传输量与运行时间不会自动减少 256 倍。Shared 容量和同步也会带来成本。'))

add('termination-error', 'execution', '深入：提前结束，牺牲了多少颜色贡献？',
    p('如果颜色与背景的每个通道都位于 [0,1]，当前剩余透射率为 T，那么后方所有内容对最终颜色的总权重不超过 T。用背景替代后方内容时，每通道误差上界可由 T 控制。'),
    math_eq(mr(mi('T'),mo('<'),mi('ε'),mo('⇒'),'<mtext>每通道误差</mtext>',mo('≤'),mi('ε')), '颜色和背景通道都在零到一时，T小于epsilon则每通道误差不超过epsilon'),
    p('例如 T=0.01，即使后方真实颜色是纯白、用于替代的背景是纯黑，每个通道最多也只相差 0.01。'),
    p('这个推理只解释截断当前像素的尾部；它不包含排序近似、滤波、低 alpha 跳过或训练变化。HDR 或未裁剪颜色也需要不同的颜色上界。'),
    note('阈值是质量与工作量之间的选择，不能只比较 FPS 而忽略误差。'), deep=True)
add('threshold-order', 'execution', '深入：教学循环与官方阈值次序有什么差别？',
    p('官方实现先计算 <code>test_T = T * (1 - alpha)</code>，表示若加入当前高斯，预计还剩多少透射率。若它低于终止阈值，会标记 done，而不把当前高斯加入 C，也不把 test_T 写回 T。'),
    p('主线的伪代码选择“先合成，再检查 T”方便解释。二者共享线程协作结构，但阈值附近的数值行为不同。若做结果校验，应明确选择哪个规范，不能要求简化版本逐位等同官方实现。'),
    note('官方实现还会跳过极小 α，并限制 α 的最大值。重现数值结果时应保持这些规则一致；只对照线程分工时，则应比较加载、同步和像素计算的结构。'), deep=True, refs=('forward',))

add('training-loop', 'learning', '怎样用渲染结果调整场景参数？',
    fig('training', '选训练视角 → 渲染图像 → 与参考照片比较 → 反向传播 → 更新高斯参数，再次迭代。'),
    p('选一个训练相机，用当前高斯参数渲染图像，再与该相机的照片比较。把图像差异汇总得到的数称为<strong>损失</strong>；损失越小，表示按这个比较规则计算的差异越小。'),
    p('反向传播计算损失对参数的<strong>梯度</strong>，即每个参数稍微增加时，损失会增大还是减小、变化有多快。优化器依据这些梯度调整参数，再次渲染。'),
    p('例如投影位置偏了，中心参数可能收到调整信号；颜色偏暗，颜色参数可能收到调整信号。把全部贡献合起来，再由优化器更新参数，重复下一次渲染。'),
    note('一次训练迭代包含渲染、反向计算和参数更新；查看已训练场景的一帧图像，只需要渲染。两者的工作量不同。'), refs=('paper','training'))
add('gradient-path', 'learning', '像素误差，沿哪些计算路径回到高斯参数？',
    p('一个像素的颜色同时依赖多个高斯。反向计算先求出损失对各个颜色贡献的影响，再沿对应的计算步骤传回参数；它有多条分支：'),
    table(['经过的中间量','传回哪些参数'], [['当前视角的 RGB','SH 颜色系数，以及决定观察方向的中心'],['像素处的有效不透明度 α','不透明度参数、二维中心与二维形状'],['二维中心与二维形状','三维中心、尺度和旋转']]),
    p('同一个参数可能通过多条路径影响损失，这些梯度贡献需要相加。例如中心既影响屏幕位置，也影响观察方向。'),
    note('反向遍历复用前向生成的有序候选列表。本次计算按已有列表求梯度，不为“某个高斯改排到第几位”这样的离散变化直接求导。'), refs=('paper','backward'))
add('backward-scatter', 'learning', '前向一个像素一个所有者，反向却会汇到同一高斯',
    fig('gradients', '前向：一个高斯影响多个像素；反向：多个像素的梯度贡献汇聚到同一高斯参数。'),
    p('一个高斯覆盖多个像素甚至多个 Tile。每个像素算出的梯度都是总梯度的一部分，需要相加，汇总到同一个高斯参数。这个多项合成一个结果的过程称为归约。'),
    p('原始实现的反向 kernel 使用原子加来汇集一些参数梯度。这里的相加具有归约意义，与前向不允许乱序的透明颜色合成是不同问题。浮点归约次序仍可能影响末位舍入。'),
    note('前向中，多个像素共同读取一个高斯；反向中，多个像素可能同时更新这个高斯的梯度，因此需要原子加或其他归约安排。'), refs=('backward',))
add('density-control', 'learning', '场景细节不足时，怎样改变高斯的数量？',
    fig('density', '克隆增加局部表示能力；拆分把大覆盖分成较小基元；剪枝移除贡献低或不合适的基元。'),
    p('只调整已有高斯，有时难以表示新的细节。<strong>克隆</strong>增加一个可继续调整的高斯；<strong>拆分</strong>用多个较小高斯替代一个较大的高斯；<strong>剪枝</strong>删除贡献很小或不合适的高斯。训练会周期性地执行这些操作。'),
    note('高斯数组变长后，需要存储和预处理的参数更多；若屏幕覆盖也增加，配对记录和像素检查量还会继续增加。训练不仅改变参数值，也改变后续渲染的工作量。'), refs=('paper','model'))
add('learned-scene', 'learning', '训练完成，查看一帧时哪些东西还在变化？',
    table(['数据','固定场景、移动相机时'], [
        ['三维中心、尺度、旋转、不透明度、SH 系数','保持不变，继续读取同一组场景参数'],
        ['相机坐标、二维中心与形状、当前视角 RGB','根据新相机重新计算'],
        ['候选 Tile、配对记录、排序和像素颜色','根据新的投影结果重新生成']]),
    p('一份场景参数可以从多个相机位置渲染。相机运动后，前一帧的候选与深度关系不一定适用；原始实现为新相机重新走前向流程。'),
    note('场景参数不变，并不意味着每帧工作量相同：相机变化会改变屏幕覆盖范围、遮挡关系和提前结束的位置。'))
add('backward-memory', 'learning', '深入：为什么不保存每个像素的完整历史？',
    p('如果为每个像素保存所有贡献高斯与每一步 T，内存会随重叠深度增长。原始实现保存最终透射率、最后贡献位置等状态，反向重新遍历有序候选列表。'),
    math_eq(mr(sub(mi('T'),'before'),mo('='),frac(sub(mi('T'),'after'),mn(1)+mo('−')+mi('α')),GAP,'<mtext>（对实际参与合成的项）</mtext>'), '参与合成前的透射率等于合成后的透射率除以一减有效不透明度'),
    p('before、after 分别表示合成当前高斯之前和之后。前向将 T 乘以 (1−α)，反向就除以这个因子；例如合成后 T=0.25、α=0.5，可以恢复合成前的 T=0.5。此式要求 α&lt;1。'),
    p('反向从后向前遍历，并按前向的跳过、终止和 α 上限规则重建状态。否则恢复出的系数就与生成图像时不一致。'),
    note('保存完整历史可以减少反向重算，但内存随每像素的贡献数量增长；仅保存关键状态能节省内存，却需要再次遍历列表、计算权重和恢复 T。'), deep=True, refs=('paper','backward'))

add('cost-model', 'performance', '不要只数高斯：三个规模决定不同阶段',
    table(['规模','定义','主要影响'], [
        ['N','高斯数量','预处理、参数存储'],
        [math_inline(mr(mi('M'),mo('='),'<munder><mo>∑</mo><mi>i</mi></munder>',sub(mi('n'),'i'))),'高斯–Tile 配对记录总数；nᵢ 为高斯 i 的候选 Tile 数','写出、排序、范围与缓冲区'],
        [math_inline(mr(mi('K'),mo('='),'<munder><mo>∑</mo><mi>p</mi></munder>',sub(mi('k'),'p'))),'各像素实际检查的候选数之和；kₚ 是像素 p 实际检查的数量，结束后不再计入候选','像素遍历与合成']]),
    p('四高斯算例中，N=4，M=11。若 Tile 5 的 256 个像素都检查 3 个候选，仅这一块就为 K 增加 768；提前结束会减少这个数量。'),
    p('同样 N 个高斯，屏幕足迹更大时 M 可能更多；覆盖重叠更深、较晚达到不透明时 K 可能更大。改变相机也会改变这些量。'),
    flow('一帧时间 = 预处理时间 + 分组与排序时间 + 像素合成时间 + 其他开销'),
    note('这是解释成本的分解，不是能仅凭 N、M、K 精确预测毫秒数的硬件模型。'))
add('tile-tradeoff', 'performance', 'Tile 越小一定越快吗？',
    table(['改变 Tile 大小','可能得到什么','可能付出什么'], [
        ['较小 Tile','候选更精细，减少无关像素检查','配对记录数 M 增加、Block 数与组织成本增加'],
        ['较大 Tile','更多像素共用候选，可能减少配对记录','无效候选检查更多，块内差异与资源需求变化']]),
    p('一个高斯覆盖范围固定时，用更细的 Tile 划分，往往会产生更多配对记录；但列表对每个像素更有针对性。效果还取决于场景、屏幕分辨率与 kernel 设计。'),
    note('只减少像素合成时间，可能被更多排序时间抵消。比较 Tile 大小时，要同时记录完整帧时间和输出图像的误差。'))
add('measure', 'performance', '怎样设计一组能回答问题的性能实验？',
    table(['控制项','记录项','比较目的'], [
        ['固定场景、相机、分辨率与阈值','N、M、K 或候选分布；各阶段时间','定位成本落在哪里'],
        ['只改变相机距离','足迹大小、配对记录数、帧时间','检验“点数相同，工作是否相同”'],
        ['只改变提前结束阈值','帧时间、图像误差','量化质量与速度折中']]),
    p('预热后测多帧，记录 GPU、实现版本与计时范围，区分渲染 kernel 时间和完整帧时间。GPU 事件用于相关设备区间；跨 CPU / GPU 的完整时间还需要保证完成后再读时钟。'),
    note('帧时间变短后，再检查图像是否因更早结束而丢失细节。浏览器交互用于核对算法过程，CUDA 性能需要在实际 GPU 上测量。'))
add('limits', 'performance', '哪些近似与限制，会在图像中暴露？',
    table(['条件','需要注意的现象'], [
        ['大足迹或复杂遮挡','共享中心深度排序与局部投影近似可能失准'],
        ['训练视角覆盖不足','未观察区域的几何或外观可能不可靠'],
        ['分辨率与观察距离改变','屏幕空间采样、滤波与细节可能变化'],
        ['透明 / 反射外观复杂','拟合的外观不等于恢复了完整物理材质']]),
    p('检查这些现象时，固定场景和相机，分别改变投影、排序、采样或提前结束的设置，才能区分图像误差来自哪里。'), refs=('paper',))
add('summary', 'performance', '把整帧放回一起：表示、组织与执行',
    fig('pipeline', '从高斯参数到屏幕像素：每个阶段改变数据的形式，也改变并行工作的单位。'),
    table(['应该能够解释','关键回答'], [
        ['图像怎样形成？','投影足迹、有效不透明度 α、按深度合成'],
        ['为什么需要前缀和与排序？','可变数量的唯一写址、Tile 分组与前后顺序'],
        ['GPU 怎样协作？','一 Tile 一 Block，像素私有 C/T，批量 shared 复用'],
        ['为什么有时不快？','配对记录增多、冗余检查、长尾、同步与组织成本']]),
    note('沿 Tile 5 的 G₀ → G₂ → G₁ 回顾：这些记录为什么属于 Tile 5？谁装入参数？像素 (17,18) 由谁计算并写出？'))
add('memory-budget', 'performance', '深入：估算参数与配对记录缓冲区',
    p('以一个教学布局估算：位置 3、尺度 3、四元数 4、不透明度 1、三阶 SH 的 RGB 系数 48，共 59 个 FP32，约 236 字节 / 高斯。100 万个高斯约 236 MB（十进制），不含对齐、梯度和优化器状态。'),
    math_eq(mr(mn(8),mo('+'),mn(4),mo('='),mn(12),'<mtext> 字节（每条记录）</mtext>',GAP,mn(12),mo('×'),sup(mn(10),7),mo('='),mn(120),'<mtext> MB</mtext>'), '8字节键加4字节ID，每条12字节；一千万条记录占120MB'),
    p('排序通常还需要输入 / 输出缓冲与临时工作区，不能把 12M 字节当作整个排序过程的峰值。训练还需要梯度、优化器状态、前向中间量等。'),
    note('实际内存由实现的数据类型、布局与库决定；本页是账目模型，不是某块 GPU 上的实测占用。'), deep=True)
add('reading', 'performance', '深入：从原始论文到实现的阅读顺序',
    table(['想核对什么','优先阅读'], [
        ['场景表示与投影','论文 §4；forward.cu 的协方差与投影计算'],
        ['优化与密度控制','论文 §5；train.py、gaussian_model.py'],
        ['排序与 Tile 并行','论文 §6 / 附录 C；rasterizer_impl.cu'],
        ['像素遍历与反向状态','forward.cu / backward.cu']]),
    p('源码入口对照：preprocessCUDA 产生屏幕参数；rasterizer_impl.cu 中的扫描、duplicateWithKeys 与 SortPairs 组织配对记录；identifyTileRanges 找组边界；renderCUDA 读取列表并维护每像素 C、T。沿输出数组追到下一阶段读取者。'),
    p('核对前缀和时，官方实现使用包含自身的前缀和，再取前一项作为起点；本讲直接使用独占前缀和，得到的写出区间相同。核对共享加载时，官方实现分字段搬运参数，本讲用 projected 结构集中表示。'),
    p('复现结果时记录源码提交号、运行配置、场景、相机和阈值，以便把数值差异与性能差异对应到具体实现。'),
    deep=True, refs=tuple(SOURCES))

assert len([s for s in SLIDES if not s['deep']]) == 49
assert len([s for s in SLIDES if s['deep']]) == 8
assert len({s['id'] for s in SLIDES}) == len(SLIDES)
