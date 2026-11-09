"""Original SVG teaching diagrams. No downloaded media or third-party artwork."""
from html import escape
from pathlib import Path
import math

GREEN='#176653'; INK='#253e2e'; MUTED='#6d8176'; LINE='#cbdcd2'; RED='#d46a57'; BLUE='#5686bd'
def text(x,y,s,size=18,color=INK,anchor='start'):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" text-anchor="{anchor}">{escape(s)}</text>'
def box(x,y,w,h,title,sub='',color=GREEN):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="#f1f7f3" stroke="{LINE}"/>'+text(x+w/2,y+32,title,19,color,'middle')+(text(x+w/2,y+58,sub,14,MUTED,'middle') if sub else '')
def arrow(x1,y1,x2,y2,color=GREEN):
    return f'<path d="M{x1},{y1} L{x2},{y2}" stroke="{color}" stroke-width="2" fill="none" marker-end="url(#arrow)"/>'
def ellipse(x,y,rx,ry,angle=0,color=GREEN,opacity=.25):
    return f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" transform="rotate({angle},{x},{y})" fill="{color}" fill-opacity="{opacity}" stroke="{color}" stroke-width="1.5"/>'
def wrap(body,h=300):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 {h}" role="img"><defs><marker id="arrow" markerWidth="9" markerHeight="9" refX="7" refY="4.5" orient="auto"><path d="M0 0L8 4.5L0 9" fill="{GREEN}"/></marker></defs><rect width="800" height="{h}" rx="16" fill="#fafcfb"/><g font-family="-apple-system,BlinkMacSystemFont,PingFang SC,Microsoft YaHei,sans-serif">{body}</g></svg>'

def build(destination):
    d=Path(destination); d.mkdir(parents=True,exist_ok=True)
    figs={}
    b=''
    for cx,angle,title in [(195,0,'未旋转：主轴与坐标轴对齐'),(605,-45,'绕 z 轴旋转 45°')]:
        cy=145
        b+=text(cx,32,title,19,INK,'middle')
        b+=f'<path d="M{cx-125} {cy}H{cx+125}M{cx} {cy+85}V{cy-88}" stroke="{LINE}" stroke-width="1.5" stroke-dasharray="5 4" fill="none"/>'
        b+=text(cx+132,cy+5,'x',17,MUTED)+text(cx+8,cy-82,'y',17,MUTED)
        b+=ellipse(cx,cy,90,45,angle,GREEN,.16)
        b+=f'<g transform="rotate({angle},{cx},{cy})"><path d="M{cx-90} {cy}H{cx+90}" stroke="{GREEN}" stroke-width="3"/><path d="M{cx} {cy-45}V{cy+45}" stroke="{BLUE}" stroke-width="3"/></g>'
        b+=f'<circle cx="{cx}" cy="{cy}" r="4" fill="{INK}"/>'
        b+=text(cx,245,'主轴标准差：2 和 1',17,MUTED,'middle')
    b+=arrow(355,145,425,145)
    figs['covariance-rotation']=wrap(b,260)
    # Three principal ellipses of a single Gaussian's illustrative isosurface.
    def projected(v):
        x,y,z=v;a=-.4;b=.55
        xx=math.cos(b)*x+math.sin(b)*z
        zz=-math.sin(b)*x+math.cos(b)*z
        return (390+math.cos(a)*xx-math.sin(a)*y,175+math.sin(a)*xx+math.cos(a)*y-.4*zz)
    b=ellipse(390,175,118,45,-18,GREEN,.13)
    for plane in range(3):
        points=[]
        for i in range(73):
            t=i*math.pi/36;v=[0,0,0];a0=plane;a1=(plane+1)%3
            v[a0]=[130,55,38][a0]*math.cos(t);v[a1]=[130,55,38][a1]*math.sin(t)
            points.append(projected(v))
        b+='<polyline points="'+' '.join(f'{x:.1f},{y:.1f}' for x,y in points)+'" fill="none" stroke="'+GREEN+'" stroke-opacity=".65" stroke-width="1.5"/>'
    for v,color in [([130,0,0],RED),([0,55,0],BLUE),([0,0,38],GREEN)]:
        x,y=projected(v);b+=f'<path d="M390 175L{x:.1f} {y:.1f}" stroke="{color}" stroke-width="3"/>'
    b+='<circle cx="390" cy="175" r="5" fill="#253e2e"/>'
    b+=text(42,92,'中心 μ：放在哪里',21)+arrow(175,107,380,170)
    b+=text(520,55,'三个尺度：各方向多宽',21)+arrow(565,70,470,140)
    b+=text(525,245,'旋转：长轴朝向哪里',21)+arrow(540,222,475,188)
    b+=text(45,280,'颜色 / SH：外观',21)+text(45,311,'不透明度：贡献强弱',21)
    b+=text(400,350,'椭球画的是等值面，高斯贡献从中心向外平滑减弱',17,MUTED,'middle')
    figs['gaussian-anatomy']=wrap(b,375)
    b=''
    for x,y,color in [(340,100,GREEN),(420,150,RED),(480,95,BLUE)]:
        b+=ellipse(x,y,45,70,-25,color)+ellipse(x,y,45,18,0,color,.08)
    for x,y,label in [(95,95,'照片 A'),(145,225,'照片 B'),(650,190,'新视角')]:
        b+=box(x-48,y-30,100,64,label)+arrow(x+(55 if x<400 else -55),y,310 if x<400 else 530,150)
    b+=text(400,275,'固定场景 · 多个相机',17,MUTED,'middle'); figs['scene']=wrap(b)
    b=''
    items=[('高斯参数','N 个基元'),('投影 / 计数','屏幕足迹'),('Scan / 写出','M 条配对记录'),('排序 / 分段','Tile 有序列表'),('并行渲染','P 个像素')]
    for i,(title,sub) in enumerate(items):
        x=18+i*156; b+=box(x,44,140,80,title,sub)
        if i<4:b+=arrow(x+142,84,x+152,84)
    b+=text(400,165,'并行单位：高斯 → 配对记录 → Tile / 像素',18,MUTED,'middle');figs['pipeline']=wrap(b,195)
    b=text(190,40,'只有位置',20,INK,'middle')+text(590,40,'大小、方向与柔和覆盖',20,INK,'middle')
    for j in range(3):
        for i in range(5):
            x=90+i*50;y=95+j*58+math.sin(i)*10
            b+=f'<circle cx="{x}" cy="{y}" r="4" fill="{GREEN}"/>'
            b+=ellipse(x+400,y,34,22,-20,GREEN,.17)
    b+=arrow(355,150,420,150);figs['point-splat']=wrap(b,285)
    b=box(25,85,150,85,'世界坐标','μw')+arrow(180,128,255,128)+box(265,85,190,85,'相机坐标','Rc μw + tc')+arrow(460,128,535,128)+box(545,85,215,85,'屏幕坐标','(fx X/Z + cx, fy Y/Z + cy)')+text(400,220,'先改变坐标系，再除以深度',18,MUTED,'middle');figs['camera']=wrap(b,265)
    b=ellipse(170,145,65,95,-35,GREEN)+ellipse(170,145,65,25,0,GREEN,.06)+text(170,270,'三维尺度 + 方向',18,INK,'middle')
    b+=arrow(265,110,400,78)+arrow(265,185,400,215)
    b+=ellipse(530,85,100,27,12,BLUE)+text(680,90,'视角 A',17)
    b+=ellipse(530,215,54,43,-35,RED)+text(680,220,'视角 B',17)
    figs['projection']=wrap(b,310)
    b=text(180,35,'Grid：4 × 4 个 Block',19,INK,'middle')+text(580,35,'一个 Block：16 × 16 线程',19,INK,'middle')
    for y in range(4):
        for x in range(4):b+=f'<rect x="{65+x*55}" y="{65+y*48}" width="50" height="43" rx="4" fill="{GREEN if (x,y)==(1,1) else "#e3eee7"}" stroke="white"/>'
    b+=arrow(300,155,410,155)
    for y in range(16):
        for x in range(16):b+=f'<rect x="{470+x*14}" y="{60+y*14}" width="12" height="12" fill="{GREEN if y==5 else "#b6d7c9"}"/>'
    b+=text(580,310,'每个线程唯一写出一个像素',17,MUTED,'middle');figs['ownership']=wrap(b,340)
    b=box(20,85,180,85,'Global','高斯参数数组')+arrow(210,125,300,125)+box(310,85,180,85,'Shared','当前候选批次')
    for y,t in [(45,'像素 p₀：C₀ / T₀'),(130,'像素 p₁：C₁ / T₁'),(215,'像素 p₂：C₂ / T₂')]:
        b+=arrow(500,125,570,y+25)+box(580,y,200,65,t)
    b+=text(275,240,'合作装入一次',17,MUTED,'middle')+text(680,315,'各自计算，共同读入',17,MUTED,'middle');figs['shared']=wrap(b,345)
    b=''
    for i,(t,sub) in enumerate([('装入','各线程搬运'),('同步 ①','装入完成'),('使用','更新私有 C/T'),('同步 ②','旧数据读完'),('再装入','覆盖下一批')]):
        b+=box(18+i*156,60,140,85,t,sub)
        if i<4:b+=arrow(160+i*156,103,171+i*156,103)
    b+=text(400,195,'所有参与者经过相同的批次交接',18,MUTED,'middle');figs['barriers']=wrap(b,235)
    b=''
    for i,(n,width) in enumerate([(0,20),(24,95),(80,210),(410,570)]):
        y=45+i*55;b+=text(25,y+18,f'Tile {i}',18)+f'<rect x="120" y="{y}" width="{width}" height="28" rx="5" fill="{GREEN}" opacity="{.35+i*.18}"/>'+text(135+width,y+21,str(n)+' 候选',16)
    b+=text(400,295,'示意工作量，不代表测量时间',17,MUTED,'middle');figs['imbalance']=wrap(b,330)
    b=''
    for i,(t,sub) in enumerate([('选相机','训练照片'),('渲染','当前参数'),('比较','图像损失'),('反向','参数梯度'),('更新','再次迭代')]):
        b+=box(18+i*156,55,140,80,t,sub)
        if i<4:b+=arrow(160+i*156,95,171+i*156,95)
    b+=f'<path d="M730 145V190H90V145" stroke="{GREEN}" fill="none" stroke-dasharray="6 5" marker-end="url(#arrow)"/>';figs['training']=wrap(b,225)
    b=box(300,90,190,85,'高斯 Gᵢ','共享参数 / 总梯度')
    for i,y in enumerate([30,115,200]):
        b+=box(20,y,170,65,f'像素 p{i}')+arrow(290,130,195,y+32)
        b+=box(610,y,170,65,f'像素 p{i} 的梯度')+arrow(605,y+32,500,130)
    b+=text(110,305,'前向：读取参数',17,MUTED,'middle')+text(680,305,'反向：归约梯度',17,MUTED,'middle');figs['gradients']=wrap(b,340)
    b=''
    for x,title in [(130,'克隆'),(400,'拆分'),(665,'剪枝')]:b+=text(x,35,title,20,INK,'middle')
    b+=ellipse(90,100,28,20)+arrow(130,100,175,100)+ellipse(190,85,28,20)+ellipse(205,120,28,20)
    b+=ellipse(340,100,48,29,-20)+arrow(395,100,425,100)+ellipse(450,82,25,16,-20)+ellipse(480,120,25,16,-20)
    b+=ellipse(610,100,35,25,0,GREEN,.08)+arrow(655,100,690,100)+text(725,106,'∅',30,MUTED,'middle')
    b+=text(400,195,'改变参数集合的数量与分布；同时改变后续计算量',17,MUTED,'middle');figs['density']=wrap(b,235)
    for name,svg in figs.items(): (d/(name+'.svg')).write_text(svg,encoding='utf-8')
    return list(figs)
