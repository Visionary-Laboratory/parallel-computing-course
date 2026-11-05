#!/usr/bin/env python3
"""Serve the complete course locally. Binds only to loopback; never deploys."""
import argparse
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
        super().end_headers()
    def guess_type(self,path):
        if path.endswith('.mjs'): return 'text/javascript'
        return super().guess_type(path)
try:
    server=ThreadingHTTPServer(('127.0.0.1',args.port),partial(Handler,directory=str(site)))
    print(f'Course: http://127.0.0.1:{args.port}/',flush=True)
    print(f'3DGS:   http://127.0.0.1:{args.port}/lectures/3d-gaussian-splatting/',flush=True)
    print('Local preview only. Ctrl+C to stop.',flush=True)
    server.serve_forever()
except KeyboardInterrupt:
    pass
