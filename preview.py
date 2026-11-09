#!/usr/bin/env python3
"""Serve the complete course locally. Binds only to loopback; never deploys."""
import argparse
import re
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--port',type=int,default=4173)
args=parser.parse_args()
site=Path(__file__).resolve().parent/'site'
class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control','no-store')
        if self.path.split('?',1)[0].endswith('.mp4'):
            self.send_header('Accept-Ranges','bytes')
        super().end_headers()
    def guess_type(self,path):
        if path.endswith('.mjs'): return 'text/javascript'
        return super().guess_type(path)
    def send_head(self):
        self._byte_range=None
        path=Path(self.translate_path(self.path))
        request=self.headers.get('Range','')
        match=re.fullmatch(r'bytes=(\d*)-(\d*)',request)
        if path.suffix!='.mp4' or not path.is_file() or not match:
            return super().send_head()
        size=path.stat().st_size
        first,last=match.groups()
        if first:
            start=int(first);end=min(int(last),size-1) if last else size-1
        else:
            length=int(last or '0');start=max(0,size-length);end=size-1
        if size==0 or start>=size or end<start:
            self.send_response(416)
            self.send_header('Content-Range','bytes */{}'.format(size))
            self.send_header('Content-Length','0')
            self.end_headers()
            return None
        stream=path.open('rb');stream.seek(start)
        self.send_response(206)
        self.send_header('Content-Type',self.guess_type(str(path)))
        self.send_header('Content-Range','bytes {}-{}/{}'.format(start,end,size))
        self.send_header('Content-Length',str(end-start+1))
        self.end_headers()
        self._byte_range=end-start+1
        return stream
    def copyfile(self,source,outputfile):
        if self._byte_range is None:
            return super().copyfile(source,outputfile)
        remaining=self._byte_range
        while remaining:
            chunk=source.read(min(64*1024,remaining))
            if not chunk:break
            outputfile.write(chunk);remaining-=len(chunk)
try:
    server=ThreadingHTTPServer(('127.0.0.1',args.port),partial(Handler,directory=str(site)))
    print(f'Course: http://127.0.0.1:{args.port}/',flush=True)
    print(f'3DGS:   http://127.0.0.1:{args.port}/lectures/3d-gaussian-splatting/',flush=True)
    print('Local preview only. Ctrl+C to stop.',flush=True)
    server.serve_forever()
except KeyboardInterrupt:
    pass
