#!/usr/bin/env python3
"""Build an additive, local-only chapter without modifying the compiled course app."""
import json
import shutil
from html import escape, unescape
import re
from pathlib import Path
import content
import figures

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
SITE=ROOT/'site'
DEST=SITE/'lectures/3d-gaussian-splatting'
ASSETS=SITE/'materials/lectures/3dgs'
DEST.mkdir(parents=True,exist_ok=True)
ASSETS.mkdir(parents=True,exist_ok=True)
figures.build(ASSETS)
for name in ['viewer.css','viewer.mjs','model.mjs']:
    shutil.copyfile(HERE/name,ASSETS/name)

def refs(keys):
    return '<div class="references">来源与延伸：'+ ' · '.join(f'<a href="{content.SOURCES[k][1]}" target="_blank" rel="noreferrer">{escape(content.SOURCES[k][0])}</a>' for k in keys)+'</div>' if keys else ''

def page_idea(s):
    match=re.search(r'<div class="takeaway">(.*?)</div>',s['html'],re.S)
    if not match:match=re.search(r'<p>(.*?)</p>',s['html'],re.S)
    text=unescape(re.sub('<[^>]+>','',match.group(1) if match else s['title']))
    text=re.sub(r'\s+',' ',text).strip()
    return text if len(text)<=140 else text[:137]+'…'

def page_nav(prefix):
    rows=[]
    for i,s in enumerate(content.SLIDES):
        active=i==0;idea_id=f'{prefix}-idea-{s["id"]}'
        rows.append(f'''<li class="toc-entry{' is-current' if active else ''}" data-slide="{s['id']}" data-deep="{str(s['deep']).lower()}"{' hidden' if s['deep'] else ''}>
          <a href="#{s['id']}" data-target="{s['id']}" aria-expanded="{str(active).lower()}" aria-controls="{idea_id}"{' aria-current="location"' if active else ''}>
            <span class="toc-page-number">{i+1:02d}</span><span>{escape(s['title'])}{'<small>深入阅读</small>' if s['deep'] else ''}</span>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg>
          </a><div class="toc-page-idea" id="{idea_id}"{'' if active else ' hidden'}><strong>本页要点</strong><p>{escape(page_idea(s))}</p></div>
        </li>''')
    return f'<nav class="lecture-page-nav" aria-label="本讲逐页目录"><div class="lecture-page-nav-heading"><strong>本讲内容</strong><span class="toc-position">1 / 49</span></div><ol class="toc-page-list">{"".join(rows)}</ol></nav>'

slides=[];main_no=0;deep_no=0
for s in content.SLIDES:
    if s['deep']:deep_no+=1; label=f'深入 {deep_no:02d}'
    else:main_no+=1;label=f'{main_no:02d}'
    topic=dict(content.TOPICS)[s['topic']]
    slides.append(f'''<section class="lecture-slide{' deep' if s['deep'] else ''}" id="{s['id']}" data-topic="{s['topic']}" data-label="{label}" tabindex="-1">
      <div class="slide-label"><span>{label} · {topic}</span><a href="#{s['id']}" aria-label="链接到：{escape(s['title'],quote=True)}">主题链接 ↗</a></div>
      <h2>{s['title']}</h2>{s['html']}{refs(s['refs'])}
    </section>''')

topic_links=[]
for key,title in content.TOPICS:
    first=next(s for s in content.SLIDES if s['topic']==key)
    topic_links.append(f'<a href="#{first["id"]}" data-target="{first["id"]}">{title}</a>')

old_lectures=[('01-introduction','01','并行基础与性能模型'),('02-execution-models','02','并行硬件与执行模型'),('03-parallel-design','03','并行程序设计思想'),('04-memory-synchronization','04','缓存一致性与同步实现'),('05-cuda-introduction','05','CUDA 编程入门'),('06-memory-hierarchy','06','CUDA 内存层次')]
nav=''.join(f'<a href="../{slug}/"><span>{num}</span>{title}</a>' for slug,num,title in old_lectures)
html=f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="{content.SUBTITLE}"><title>{content.TITLE} · 并行计算与算子编程</title>
<link rel="icon" href="../../favicon.svg"><link rel="stylesheet" href="../../materials/lectures/3dgs/viewer.css">
<script type="module" src="../../materials/lectures/3dgs/viewer.mjs"></script></head>
<body class="hide-deep"><a class="skip" href="#main-content">跳转到正文</a>
<header class="site-header"><a class="brand" href="../../"><span class="brand-mark">▦</span><span>并行计算与算子编程<small>PARALLEL COMPUTING &amp; OPERATOR PROGRAMMING</small></span></a><nav><a href="../../">课程讲义</a><a href="../../glossary/">术语索引</a><span class="institution">人工智能学院</span></nav></header>
<aside class="course-sidebar" id="course-menu" aria-label="课程目录"><div class="sidebar-title">课程讲义 <span>已公开 6 讲</span></div><a href="../../">课程概览</a><a href="../../glossary/">术语索引</a><div class="nav-label">已公开讲义</div>{nav}<div class="nav-label">算子案例 · 本地草稿</div><a class="active" href="./" aria-current="page"><span>GS</span>3D Gaussian Splatting</a><p class="sidebar-note">从表示到算法<br>从数据到并行执行</p></aside>
<div class="workspace"><div class="toolbar"><div class="location"><button id="menu" aria-expanded="false" aria-controls="course-menu" aria-label="切换课程目录">☰</button><span>CASE STUDY <b>3DGS</b></span></div><div class="tools"><button id="depth" aria-pressed="false">展开深入阅读 8 页</button><a id="export" href="?mode=print" target="_blank" rel="noopener">导出 / 打印</a><div class="mode-switch" role="group" aria-label="讲义显示模式"><button id="read" aria-pressed="true">阅读</button><button id="present" aria-pressed="false">演示</button></div></div></div>
<div class="print-tools"><strong>本讲打印预览</strong><label><input id="print-answers" type="checkbox">包含参考答案</label><button id="print-now">打印 / 保存为 PDF</button><a href="./">返回阅读</a></div>
<div class="reading-layout"><main id="main-content"><header class="lecture-title"><div class="eyebrow">算子案例 <span>本地草稿</span></div><h1>{content.TITLE}</h1><p>{content.SUBTITLE}</p><div class="metadata">2026-11-04 <span>·</span> 49 页主线 <span>·</span> 8 页深入阅读 <span>·</span> 约 135 分钟</div></header>
<section class="learning-overview"><h2>学完这一讲，你能</h2><ul><li>从高斯参数解释屏幕足迹与前后遮挡</li><li>用计数、Scan 与排序组织 Tile 候选</li><li>追踪 Block 内的装入、同步、合成与结束</li><li>从引用数、像素工作量与质量解释性能取舍</li></ul></section>
<nav class="topic-overview" aria-label="本讲主题">{''.join(topic_links)}</nav>
<noscript><p class="takeaway">当前为静态阅读。启用 JavaScript 后可使用演示、交互图示和深入阅读切换。</p><style>.hide-deep .deep{{display:block!important}}</style></noscript>
<div id="slides">{''.join(slides)}</div>
<footer class="chapter-footer">课程原创讲解与图示 · 3DGS 方法：Kerbl 等（2023）<br><a href="https://arxiv.org/html/2308.04079v1">原论文</a> · <a href="../../">返回课程概览</a></footer></main>
<aside class="contents" aria-label="本讲内容">{page_nav('desktop')}</aside></div></div>
<button id="contents-open" class="mobile-contents-button" aria-haspopup="dialog" aria-controls="contents-dialog">▦ 本讲内容</button>
<dialog id="contents-dialog" aria-label="本讲内容"><div class="contents-dialog-header"><span>逐页浏览讲义</span><button id="contents-close" aria-label="关闭本讲内容">关闭 ×</button></div>{page_nav('mobile')}</dialog>
<nav class="presentation-controls" aria-label="翻页控制"><button id="prev" aria-label="上一页">← 上一页</button><label>跳至 <select id="page-select" aria-label="选择讲义页"></select></label><output id="progress" aria-live="polite">1 / 49</output><button id="next">下一步 →</button><button id="fullscreen" aria-label="切换全屏">全屏</button></nav>
<div id="status" class="sr-only" aria-live="polite"></div></body></html>'''
(DEST/'index.html').write_text(html,encoding='utf-8')
(ASSETS/'chapter.json').write_text(json.dumps({'title':content.TITLE,'topics':content.TOPICS,'slides':content.SLIDES,'sources':content.SOURCES},ensure_ascii=False,indent=2),encoding='utf-8')

# Additive preview navigation. Do not rewrite the compiled React bundle or claim
# the draft is published. The original generator can later import content.py/JSON.
nav_script=SITE/'assets/3dgs-preview-nav.js'
nav_script.write_text('''(() => {
 const root = document.querySelector('meta[name="course-root"]')?.content || './';
 const href = root + 'lectures/3d-gaussian-splatting/';
 function attach() {
   const sidebar = document.querySelector('.course-nav');
   if (sidebar && !sidebar.querySelector('[data-gs-draft]')) {
     const a=document.createElement('a'); a.href=href; a.dataset.gsDraft='';
     a.className='lesson-link'; a.textContent='GS · 3D Gaussian Splatting（本地草稿）';
     a.style.cssText='margin-top:16px;padding:12px;color:#176653;border-top:1px solid #e2e9e4';
     sidebar.append(a);
   }
   const syllabus=document.querySelector('#syllabus');
   if(syllabus && !syllabus.querySelector('[data-gs-draft]')) {
     const a=document.createElement('a'); a.href=href; a.dataset.gsDraft='';
     a.textContent='本地草稿 · 3D Gaussian Splatting：从三维表示到 GPU 并行渲染 →';
     a.style.cssText='display:block;margin-top:24px;padding:20px;border:1px solid #bfd5c5;border-radius:8px;background:#f3f8f5;color:#176653';
     syllabus.append(a);
   }
 }
 new MutationObserver(attach).observe(document.body,{childList:true,subtree:true}); attach();
})();\n''',encoding='utf-8')
for page in SITE.rglob('*.html'):
    if page==DEST/'index.html':continue
    original=page.read_text(encoding='utf-8')
    if '3dgs-preview-nav.js' in original:continue
    import os
    relative=os.path.relpath(nav_script,page.parent)
    page.write_text(original.replace('</body>',f'<script defer src="{relative}"></script></body>'),encoding='utf-8')
print(f'Built {len(content.SLIDES)} pages (49 main + 8 deep), 3 exercises, {DEST}')
