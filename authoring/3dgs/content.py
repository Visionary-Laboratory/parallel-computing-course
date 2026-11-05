"""Editable Chinese lecture. Original teaching text and examples; source links below.

Build with: python3 authoring/3dgs/build.py
No network, packages, or original private course generator required.
"""
from html import escape

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
def eq(text): return '<div class="equation" role="math">' + text + '</div>'
def table(head, rows):
    return '<div class="table-scroll"><table><thead><tr>' + ''.join('<th scope="col">'+c+'</th>' for c in head) + '</tr></thead><tbody>' + ''.join('<tr>'+''.join('<td>'+str(c)+'</td>' for c in row)+'</tr>' for row in rows) + '</tbody></table></div>'
def code(text): return '<pre><code>' + escape(text.strip()) + '</code></pre>'
FIGURE_HEIGHTS = dict(scene=300, pipeline=195, **{'point-splat':285}, camera=265, projection=310, ownership=340, shared=345, barriers=235, imbalance=330, training=225, gradients=340, density=235)
def fig(name, caption): return f'<figure><img src="../../materials/lectures/3dgs/{name}.svg" width="800" height="{FIGURE_HEIGHTS[name]}" alt="{escape(caption, quote=True)}" loading="lazy"><figcaption>{caption}</figcaption></figure>'
def demo(name, caption): return f'<div class="demo" data-demo="{name}"></div><p class="caption">{caption}</p>'
def answer(text): return '<details class="answer"><summary>查看参考答案</summary><div>'+text+'</div></details>'
def add(id, topic, title, *body, refs=(), deep=False):
    SLIDES.append(dict(id=id, topic=topic, title=title, html='\n'.join(body), refs=list(refs), deep=deep))

add('novel-view', 'task', '拍过的照片，怎样变成没有拍过的视角？',
    p('围着一个静态场景拍摄多张照片。现在移动一台虚拟相机，希望得到这个新位置应当看到的图像。这叫<strong>新视角合成</strong>。相机移动后，遮挡、物体的投影位置与外观都会改变。'),
    fig('scene', '同一个场景，多个已知相机与一个待渲染的新相机；图为课程原创示意。'),
    p('3D Gaussian Splatting（3DGS）用一组可优化的三维高斯描述场景，再把它们投影、合成为图像。先到<a href="https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/" target="_blank" rel="noreferrer">原论文项目页</a>观察真实场景视频，再带着“每一帧如何算出来”回到本讲。'),
    note('本讲目标：既能解释图像如何形成，也能指出计算交给谁、数据放在哪里、何时需要等待。'), refs=('project','paper'))
add('train-vs-render', 'task', '先分清两件事：学习场景与渲染场景',
    table(['过程','输入','输出 / 操作'], [
        ['学习 / 训练','多视角照片、相机参数、初始点','反复渲染并与照片比较，更新高斯参数'],
        ['渲染 / 推理','学好的高斯、一个目标相机','生成该相机的一帧图像']]),
    p('原始方法通常使用 SfM（运动恢复结构）提供相机位姿与稀疏点云。这里把它们作为已知输入；课堂不展开相机标定。'),
    p('先讲清<strong>固定参数时的一次前向渲染</strong>，再回到如何训练。移动虚拟相机需要重新投影和组织屏幕上的工作，通常不需要重新训练整个场景。'), refs=('paper',))
add('route', 'task', '沿一帧图像，串起前面学过的并行思想',
    fig('pipeline', '高斯参数 → 投影 → 计数与前缀和 → 生成引用 → 排序与分段 → Tile 渲染 → 图像。'),
    table(['已有知识','在本讲解决什么问题'], [
        ['第三讲：计数、前缀和、唯一地址','一个高斯对应多个 Tile，怎样并行写出可变数量的记录？'],
        ['第五讲：线程索引与输出所有权','由哪个线程写一个像素？'],
        ['第六讲：shared、同步与复用','相邻像素怎样共用一批高斯参数？']]),
    note('一路反复问：哪些工作独立？哪些有顺序？为了减少计算，额外花了什么成本？'))

add('point-to-splat', 'representation', '一个点的位置，还不足以覆盖一块表面',
    fig('point-splat', '左：只有中心的稀疏点；右：中心带有大小与方向，形成彼此重叠的柔和覆盖。'),
    p('一个点只告诉我们“在哪里”。为它增加空间尺度与方向，就能描述一个有范围的局部贡献：中心附近强，离中心越远越弱。'),
    p('图中的椭圆或椭球是等值线 / 等值面。高斯并不是边界坚硬的小球，也不是固定大小的方形像素。多个高斯可以重叠，共同描述同一片区域。'), refs=('paper',))
add('gaussian-falloff', 'representation', '从一维开始：距离怎样改变贡献？',
    eq('g(x) = exp[−½ ((x − μ) / σ)²]'),
    table(['离中心的距离','0','σ','2σ','3σ'], [['相对权重','1.000','0.607','0.135','0.011']]),
    p('<strong>μ</strong> 控制位置，<strong>σ &gt; 0</strong> 控制宽度。相同距离下，σ 越大，衰减越慢。这里使用峰值为 1 的未归一化高斯核，后续还要乘上可学习的不透明度。'),
    note('数学上高斯没有有限边界；程序为了节省计算，需要选定有限的处理范围。'))
add('ellipse', 'representation', '二维高斯：拉长、旋转，改变覆盖形状',
    demo('ellipse', '调节两个尺度、角度和不透明度。图像按二维高斯公式计算；虚线为 2σ 等值线，图示不代表 GPU 性能。'),
    p('两个方向尺度相同，等值线是圆；尺度不同，就是椭圆。旋转只改变方向，不改变两个主轴尺度。'),
    eq('g(p) = exp[−½ (p − μ)ᵀ Σ⁻¹ (p − μ)]'),
    p('Σ（协方差）把大小与方向放在同一个矩阵里。我们先用图理解它，再把同一思路搬到三维。'))
add('gaussian-record', 'representation', '一个三维高斯，需要保存哪些参数？',
    table(['参数','含义','影响图像的方式'], [
        ['中心 μ ∈ ℝ³','在场景中的位置','投影中心与深度'],
        ['尺度 s ∈ ℝ³、旋转 q','三个方向的大小与姿态','投影足迹的形状'],
        ['不透明度 o','贡献的强弱','局部 alpha 与遮挡'],
        ['颜色参数 / SH 系数','随观察方向变化的外观','该相机下的 RGB']]),
    p('这是一份显式参数表。渲染时反复读取它；训练时更新它。高斯数量也可以随训练改变。'),
    note('高斯是可优化的场景基元，不是预先知道的真实物体，也不必一一对应物体表面上的点。'), refs=('paper','model'))
add('covariance', 'representation', '把尺度与旋转组合成协方差',
    eq('S = diag(sₓ, sᵧ, s_z)　　Σ = R S Sᵀ Rᵀ'),
    p('先沿局部坐标轴缩放，再旋转到世界坐标系。这里 s 是标准差尺度，因此协方差中出现 s²。R 来自归一化旋转四元数。'),
    table(['选择','结果'], [['sₓ = sᵧ = s_z','各向同性；旋转不改变形状'],['sₓ ≫ sᵧ ≈ s_z','沿一个方向拉长'],['两个尺度大、一个尺度小','薄片状局部覆盖']]),
    p('正尺度配合有效旋转使协方差保持正定。优化时可用 exp 将无约束变量转换为正尺度。'), refs=('paper','model'))
add('opacity', 'representation', '不透明度与高斯权重，是两个不同的量',
    eq('αᵢ(p) = oᵢ · gᵢ(p)'),
    p('oᵢ 是这个高斯的参数；gᵢ(p) 随像素位置变化；αᵢ(p) 才是它在该像素上的局部 alpha。中心附近 α 较大，边缘较小。'),
    table(['假设 o = 0.8','中心 g=1','较远处 g=0.25'], [['局部 alpha','0.8','0.2']]),
    note('这些 alpha 不需要在所有高斯之间归一化到总和为 1。后面的透射率会决定前后遮挡的权重。'), refs=('paper',))
add('appearance', 'representation', '为什么颜色可以随观察方向变化？',
    p('同一位置从不同方向看，可能有不同亮度或高光。只保存固定 RGB 会限制这种外观的表达。原始 3DGS 用球谐函数（SH）的系数表达方向相关颜色。'),
    eq('c(d) = Σₖ aₖ Yₖ(d)　（对 R、G、B 分别求值）'),
    p('d 是约定好的观察方向，Yₖ 是固定方向基函数，aₖ 是学习得到的系数。可以把它理解为“用几种已知的方向变化模式，组合出颜色”。'),
    p('课堂先固定各高斯的 RGB，便于手算与追踪渲染；真实实现可在每高斯预处理阶段求该视角下的颜色。'), refs=('paper','forward'))

add('camera-coordinates', 'projection', '先把中心变换到相机坐标系',
    fig('camera', '世界中的高斯中心先变换到相机坐标，再通过透视投影映射到屏幕；相机朝 +Z 的约定仅用于本讲算例。'),
    eq('μ_c = R_c μ_w + t_c'),
    p('世界坐标描述场景中的固定位置；相机坐标描述相对当前相机的位置。用 Z_c 表示沿相机前向的深度。相机动了，同一高斯的相机坐标与排序深度就可能改变。'),
    note('相机旋转 R_c 与高斯自身旋转 R 是不同的矩阵；实际工程还要统一行列向量、坐标轴与矩阵存储约定。'))
add('perspective', 'projection', '透视投影：越远，屏幕位移越小',
    eq('u = fₓ X_c / Z_c + cₓ　　v = fᵧ Y_c / Z_c + cᵧ'),
    p('fₓ、fᵧ 是以像素计的焦距，(cₓ,cᵧ) 是主点。下例取 fₓ=fᵧ=100，主点 (32,32)，只比较位置：'),
    table(['相机坐标 (X,Y,Z)','屏幕坐标 (u,v)'], [['(0, 0, 2)','(32, 32)'],['(0.2, 0, 2)','(42, 32)'],['(0.2, 0, 4)','(37, 32)']]),
    p('第二、三个中心的 X 相同，深度加倍后，偏离主点的距离减半。Z 接近零时除法不稳定，不能把所有输入都直接投影。'))
add('project-shape', 'projection', '投影一个高斯，不能只投影中心',
    fig('projection', '同一个三维椭球从不同观察方向投影，屏幕足迹的大小与长轴方向都可能改变。'),
    p('如果所有中心都画成固定半径的圆，就丢掉了三维尺度、旋转与透视变化。除了中心 μ₂D，还需要得到屏幕上的二维协方差 Σ₂D。'),
    p('透视包含除法，是非线性映射。原始方法在高斯中心附近做局部线性近似，用这个小范围内的“变化率”来传播形状。'),
    note('“投影后是二维高斯”在这里是一种局部近似，不是任意大三维高斯经过透视后的精确恒等式。'), refs=('paper',))
add('project-covariance', 'projection', '用局部变化率把三维形状带到屏幕',
    eq('Σ_c = R_c Σ R_cᵀ　　Σ₂D ≈ J Σ_c Jᵀ'),
    p('J 是 2×3 的投影雅可比矩阵：相机坐标改变一点，屏幕坐标改变多少。矩阵尺寸检查：2×3 · 3×3 · 3×2 → 2×2。'),
    p('先记住数据流：<strong>三维协方差 → 相机方向下的协方差 → 屏幕二维协方差</strong>。课堂主线不要求手推每个偏导。'),
    p('得到 Σ₂D 后，计算它的逆矩阵 Q，用于对每个候选像素求高斯权重。数值稳定与屏幕空间滤波还需要实现中的额外处理。'), refs=('paper','forward'))
add('jacobian', 'projection', '深入：透视雅可比的每一项从哪里来？',
    eq('J = [ fₓ/Z　 0　 −fₓX/Z² ;　0　 fᵧ/Z　 −fᵧY/Z² ]'),
    p('对 u=fₓX/Z+cₓ 分别求 X、Y、Z 的偏导，得到第一行；v 的偏导给出第二行。靠近主轴时 X、Y 较小，深度扰动对屏幕位置的横向影响较弱。'),
    p('例如 X=Y=0，fₓ=fᵧ=f，三维各向同性 Σ=σ²I，则 Σ₂D=(fσ/Z)²I。深度加倍，屏幕标准差减半，协方差对角元变为四分之一。'),
    note('这个例子有明确的中心与各向同性假设；不能据此把任意旋转椭球都简化成同一个屏幕圆。'), deep=True, refs=('paper',))
add('finite-footprint', 'projection', '无限的高斯，有限的候选区域',
    p('不能为一个高斯访问整张图像。实现用有限半径得到屏幕包围框，再裁剪到图像范围。基线代码根据二维协方差的最大特征值估计约 3σ 半径。'),
    eq('r ≈ ceil(3 √λ_max(Σ₂D))'),
    p('包围框负责快速找<strong>候选 Tile</strong>；真正合成时仍要按椭圆公式计算每个像素的 alpha，并跳过很小的贡献。框内不等于有效贡献，框外也不是数学上严格为零。'),
    note('课程算例会直接给定整数中心、半径与深度，用于练习分组；这些值不声称来自某个真实训练场景。'), refs=('forward',))
add('preprocess', 'projection', '每高斯预处理：先做一次，供后面反复使用',
    table(['输入 / 步骤','输出'], [['中心与当前相机','可见性判断、屏幕中心、深度'],['尺度、旋转、相机','二维协方差与逆矩阵'],['方向与 SH 系数','当前视角颜色'],['屏幕足迹','包围框、候选 Tile 数']]),
    p('不同高斯的这些计算大体独立，可以按高斯并行。后续每个像素无需重新计算这个高斯的三维投影。不可见或没有候选 Tile 的高斯产生零条引用。'),
    note('并行单位会改变：现在是“每个高斯”，稍后变成“每个 Tile / 像素”。'), refs=('forward','pipeline'))

add('evaluate-alpha', 'compositing', '先算一个高斯在一个像素上的贡献',
    eq('δ = p − μ₂D　　Q = Σ₂D⁻¹'),
    eq('α(p) = o exp[−½(Qₓₓδₓ² + 2Qₓᵧδₓδᵧ + Qᵧᵧδᵧ²)]'),
    p('二维对称矩阵只需保存三个独立元素。交叉项带有系数 2；展开表达式时漏掉它，会改变旋转椭圆的形状。'),
    p('先用一个像素与一个高斯理解“离中心有多远”，再讨论多个高斯怎样叠加。实现中的 alpha 上限和微小贡献阈值属于数值与质量折中。'), refs=('forward',))
add('transmittance', 'compositing', '前面的覆盖，决定后面还能贡献多少',
    eq('C = 0，T = 1；从前到后遍历：'),
    eq('C ← C + T αᵢ cᵢ　　T ← T(1 − αᵢ)'),
    p('C 是已累计颜色；T 是剩余透射率。最开始没有遮挡，T=1。每个高斯先用当前 T 加入颜色，再减少留给后方的比例。'),
    eq('最终颜色 = C + T c_bg'),
    note('T 必须先用于本次颜色贡献，再更新给下一个高斯。颜色为 RGB 向量，T 与 α 是标量。'), refs=('paper',))
add('blend-demo', 'compositing', '追踪一个像素：红、绿、蓝怎样叠加？',
    demo('blend', '教学算例直接给定该像素的局部 alpha：G₀=0.5、G₂=0.25、G₁=0.5。它们不是整幅图共享的常数。'),
    p('黑色背景，从前向后为 G₀（红）→ G₂（绿）→ G₁（蓝）。逐步观察每个颜色分量和剩余 T。'),
    note('多个高斯共同影响一个像素，但它们的贡献权重不是简单平均。'))
add('order-matters', 'compositing', '交换深度顺序，为什么颜色变了？',
    table(['两个高斯，局部 α 都是 0.5','红色分量','蓝色分量','剩余 T'], [
        ['红在前、蓝在后','0.5','0.25','0.25'],['蓝在前、红在后','0.25','0.5','0.25']]),
    p('剩余透射率相同，但颜色不同。普通颜色相加可以交换次序；有遮挡的 alpha 合成不能随意交换前后次序。'),
    note('给每个高斯启动线程并 atomicAdd 颜色，并不能自动得到正确的透明合成。原子加解决写竞争，不解决深度语义。'))
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
    p('约 2 分钟。初始 C=0、T=1；红色 α=0.5 在前，蓝色 α=0.5 在后，黑色背景。'),
    code('''for (Gaussian g : front_to_back) {
    float a = alpha_at(g, pixel);
    C += __________;
    T  = __________;
}'''),
    p('补全表达式，并给出最终 RGB 与 T。若先更新 T 再计算 C，会发生什么？'),
    answer(p('<code>C += T * a * g.color;</code>，<code>T = T * (1-a);</code>。结果 RGB=(0.5,0,0.25)，T=0.25。先更新 T 会把当前高斯也当成其自身前方的遮挡，低估本次贡献。')))
add('composite-scan', 'compositing', '深入：像素内的合成能否使用 Scan？',
    eq('(Cₐ,Tₐ) ⊗ (Cᵦ,Tᵦ) = (Cₐ + TₐCᵦ, TₐTᵦ)'),
    p('把相邻、已保持深度顺序的片段表示为“局部颜色 + 透射率”，这个组合在精确算术下具有结合性，因此存在树形归约或扫描的可能。它不具有交换性，不能改变前后顺序。'),
    p('基线 Tile 渲染器选择每像素顺序遍历：像素间已有大量并行，还能自然利用提前结束。额外的像素内并行会带来中间状态、通信和调度成本。浮点运算重新分组也可能改变舍入。'),
    note('“这份实现里有顺序循环”不等于“数学上绝对无法并行”。'), deep=True)

add('naive-cost', 'tiles', '最直接的方法，为什么会做太多无用工作？',
    code('''parallel_for pixel in image:
    for gaussian in all_gaussians_in_depth_order:
        evaluate_and_blend(pixel, gaussian)'''),
    p('设有 P 个像素、N 个高斯，最直接的候选检查量为 P×N。1920×1080 像素与 100 万个高斯，对应约 2.07×10¹² 对组合；其中很多在屏幕上相距很远。'),
    note('第一步优化不是把同样多的检查发给更多线程，而是让每个像素只访问附近的候选高斯。'))
add('pixel-ownership', 'tiles', '选择输出所有者：每个像素交给一个线程',
    table(['方案','方便之处','还需要解决'], [
        ['按高斯散射到像素','直接遍历自己的覆盖范围','多个高斯写同一像素，还要满足深度顺序'],
        ['按像素聚集高斯','一个线程持有 C、T，唯一写出像素','怎样快速得到这个像素的候选列表？']]),
    p('基线选择后者。若为每个像素建立独立列表，管理与存储可能很贵。相邻像素的候选通常相似，于是让一小块屏幕共用一个列表。'),
    note('输出所有权解决前向颜色写冲突；候选列表解决“去哪里读”的问题。'), refs=('paper',))
add('tile-demo', 'tiles', '把屏幕分成 Tile，共用一份候选列表',
    demo('tiles', '64×64 教学屏幕，16×16 像素一个 Tile，共 4×4 个 Tile。点击或用键盘选择 Tile，查看候选及深度顺序。虚线框是候选包围框。'),
    p('同一 Tile 的像素遍历相同的高斯 ID 列表，但各自计算到高斯中心的距离、alpha 和颜色。列表相同不代表每个像素都有相同贡献。'),
    note('基线采用 16×16 Tile；这是具体实现选择，不是 3DGS 数学定义的一部分。'), refs=('paper','forward'))
add('toy-records', 'tiles', '贯穿算例：四个高斯产生多少条引用？',
    table(['高斯 / 颜色','中心 (u,v)','候选半径 r','深度 z','覆盖的 Tile ID'], [
        ['G₀ / 红','(20,20)',8,2,'0, 1, 4, 5'],
        ['G₁ / 蓝','(26,12)',6,4,'1, 5'],
        ['G₂ / 绿','(30,26)',10,3,'5, 6, 9, 10'],
        ['G₃ / 黄','(54,54)',4,5,'15']]),
    p('Tile ID = tile_y×4 + tile_x，左上角为 0。这里用半开包围框 [u−r,u+r)×[v−r,v+r)，求重叠 Tile，并裁剪到屏幕。'),
    p('这是明确约定的教学边界规则；真实渲染器的像素取样与边界取整须以源码为准。后续步骤始终使用这张表。'),
    note('四个高斯，十一条 Gaussian–Tile 引用。复制的是 ID / 排序记录，通常不需要为每条引用复制全部高斯参数。'))
add('scan-offsets', 'tiles', '数量不一样，先用前缀和分配写出位置',
    eq('count = [4, 2, 4, 1]　→　offset = [0, 4, 6, 10]'),
    table(['高斯','写出区间（左闭右开）'], [['G₀','[0,4)'],['G₁','[4,6)'],['G₂','[6,10)'],['G₃','[10,11)']]),
    p('offset 是独占前缀和，每个高斯提前知道自己专属的输出区域。即使 G₂ 最早执行，也只写 [6,10)，不会抢占 G₀ 的位置。'),
    p('原代码使用包含式扫描，再读取前一项得到起点；与这里直接计算独占前缀和的教学表示等价。'), refs=('pipeline',))
add('exercise-offset', 'tiles', '随堂填空 ②：给每个高斯一段独占空间',
    p('约 2 分钟。换一组覆盖数量 <code>count=[2,0,3,1]</code>，含一个不可见高斯。'),
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
    note('前缀和解决唯一写址；排序解决按 Tile 聚集与深度顺序。它们解决的是两个问题。'), refs=('pipeline',))
add('sort-pairs', 'tiles', '一次排序，先按 Tile，再按深度',
    table(['Tile','排序后高斯 ID','对应深度'], [
        [0,'G₀',2],[1,'G₀, G₁','2,4'],[4,'G₀',2],[5,'G₀, G₂, G₁','2,3,4'],[6,'G₂',3],[9,'G₂',3],[10,'G₂',3],[15,'G₃',5]]),
    p('把 Tile ID 放在主关键字，把相机空间深度放在次关键字；GPU 排序将相同 Tile 的记录聚集起来，并在组内按前到后排列。'),
    p('Tile 5 最能说明问题：写出时 G₁ 在 G₂ 前，排序后 G₂ 必须移到 G₁ 前。'),
    note('基线使用高斯中心深度共享组内顺序，未对每个像素重新精确求交排序，因此存在近似。'), refs=('paper','pipeline'))
add('tile-ranges', 'tiles', '找到每个 Tile 的起止位置，交给渲染器',
    eq('sorted IDs = [G₀, G₀,G₁, G₀, G₀,G₂,G₁, G₂, G₂, G₂, G₃]'),
    table(['Tile','范围 [begin,end)','列表长度'], [[0,'[0,1)',1],[1,'[1,3)',2],[4,'[3,4)',1],[5,'[4,7)',3],[15,'[10,11)',1]]),
    p('比较相邻排序记录的 Tile ID，边界处写出范围。没有记录的 Tile 保持空范围，渲染时输出背景。'),
    fig('pipeline', '投影后，依次计数、Scan、写记录、排序、找边界，再由各 Tile 读取自己的有序范围。'),
    note('阶段之间存在数据依赖。同一 CUDA stream 中按顺序提交这些操作即可建立执行顺序；无需在每一阶段都让 CPU 等待。'), refs=('pipeline',))
add('sort-key', 'tiles', '深入：64 位排序 Key 包含什么？',
    eq('key = (uint64(tile_id) ≪ 32) | depth_bits'),
    p('Tile ID 占高位，深度编码占低位。基线把通过可见性检查的正有限浮点深度按位解释为无符号整数；在这个范围内，位模式顺序与数值顺序一致。'),
    p('不能直接把相同做法用于任意带负号浮点数、NaN 或不一致的深度约定。位打包不是把深度数值强制转换成整数。'),
    p('Radix sort 的内部并行原理不在本讲展开；我们关注输入记录数、键和值的大小、临时缓冲区及其整体成本。'), deep=True, refs=('pipeline',))

add('block-mapping', 'execution', '一个 Tile 一个 Block，一个像素一个线程',
    fig('ownership', '64×64 屏幕对应 4×4 个 Block；每个 Block 的 16×16 个线程负责一个 Tile 的 256 个像素。'),
    code('''// 本讲采用 x 对应列、y 对应行
int x = blockIdx.x * 16 + threadIdx.x;
int y = blockIdx.y * 16 + threadIdx.y;
bool inside = x < width && y < height;'''),
    p('每个线程在寄存器中维护自己的 C 与 T，最后写出自己的像素。不要把一个 Block 等同于一个 SM：Block 由硬件调度，多个 Block 可在资源允许时驻留于同一 SM。'), refs=('forward',))
add('shared-load', 'execution', '同一份高斯参数，让整个 Block 共用',
    fig('shared', '线程合作搬入一批高斯参数；同步后，同一 Tile 的不同像素读取这些参数，维护各自的 C 与 T。'),
    p('设一批 B 个候选，Tile 有 256 个像素。若每个像素独立重复获取参数，会产生很多重复读取请求。合作加载后，多个像素从 shared 读取同一批屏幕中心、形状与不透明度。'),
    p('本讲伪代码把 RGB 也放入 shared 以便展示。官方基线对部分几何参数使用 shared，颜色访问方式应具体看源码。'),
    note('减少 global 读取请求，不等于显存流量或时间按同一倍数减少：缓存、shared 访问、同步与寄存器压力也参与总成本。'), refs=('forward',))
add('batch-lifetime', 'execution', '一块 Shared，分批复用：两道交接不能少',
    fig('barriers', '批次循环：所有参与者完成装入 → 同步 → 读取并合成 → 同步 → 下一批覆盖相同 shared 缓冲区。'),
    p('<strong>装入后同步：</strong>确保其他线程写的数据可以读取。<strong>覆盖前同步：</strong>确保旧数据已被所有仍需读取的线程使用完。'),
    p('第二道同步可以与下一轮开始处的集体操作合并，但不能凭空消失。同步必须沿一致的 Block 控制流执行。'),
    note('把同步放进“只有这个像素还没结束”的分支，会破坏全块交接。'))
add('render-pseudocode', 'execution', '把分工、复用与顺序放进同一个循环',
    code('''// 教学伪代码；所有线程执行外层循环和 barrier
bool done = !inside;
C = 0; T = 1;
for (batch in tile_sorted_list) {
    if (block_all(done)) break; // 全块投票，统一退出
    load_batch_cooperatively(shared, batch); // done 线程也参加
    block_barrier();
    if (!done) {
        for (g in valid_entries(shared)) {
            a = alpha_at(g, pixel);
            C += T * a * g.color;
            T *= (1 - a);
            if (T < epsilon) { done = true; break; }
        }
    }
    block_barrier(); // 等大家读完，才可覆盖 shared
}
if (inside) image[pixel] = C + T * background;'''),
    p('这里在纳入当前项后检查 T，省略 alpha 裁剪与微小贡献跳过，目的是突出并行结构；它不是官方 kernel 的逐行复制，也不保证逐位相同的结果。'), refs=('forward',))
add('pixel-done', 'execution', '像素结束，不等于线程可以提前 return',
    table(['状态','是否继续合成','是否参与加载 / 同步'], [
        ['有效像素，T 仍大','是','是'],['有效像素，T 已很小','否','是，直到全块统一结束'],['边缘 Tile 的越界线程','否','是，可能负责其他像素所需的数据']]),
    p('线程既是“一个像素的计算者”，又是“一个 Block 的搬运参与者”。前一个角色完成，并不代表后一个角色可以消失。'),
    note('全块投票所有像素都 done 后，才能统一提前结束批次循环。'), refs=('forward',))
add('exercise-sync', 'execution', '随堂填空 ③：把同步放在所有参与者都会经过的位置',
    p('约 3 分钟。假设下面每一轮都要复用同一个 shared 缓冲区。补出两处操作，并说明是否允许 <code>if (done) return;</code>。'),
    code('''for (batch in batches) {
    load_batch_cooperatively(shared, batch);
    __________;              // 开始读之前
    if (!done) blend_pixel(shared);
    __________;              // 下一轮覆盖之前
}'''),
    answer(p('两处都需要 Block 级 barrier（CUDA 中可用 <code>__syncthreads()</code>），并放在 <code>if (!done)</code> 外。这里不能让 done 线程自行 return：它还可能承担后续批次的加载，其他线程也依赖一致的协作协议。统一的全块退出需另行设计。')))
add('uneven-work', 'execution', '相同的线程数，不代表相同的工作量',
    fig('imbalance', '不同 Tile 的候选数与各像素结束位置不同；少量繁忙 Tile 可能成为整帧尾部。'),
    p('空背景 Tile 很快结束，复杂边缘可能覆盖很多高斯。即使同一 Tile 内，一些像素早已不透明，另一些仍在处理后方内容。'),
    p('Warp 内的分支让部分 lane 不再做合成，但这些线程仍可能参加加载和同步。整块何时结束，还取决于未完成的像素。'),
    note('看平均候选数还不够：也要看分布、长尾和每个像素实际处理到的位置。'))
add('implementation-map', 'execution', '回到源码：我们现在能读懂哪几段？',
    table(['逻辑阶段','官方入口 / 关键名字','阅读时追踪的状态'], [
        ['每高斯预处理','forward.cu / preprocessCUDA','屏幕中心、conic、radii、tiles_touched'],
        ['前缀和与分组','rasterizer_impl.cu / forward','point_offsets、duplicateWithKeys、SortPairs'],
        ['分段','identifyTileRanges','ranges[tile]'],
        ['每 Tile 渲染','forward.cu / renderCUDA','point_list、shared、T、C、done']]),
    p('先沿“输入 → 输出数组 → 下一阶段读取者”看调用链，再进入每行索引。网页示例是独立的教学简化；官方 main 分支会变化，复现实验应记录所用提交版本。'), refs=('forward','pipeline'))
add('termination-error', 'execution', '深入：提前结束，牺牲了多少颜色贡献？',
    p('如果颜色与背景的每个通道都位于 [0,1]，当前剩余透射率为 T，那么后方所有内容对最终颜色的总权重不超过 T。用背景替代后方内容时，每通道误差上界可由 T 控制。'),
    eq('T &lt; ε　⇒　在上述有界颜色条件下，每通道剩余误差 ≤ ε'),
    p('这个推理只解释截断当前像素的尾部；它不包含排序近似、滤波、低 alpha 跳过或训练变化。HDR 或未裁剪颜色也需要不同的颜色上界。'),
    note('阈值是质量与工作量之间的选择，不能只比较 FPS 而忽略误差。'), deep=True)
add('threshold-order', 'execution', '深入：教学循环与官方阈值次序有什么差别？',
    p('官方基线会对 alpha 设上限、跳过极小 alpha，并先计算候选 <code>test_T</code>。若它低于终止阈值，会标记 done 而不把该候选加入 C，也不把 test_T 写回 T。'),
    p('主线的伪代码选择“先合成，再检查 T”方便解释。二者共享线程协作结构，但阈值附近的数值行为不同。若做结果校验，应明确选择哪个规范，不能要求简化版本逐位等同官方实现。'),
    note('学习结构时允许简化；比较实现时必须把简化条件写清楚。'), deep=True, refs=('forward',))

add('training-loop', 'learning', '渲染器怎样成为一个可学习的模型？',
    fig('training', '选训练视角 → 渲染图像 → 与参考照片比较 → 反向传播 → 更新高斯参数，再次迭代。'),
    eq('L = (1 − λ)L₁ + λ(1 − SSIM)'),
    p('原始方法组合像素 L₁ 损失与结构相似性项。可先把 L 理解为“当前渲染与训练照片的差异”。选一个训练相机，计算一次损失，再把梯度传回高斯。'),
    p('要评估新视角能力，应另外使用未参加训练的相机图像；记住训练照片不等于学会所有新视角。'), refs=('paper','training'))
add('gradient-path', 'learning', '像素误差，沿哪条链回到高斯参数？',
    eq('损失 → 像素颜色 → alpha / 颜色 → 二维中心与形状 → 三维参数'),
    p('颜色不对，可调整颜色系数；覆盖位置不对，可调整中心；足迹不合适，可调整尺度与旋转；遮挡强弱不对，可调整不透明度。它们通常共同影响损失，并非各自负责一种独立错误。'),
    p('反向计算复用前向的排序与 Tile 范围。渲染器并不对排序位置、整数 Tile 归属、增删高斯等离散决定做普通连续求导。'),
    note('可微渲染描述局部连续计算的梯度路径；整个带分支、排序和拓扑变化的过程不是处处光滑。'), refs=('paper','backward'))
add('backward-scatter', 'learning', '前向一个像素一个所有者，反向却会汇到同一高斯',
    fig('gradients', '前向：一个高斯影响多个像素；反向：多个像素的梯度贡献汇聚到同一高斯参数。'),
    p('一个高斯覆盖多个像素甚至多个 Tile。每个像素算出的梯度都是总梯度的一部分，需要归约到同一个高斯参数上。'),
    p('基线反向 kernel 使用原子加来汇集一些参数梯度。这里的相加具有归约意义，与前向不允许乱序的透明颜色合成是不同问题。浮点归约次序仍可能影响末位舍入。'),
    note('同一个算法，前向和反向的读写冲突结构可以不同。'), refs=('backward',))
add('density-control', 'learning', '只有移动参数还不够：还要增加、拆分与删除',
    fig('density', '克隆增加局部表示能力；拆分把大覆盖分成较小基元；剪枝移除贡献低或不合适的基元。'),
    p('如果某一区域的表示不足，仅微调现有高斯可能不够。原始方法结合视空间位置梯度统计与尺度，决定哪些高斯适合克隆或拆分，并移除不透明度过低等不需要的基元。'),
    p('这些是周期性的自适应密度控制操作，不是在每次普通梯度更新中把数组长度连续地“求导出来”。'),
    note('高斯数增加可能改善质量，也可能增加显存、分组与渲染成本。数量与质量不是单调的一一对应。'), refs=('paper','model'))
add('learned-scene', 'learning', '训练完成，查看一帧时哪些东西还在变化？',
    table(['保持不变（固定场景推理）','随目标相机重新计算'], [
        ['中心、尺度、旋转、不透明度、SH 系数','相机坐标、屏幕中心与足迹'],
        ['高斯参数集合','视角相关颜色、可见性'],
        ['无需计算训练损失或反向梯度','Tile 覆盖、排序、像素合成']]),
    p('一份场景参数可以从多个相机位置渲染。相机运动后，前一帧的候选与深度关系不一定适用；本讲基线为新相机重新走前向流程。'),
    note('“显式表示”节省了某些查询计算，但并不意味着每帧只需把点画到屏幕上。'))
add('backward-memory', 'learning', '深入：为什么不保存每个像素的完整历史？',
    p('如果为每个像素保存所有贡献高斯与每一步 T，内存会随重叠深度增长。基线保存最终透射率、最后贡献位置等状态，反向重新遍历有序候选列表。'),
    eq('T_before = T_after / (1 − α)　（对实际参与合成的项）'),
    p('反向从后向前恢复需要的系数，同时复用前向列表和批量加载。必须与前向的跳过、终止和 alpha 裁剪规则匹配。'),
    note('这里体现“保存还是重算”的权衡。减少每像素历史存储，并不代表没有全局排序缓冲区或没有反向计算成本。'), deep=True, refs=('paper','backward'))

add('cost-model', 'performance', '不要只数高斯：三个规模决定不同阶段',
    table(['规模','定义','主要影响'], [
        ['N','高斯数量','预处理、参数存储'],
        ['M = Σᵢ nᵢ','Gaussian–Tile 引用数量','写出、排序、范围与缓冲区'],
        ['K = Σₚ kₚ','所有像素实际检查的候选总数','像素遍历与合成']]),
    p('同样 N 个高斯，屏幕足迹更大时 M 可能更多；覆盖重叠更深、较晚达到不透明时 K 可能更大。改变相机也会改变这些量。'),
    eq('一帧时间 = 预处理 + 分组 / 排序 + 渲染 + 其他开销'),
    note('这是解释成本的分解，不是能仅凭 N、M、K 精确预测毫秒数的硬件模型。'))
add('tile-tradeoff', 'performance', 'Tile 越小一定越快吗？',
    table(['改变 Tile 大小','可能得到什么','可能付出什么'], [
        ['较小 Tile','候选更精细，减少无关像素检查','引用 M 增加、Block 数与组织成本增加'],
        ['较大 Tile','更多像素共用候选，可能减少引用','无效候选检查更多，块内差异与资源需求变化']]),
    p('一个高斯覆盖范围固定时，用更细的 Tile 划分，往往会产生更多引用；但列表对每个像素更有针对性。效果还取决于场景、屏幕分辨率与 kernel 设计。'),
    note('在相同图像质量与正确性条件下测完整路径，再讨论某一个 kernel 的变化。'))
add('measure', 'performance', '怎样设计一组能回答问题的性能实验？',
    table(['控制项','记录项','比较目的'], [
        ['固定场景、相机、分辨率与阈值','N、M、K 或候选分布；各阶段时间','定位成本落在哪里'],
        ['只改变相机距离','足迹大小、引用数、帧时间','检验“点数相同，工作是否相同”'],
        ['只改变提前结束阈值','帧时间、图像误差','量化质量与速度折中']]),
    p('预热后测多帧，记录 GPU、实现版本与计时范围，区分渲染 kernel 时间和完整帧时间。GPU 事件用于相关设备区间；跨 CPU / GPU 的完整时间还需要保证完成后再读时钟。'),
    note('本讲交互图运行于浏览器，只演示算法；没有把浏览器动画速度当成 CUDA benchmark，也没有虚构 GPU 实测数据。'))
add('limits', 'performance', '哪些近似与限制，会在图像中暴露？',
    table(['条件','需要注意的现象'], [
        ['大足迹或复杂遮挡','共享中心深度排序与局部投影近似可能失准'],
        ['训练视角覆盖不足','未观察区域的几何或外观可能不可靠'],
        ['分辨率与观察距离改变','屏幕空间采样、滤波与细节可能变化'],
        ['透明 / 反射外观复杂','拟合的外观不等于恢复了完整物理材质']]),
    p('本讲讲的是原始 3DGS 思路及其基线并行结构。后续研究可以改进排序、抗锯齿、压缩与训练，但应先弄清改动解决的是哪一种误差或成本。'), refs=('paper',))
add('summary', 'performance', '把整帧放回一起：表示、组织与执行',
    fig('pipeline', '从高斯参数到屏幕像素：每个阶段改变数据的形式，也改变并行工作的单位。'),
    table(['应该能够解释','关键回答'], [
        ['图像怎样形成？','投影足迹、局部 alpha、按深度合成'],
        ['为什么需要前缀和与排序？','可变数量的唯一写址、Tile 分组与前后顺序'],
        ['GPU 怎样协作？','一 Tile 一 Block，像素私有 C/T，批量 shared 复用'],
        ['为什么有时不快？','引用膨胀、冗余检查、长尾、同步与组织成本']]),
    note('最后的自检：沿 Tile 5 的 G₀ → G₂ → G₁，说明每条记录从哪里来、哪个线程读、哪个线程写结果。'))
add('memory-budget', 'performance', '深入：估算参数与引用缓冲区',
    p('以一个教学布局估算：位置 3、尺度 3、四元数 4、不透明度 1、三阶 SH 的 RGB 系数 48，共 59 个 FP32，约 236 字节 / 高斯。100 万个高斯约 236 MB（十进制），不含对齐、梯度和优化器状态。'),
    eq('引用的一份 key + ID：8 + 4 = 12 字节；M=1000 万 → 120 MB'),
    p('排序通常还需要输入 / 输出缓冲与临时工作区，不能把 12M 字节当作整个排序过程的峰值。训练还需要梯度、优化器状态、前向中间量等。'),
    note('实际内存由实现的数据类型、布局与库决定；本页是账目模型，不是某块 GPU 上的实测占用。'), deep=True)
add('reading', 'performance', '深入：从原始论文到实现的阅读顺序',
    table(['想核对什么','优先阅读'], [
        ['场景表示与投影','论文 §4；forward.cu 的协方差与投影计算'],
        ['优化与密度控制','论文 §5；train.py、gaussian_model.py'],
        ['排序与 Tile 并行','论文 §6 / 附录 C；rasterizer_impl.cu'],
        ['像素遍历与反向状态','forward.cu / backward.cu']]),
    p('本讲图解与小型算例为课程原创。方法归属 Kerbl、Kopanas、Leimkühler 与 Drettakis（2023）。论文 HTML 标注 CC BY 4.0；官方代码具有自己的许可条款，本讲未复制或重新分发其实现。'),
    p('本页链接指向原论文与官方项目。复现时记录提交号、运行配置、场景、相机和阈值；不要把不同版本的性能数字直接混在一起。'),
    deep=True, refs=tuple(SOURCES))

assert len([s for s in SLIDES if not s['deep']]) == 49
assert len([s for s in SLIDES if s['deep']]) == 8
assert len({s['id'] for s in SLIDES}) == len(SLIDES)
