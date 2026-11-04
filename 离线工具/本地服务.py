# -*- coding: utf-8 -*-
"""
活动代币计算器 · 本地服务

双击「启动计算器.bat」后：
  1. 在 127.0.0.1 上提供计算器页面
  2. 自动打开浏览器
  3. 页面里点「同步最新数据」时，由本程序去 PRTS wiki 抓最新数据

浏览器自己抓不了 wiki（对方没开跨域许可），所以抓取必须由本地进程完成。
"""

import ctypes
import datetime
import importlib.util
import json
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.parse
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

APP_DIR = os.path.dirname(os.path.abspath(__file__))


def _find_root():
    """本脚本可能被放在「离线工具」子目录里，页面和数据在上一层。"""
    for d in (APP_DIR, os.path.dirname(APP_DIR)):
        if os.path.exists(os.path.join(d, 'index.html')):
            return d
    return APP_DIR


ROOT = _find_root()

DATA_JSON = os.path.join(ROOT, '活动数据.json')
DATA_JS = os.path.join(ROOT, '活动数据.js')

DEFAULT_ACTIVITY = '时间啊，向前！'
PORT_CANDIDATES = [8765, 8766, 8767, 8768, 8769, 8770]

_fetch_module = None


def fetch_module():
    """按文件路径加载抓取脚本，避免依赖模块名（它是中文名）。"""
    global _fetch_module
    if _fetch_module is not None:
        return _fetch_module
    path = os.path.join(ROOT, '工具', '更新活动数据.py')
    if not os.path.exists(path):
        path = os.path.join(ROOT, '更新活动数据.py')
    spec = importlib.util.spec_from_file_location('arkfetch', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _fetch_module = mod
    return mod


def load_initial_data():
    for p in (DATA_JSON, DATA_JS):
        if os.path.exists(p):
            try:
                if p.endswith('.js'):
                    with open(p, encoding='utf-8') as f:
                        txt = f.read()
                    i = txt.find('{')
                    return json.loads(txt[i:txt.rfind('}') + 1])
                with open(p, encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                continue
    return None


def write_data_js(data):
    with open(DATA_JS, 'w', encoding='utf-8') as f:
        f.write('window.__ACTIVITY_DATA__ = ')
        json.dump(data, f, ensure_ascii=False)
        f.write(';\n')


def free_port():
    for p in PORT_CANDIDATES:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(('127.0.0.1', p))
                return p
            except OSError:
                continue
    return PORT_CANDIDATES[0]


class Handler(SimpleHTTPRequestHandler):
    server_version = 'ArkEventCalc/1.1'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def log_message(self, fmt, *args):
        pass

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Cache-Control', 'no-store')

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_POST(self):
        if self.path.startswith('/api/update'):
            self.handle_update()
        else:
            self.send_error(404)

    def do_GET(self):
        if self.path.startswith('/api/update'):
            self.handle_update()
        elif self.path in ('/', '/index.html'):
            self.serve_file(os.path.join(ROOT, 'index.html'), 'text/html; charset=utf-8')
        elif self.path.split('?')[0] in ('/活动数据.js', '/%E6%B4%BB%E5%8A%A8%E6%95%B0%E6%8D%AE.js'):
            # 优先给用户目录里最新的那份
            p = DATA_JS
            self.serve_file(p, 'application/javascript; charset=utf-8')
        else:
            super().do_GET()

    def serve_file(self, path, ctype):
        if not os.path.exists(path):
            self.send_error(404)
            return
        with open(path, 'rb') as f:
            body = f.read()
        self.send_response(200)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def handle_update(self):
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        name = (qs.get('name') or [DEFAULT_ACTIVITY])[0] or DEFAULT_ACTIVITY
        t0 = time.time()
        try:
            data = fetch_module().build(name)
            data['built'] = time.strftime('%Y-%m-%d %H:%M')
            with open(DATA_JSON, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=1)
            write_data_js(data)
            payload = {'ok': True, 'data': data, 'seconds': round(time.time() - t0, 1)}
        except Exception as e:
            payload = {'ok': False, 'error': str(e)[:600]}
        body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)


BROWSER_CANDIDATES = [
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
    os.path.join(os.environ.get('LOCALAPPDATA', ''), r'Google\Chrome\Application\chrome.exe'),
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
]


def open_browser(url):
    """先直接拉起已知浏览器，再退回系统关联。返回是否成功。"""
    for exe in BROWSER_CANDIDATES:
        if exe and os.path.exists(exe):
            try:
                subprocess.Popen([exe, url], close_fds=True,
                                 creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000))
                log('browser via ' + exe)
                return True
            except Exception as e:
                log('browser exe failed %r' % (e,))
    if os.name == 'nt':
        try:
            os.startfile(url)
            log('browser via startfile')
            return True
        except Exception:
            pass
        try:
            subprocess.Popen(['cmd', '/c', 'start', '', url],
                             creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000))
            log('browser via cmd start')
            return True
        except Exception:
            pass
    try:
        webbrowser.open(url)
        return True
    except Exception:
        return False


LOG = os.path.join(APP_DIR, '_启动日志.txt')


def log(msg):
    try:
        with open(LOG, 'a', encoding='utf-8') as f:
            f.write('[%s] %s\n' % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), msg))
    except Exception:
        pass


def msgbox(text, title='活动代币计算器'):
    try:
        ctypes.windll.user32.MessageBoxW(None, str(text), title, 0x10)
    except Exception:
        pass


def main():
    log('== start app_dir=%s cwd=%s argv=%s' % (APP_DIR, os.getcwd(), sys.argv))
    port = free_port()
    httpd = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    url = 'http://127.0.0.1:%d/' % port
    log('listen on %d' % port)
    print('=' * 46)
    print(' 活动代币计算器已启动')
    print(' 页面地址：' + url)
    print(' 浏览器没自动打开的话，把这行地址复制进去。')
    print(' 关掉这个窗口 = 停止服务。')
    print('=' * 46)
    sys.stdout.flush()
    if not os.environ.get('ARK_NO_BROWSER'):
        def _open():
            ok = False
            try:
                ok = open_browser(url)
            except Exception as e:
                log('open_browser raised %r' % (e,))
            if not ok:
                log('open_browser failed, keep window')
                msgbox('浏览器没能自动打开。\n\n请复制下面这个地址到浏览器：\n' + url)
        threading.Timer(1.2, _open).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == '__main__':
    try:
        main()
    except Exception:
        import traceback
        tb = traceback.format_exc()
        log('FATAL\n' + tb)
        msgbox('启动失败：\n\n' + tb[-700:])
        raise
