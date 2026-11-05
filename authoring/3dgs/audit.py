"""Check generated lecture structure and local dependencies without a browser."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit,unquote
import re
import content

ROOT=Path(__file__).resolve().parents[2]
PAGE=ROOT/'site/lectures/3d-gaussian-splatting/index.html'
class Audit(HTMLParser):
    def __init__(self):
        super().__init__();self.ids=[];self.links=[];self.assets=[];self.main=0;self.deep=0;self.answers=0;self.demos=0
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.append(a['id'])
        if tag=='a':self.links.append(a.get('href',''))
        if tag in ('script','img'):self.assets.append(a.get('src',''))
        if tag=='link':self.assets.append(a.get('href',''))
        if 'lecture-slide' in a.get('class','').split():
            if 'deep' in a.get('class','').split():self.deep+=1
            else:self.main+=1
        if 'answer' in a.get('class','').split():self.answers+=1
        if 'data-demo' in a:self.demos+=1

a=Audit();a.feed(PAGE.read_text(encoding='utf-8'))
assert len(a.ids)==len(set(a.ids)), 'Duplicate IDs'
assert (a.main,a.deep,a.answers,a.demos)==(49,8,3,3)
for href in a.links+a.assets:
    u=urlsplit(href)
    if u.scheme or u.netloc:continue
    if not u.path and u.fragment:
        assert unquote(u.fragment) in a.ids, href
    elif u.path:
        p=(PAGE.parent/unquote(u.path)).resolve()
        assert p.exists(), str(p)
        if p.is_dir():assert (p/'index.html').exists(), str(p)
for s in content.SLIDES:
    assert len(re.sub('<[^>]+>','',s['html']))>80,s['id']
    assert all(k in content.SOURCES for k in s['refs'])
assert not re.search(r'TODO|PLACEHOLDER|待补充',PAGE.read_text(encoding='utf-8'))
print('PASS: 49 main pages, 8 deep pages, 3 answers, 3 demos, unique anchors, and all local dependencies.')
