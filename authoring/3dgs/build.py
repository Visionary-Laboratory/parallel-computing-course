#!/usr/bin/env python3
"""Build an additive, local-only chapter without modifying the compiled course app."""
import json
import shutil
from html import escape, unescape
import re
from pathlib import Path
import content
import figures
import visual_io

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
SITE=ROOT/'site'
DEST=SITE/'lectures/3d-gaussian-splatting'
ASSETS=SITE/'materials/lectures/3dgs'
DEST.mkdir(parents=True,exist_ok=True)
ASSETS.mkdir(parents=True,exist_ok=True)
figures.build(ASSETS)
for name in ['viewer.css','viewer.mjs','model.mjs','visual_io.mjs']:
    shutil.copyfile(HERE/name,ASSETS/name)
(ASSETS/'media').mkdir(exist_ok=True)
for media in (HERE/'media').iterdir():
    if media.is_file():shutil.copyfile(media,ASSETS/'media'/media.name)
visual_io.build_static(ASSETS/'media')

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

def icon(name):
    paths={'grid':'<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 10h18M10 3v18"/>',
           'book':'<path d="M12 5c-3-2-7-2-10-1v15c3-1 7-1 10 1 3-2 7-2 10-1V4c-3-1-7-1-10 1v15"/>',
           'screen':'<rect x="3" y="3" width="18" height="14" rx="2"/><path d="M8 21h8m-4-4v4m-2-14 5 3-5 3Z"/>',
           'print':'<path d="M6 9V3h12v6M6 17H3V9h18v8h-3M6 14h12v7H6Z"/>',
           'full':'<path d="M8 3H3v5m13-5h5v5M3 16v5h5m13-5v5h-5"/>'}
    return f'<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{paths[name]}</svg>'

slides=[];main_no=0;deep_no=0;last_topic=None
for s in content.SLIDES:
    if s['deep']:deep_no+=1; label=f'深入 {deep_no:02d}'
    else:main_no+=1;label=f'{main_no:02d}'
    topic=dict(content.TOPICS)[s['topic']]
    if s['topic']!=last_topic:
        slides.append(f'<h2 class="topic-heading">{topic}</h2>')
        last_topic=s['topic']
    slides.append(f'''<section class="lecture-slide{' deep' if s['deep'] else ''}" id="{s['id']}" data-topic="{s['topic']}" data-label="{label}" tabindex="-1">
      <div class="slide-label"><a href="#{s['id']}" title="此主题的稳定链接"><span class="page-number">{label}</span> · 主题链接</a><button class="start-page" data-start="{s['id']}" aria-label="从{label}页开始浏览">{icon('screen')} 从此页开始</button></div>
      <div class="slide-topline"><span>并行计算与算子编程</span><span>{topic}</span></div>
      <div class="print-page-label">{content.SLIDES.index(s)+1:02d} / 57 · {topic}{' · 深入阅读' if s['deep'] else ''}</div>
      <div class="slide-body"><h2>{s['title']}</h2>{s['html']}{refs(s['refs'])}</div>
      <div class="slide-bottomline"><span>人工智能学院</span><span class="slide-page-count"></span></div>
    </section>''')

topic_links=[]
for key,title in content.TOPICS:
    first=next(s for s in content.SLIDES if s['topic']==key)
    topic_links.append(f'<a href="#{first["id"]}" data-target="{first["id"]}">{title}</a>')

old_lectures=[('01-introduction','01','并行基础与性能模型'),('02-execution-models','02','并行硬件与执行模型'),('03-parallel-design','03','并行程序设计思想'),('04-memory-synchronization','04','缓存一致性与同步实现'),('05-cuda-introduction','05','CUDA 编程入门'),('06-memory-hierarchy','06','CUDA 内存层次')]
nav=''
for slug,num,title in old_lectures:
    if num=='01':nav+='<div class="nav-label">第一部分 <b>理解并行计算</b></div>'
    if num=='05':nav+='<div class="nav-label">第二部分 <b>走进 CUDA 编程</b></div>'
    nav+=f'<a href="../{slug}/"><span>{num}</span>{title}<i>●</i></a>'
print_index='<nav class="print-index" aria-label="PDF 主题目录"><h2>本讲目录</h2><ol>'+''.join(f'<li><a href="#{s["id"]}">{escape(s["title"])}</a></li>' for s in content.SLIDES)+'</ol></nav>'
html=f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="{content.SUBTITLE}"><title>{content.TITLE} · 并行计算与算子编程</title>
<link rel="icon" href="../../favicon.svg"><link rel="stylesheet" href="../../materials/lectures/3dgs/viewer.css">
<script type="module" src="../../materials/lectures/3dgs/viewer.mjs"></script></head>
<body class="hide-deep"><a class="skip" href="#main-content">跳转到正文</a>
<header class="site-header"><a class="brand" href="../../"><span class="brand-mark">{icon('grid')}</span><span>并行计算与算子编程<small>PARALLEL COMPUTING &amp; OPERATOR PROGRAMMING</small></span></a><nav aria-label="网站导航"><a href="../../">课程讲义</a><a href="../../glossary/">术语索引</a><span class="institution">人工智能学院</span></nav></header>
<aside class="course-sidebar" id="course-menu" aria-label="课程目录"><div class="sidebar-title">课程讲义 <span>已公开 6 讲</span></div><a href="../../">{icon('book')} 课程概览</a><a href="../../glossary/">术语索引</a>{nav}<a class="resources-link" href="../../#resources">参考资料 ↗</a><div class="nav-label">算子案例 · 本地草稿</div><a class="active" href="./" aria-current="page"><span>GS</span>3D Gaussian Splatting</a><p class="sidebar-note">公开课程讲义 <span>第一至六讲</span></p></aside>
<div class="workspace"><div class="breadcrumb"><div><a href="../../">课程讲义</a><span>›</span><span>3D Gaussian Splatting</span></div><span>从阅读到课堂</span></div><div class="toolbar"><div class="location"><button id="menu" aria-expanded="false" aria-controls="course-menu" aria-label="切换课程目录">☰</button><span>CASE STUDY 3DGS</span><span>算子案例</span></div><div class="tools"><a id="export" href="?mode=print" target="_blank" rel="noopener">{icon('print')} 导出本讲 PDF</a><button id="depth" aria-pressed="false">主线 · 展开深入阅读 8 页</button><div class="mode-switch" role="tablist" aria-label="讲义显示模式"><button id="read" role="tab" aria-selected="true" aria-controls="lecture-panel">{icon('book')} 阅读</button><button id="present" role="tab" aria-selected="false" aria-controls="lecture-panel" tabindex="-1">{icon('screen')} 演示</button></div><button id="fullscreen" aria-label="全屏演示" title="全屏演示（F）">{icon('full')}</button></div></div>
<div class="print-tools"><a href="./">← 返回本讲</a><div><label><input id="print-answers" type="checkbox">包含参考答案</label><button id="print-now" disabled>正在准备图文…</button></div><p>导出本讲全部 57 个主题。选择“另存为 PDF”，建议 A4 纸张、关闭页眉和页脚；交互示例保留静态图文。</p><p id="print-status" role="status"></p></div>
<div id="lecture-panel" role="tabpanel" aria-labelledby="read"><div class="reading-layout"><main id="main-content"><header class="lecture-title"><div class="eyebrow">算子案例 <span>本地草稿</span></div><h1>{content.TITLE}</h1><p>{content.SUBTITLE}</p><div class="metadata">2026-11-08<br><span id="reading-count">49 页</span> · <button id="browse">逐页浏览 →</button><span class="duration"> · 约 135 分钟</span></div></header>
<section class="learning-overview"><h2>学完这一讲，你能</h2><ul><li>从高斯参数解释屏幕足迹与前后遮挡</li><li>用计数、Scan 与排序组织 Tile 候选</li><li>追踪 Block 内的装入、同步、合成与结束</li><li>从高斯覆盖的 Tile 数、像素实际处理的候选数量与图像质量，解释性能取舍</li></ul></section>
<nav class="topic-overview" aria-label="本讲主题">{''.join(topic_links)}</nav>
<noscript><p class="takeaway">当前为静态阅读。启用 JavaScript 后可使用演示、交互图示和深入阅读切换。</p><style>.hide-deep .deep{{display:block!important}}</style></noscript>
{print_index}<div id="slides">{''.join(slides)}</div>
<footer class="chapter-footer"><a href="../../">← 返回课程概览</a><p>并行计算与算子编程 <a href="../../glossary/">术语索引 ↗</a></p>课程原创讲解与图示 · 3DGS 方法：Kerbl 等（2023） · <a href="https://arxiv.org/html/2308.04079v1">原论文</a></footer></main>
<aside class="contents" aria-label="本讲内容">{page_nav('desktop')}</aside></div>
<div class="presentation-footer"><progress id="slide-progress" aria-label="本讲浏览进度" value="1" max="49"></progress><div class="presentation-controls"><button id="presentation-contents" aria-label="打开页面目录" aria-haspopup="dialog">{icon('grid')}</button><span class="keyboard-hint">← → 答案 / 翻页 · F 全屏</span><nav aria-label="演示翻页"><button id="prev" aria-label="上一页">←</button><button id="page-picker" aria-label="选择页码" aria-haspopup="dialog"><output id="progress">1 / 49</output></button><button id="next" aria-label="下一页">→</button></nav></div><p id="slide-status" role="status"></p></div></div></div>
<button id="contents-open" class="mobile-contents-button" aria-haspopup="dialog" aria-controls="contents-dialog">▦ 本讲内容</button>
<dialog id="contents-dialog" aria-label="本讲页面"><div class="contents-dialog-header"><h2>本讲页面</h2><button id="contents-close" aria-label="关闭本讲内容">关闭 ×</button></div><p class="dialog-description">按页查看标题与核心思想，当前页自动展开。</p>{page_nav('mobile')}</dialog>
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
