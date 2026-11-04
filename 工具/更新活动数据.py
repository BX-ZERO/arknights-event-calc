# -*- coding: utf-8 -*-
"""明日方舟活动代币数据抓取 + 页面生成（通用版）。

用法：
    更新活动数据.py "活动名"
不带参数时交互输入。抓取 PRTS wiki 的活动页，生成同目录的
「index.html」以及数据快照「活动数据.json」。
"""
import urllib.request, urllib.parse, json, re, sys, io, time, os, base64
import html as _html_lib

_HERE = os.path.dirname(os.path.abspath(__file__))
# 三个脚本平时放在「工具」子目录里，工作目录要提到上一级（页面、数据都那儿）
BASE = os.path.dirname(_HERE) if os.path.basename(_HERE) == '工具' else _HERE
# 控制台编码跟着环境走：bat 里设了 gbk，直接在 Git Bash / IDE 里跑则用 utf-8
_enc = (os.environ.get('PYTHONIOENCODING') or '').split(':')[0].strip()
if not _enc:
    _enc = 'gbk' if os.name == 'nt' else 'utf-8'
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=_enc, errors='replace')
except Exception:
    pass

UA = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Referer': 'https://prts.wiki/',
}
API = 'https://prts.wiki/api.php'

# ---------------- 控制台显示 ----------------
IS_TTY = sys.stdout.isatty()
COLOR = IS_TTY and not os.environ.get('NO_COLOR')


def _c(t, code):
    return ('\033[%sm%s\033[0m' % (code, t)) if COLOR else t


def green(t):
    return _c(t, '32')


def yellow(t):
    return _c(t, '33')


def red(t):
    return _c(t, '31')


def dim(t):
    return _c(t, '2')


def bold(t):
    return _c(t, '1')


def _out(s=''):
    sys.stdout.write(s + '\n')
    sys.stdout.flush()


def rule(ch='─', n=56):
    _out(dim(ch * n))


def title(text):
    _out()
    rule('═')
    _out(bold('  ' + text))
    rule('═')


def step(no, total, label, extra='', ok=True):
    tag = green('√') if ok else red('×')
    _out('  %s [%d/%d] %-18s %s' % (tag, no, total, label, extra))


def pbar(done, total, label='', width=18):
    """只在真控制台里画，重定向到文件时什么都不做。"""
    if not IS_TTY or total <= 0:
        return
    k = int(round(width * done / float(total)))
    bar = '█' * k + '·' * (width - k)
    pct = int(100 * done / float(total))
    sys.stdout.write('\r  %s %s %3d%%  %d/%d   ' % (label, bar, pct, done, total))
    sys.stdout.flush()
    if done >= total:
        sys.stdout.write('\n')
        sys.stdout.flush()



VERBOSE = bool(os.environ.get('ARK_VERBOSE'))


def say(*a):
    """技术细节，设 ARK_VERBOSE=1 才显示。"""
    if VERBOSE:
        print(*a)


def note(msg):
    """过程中给用户的提示（不参与结果汇总）。"""
    _out('  ' + dim('· ' + msg))


def ok(msg):
    _out('  %s %s' % (green('√'), msg))

def api(**params):
    params.setdefault('format', 'json')
    url = API + '?' + urllib.parse.urlencode(params)
    last = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.loads(r.read().decode('utf-8'))
        except Exception as e:
            last = e
            time.sleep(2 + attempt * 3)
    raise last


def strip_templates(s, rounds=8):
    out = s
    for _ in range(rounds):
        new = re.sub(r'\{\{[^{}]*\}\}', '', out)
        if new == out:
            break
        out = new
    return out


def clean_text(s):
    s = strip_templates(s)
    s = s.replace("'''", '').replace('<small>', '').replace('</small>', '')
    s = re.sub(r'<[^>]+>', '', s)
    return re.sub(r'\s+', ' ', s).strip()


def page_exists(title):
    try:
        d = api(action='parse', page=title, prop='sections')
        return 'parse' in d
    except Exception:
        return False


def resolve_page(raw):
    cands = [raw.strip()]
    m = re.search(r'[「『](.+?)[」』]', raw)
    if m:
        cands.append(m.group(1).strip())
    cands.append(re.sub(r'^(SideStory|故事集|危机合约|联锁竞赛|多维合作)\s*', '', raw).strip())
    for c in cands:
        if c and page_exists(c):
            return c
    raise SystemExit('找不到页面：' + raw)


def fetch(page):
    secs = api(action='parse', page=page, prop='sections')['parse']['sections']
    s0 = api(action='parse', page=page, prop='wikitext', section=0)['parse']['wikitext']['*']
    texts = {}
    for s in secs:
        if not s.get('index'):
            continue
        name = clean_text(s['line'])
        try:
            texts[name] = api(action='parse', page=page, prop='wikitext',
                              section=s['index'])['parse']['wikitext']['*']
            time.sleep(0.3)
        except Exception as e:
            print('  [warn] 读取章节失败:', name, e)
    return s0, texts


def field(s0, key):
    m = re.search(r'\|' + key + r'=([^\n|}]*)', s0)
    return m.group(1).strip() if m else ''


def parse_shop(wt):
    m = re.search(r'\|data=\s*\n(.*?)\}\}\s*$', wt, re.S)
    body = m.group(1) if m else ''
    token_alias = ''
    mt = re.search(r'\|token_alias=([^\n|}]*)', wt)
    if mt:
        token_alias = mt.group(1).replace('带框_', '').strip()
    items, group = [], ''
    for raw in body.split('\n'):
        raw = raw.strip()
        if not raw:
            continue
        parts = raw.split(';;')
        if parts[0] == 'X':
            g = clean_text(parts[1])
            group = g if g else group
            continue
        if len(parts) < 5:
            continue
        typ, content, qty, price, quality = parts[0], parts[1], parts[2], parts[3], parts[4]
        name = clean_text(content)
        if not name:
            continue
        try:
            price_i = int(re.sub(r'[^\d]', '', price) or 0)
        except Exception:
            price_i = 0
        if qty.strip() == '∞':
            qty_i = -1
        else:
            try:
                qty_i = int(re.sub(r'[^\d]', '', qty) or 0)
            except Exception:
                qty_i = 0
        items.append({
            'group': group, 'name': name, 'qty': qty_i,
            'price': price_i, 'quality': quality.strip(), 'special': typ == '1',
        })
    return items, token_alias


def tab_sections(body):
    """tabber 里每一页：[(页签名, 内容)]。只有一个页签时返回 [('', 全部)]。"""
    parts = re.split(r'\n\s*([^\n=|{}]+?)\s*=\s*\n', '\n' + body)
    if len(parts) > 1:
        return [(parts[i].strip(), parts[i + 1]) for i in range(1, len(parts) - 1, 2)]
    return [('', body)]


def parse_stages(wt, token):
    head, _, _ = wt.partition('{{活动信赖获取提升干员')
    m = re.search(r'<tabber>(.*?)</tabber>', head, re.S)
    body = m.group(1) if m else head
    out = []
    t = re.escape(token)
    for pname, ptab in tab_sections(body):
        for m2 in re.finditer(r'\{\{关卡链接\|([^}]+)\}\}(.*?)(?=\{\{关卡链接\||\Z)', ptab, re.S):
            code = m2.group(1).strip()
            seg = m2.group(2)
            sanity = re.search(r'\{\{道具图标\|理智\|(\d+)', seg)
            if not sanity:
                continue
            tk = re.search(r'\{\{关卡报酬\|' + t + r'\|\|60px\|n=(\d+)\}\}', seg)
            first = re.search(r'\{\{关卡报酬\|' + t + r'\|三星获得\|60px\|n=(\d+)\}\}', seg)
            if not tk and not first:
                continue
            out.append({
                'code': code,
                'sanity': int(sanity.group(1)),
                'token': int(tk.group(1)) if tk else 0,
                'first': int(first.group(1)) if first else 0,
                'regular': bool(tk),
                'phase': pname,
            })
    return out


def parse_milestones(texts, token):
    t = re.escape(token)
    best, total, best_name = [], 0, ''
    for name, wt in texts.items():
        if 'EventShopList' in wt or '关卡信息' in name:
            continue
        rows = re.split(r'\n\|-\n', wt)
        cur = []
        for r in rows:
            cells = [c.strip() for c in r.split('\n') if c.strip().startswith('|')]
            if len(cells) < 2:
                continue
            cond = clean_text(cells[0].lstrip('|'))
            if not cond or cond.startswith('!'):
                continue
            tk = re.search(r'\{\{道具图标\|' + t + r'\|(\d+)\|50px', cells[1])
            if not tk:
                continue
            cur.append({'cond': cond, 'token': int(tk.group(1))})
        s = sum(x['token'] for x in cur)
        if s > total:
            best, total, best_name = cur, s, name
    return best, total, best_name


def parse_phases(page, sec_idx):
    """关卡信息里的 tabber 就是游戏内的阶段按钮，返回 [(阶段名, [关卡代号])]。"""
    try:
        wt = api(action='parse', page=page, prop='wikitext', section=sec_idx)['parse']['wikitext']['*']
    except Exception:
        return []
    m = re.search(r'<tabber>(.*?)</tabber>', wt, re.S)
    body = m.group(1) if m else wt
    out = []
    for name, ptab in tab_sections(body):
        if not name or name in ('-', '|'):
            continue
        codes = re.findall(r'\{\{关卡链接\|([^}|]+)', ptab)
        out.append((name, codes))
    return out


def base_name(name):
    """从「阶段商品1：国度的信物」「龙门币×5000」这类显示名里取出道具本名。"""
    n = re.sub(r'^阶段商品\s*\d+\s*[：:]\s*', '', str(name))
    n = re.sub(r'\s*[×xX]\s*\d+\s*$', '', n)
    return n.strip()


def get_bytes(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def _norm(t):
    return re.sub(r'^(文件|File|檔案|档案)\s*:', '', t).replace('_', ' ').strip()


def _tight_box(im):
    """家具图是灰白底、alpha 全满，只能按颜色找主体范围。"""
    rgb = im.convert('RGB')
    w, h = rgb.size
    px = rgb.load()
    minx, miny, maxx, maxy = w, h, -1, -1
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            mx, mn = max(r, g, b), min(r, g, b)
            if mx - mn <= 14 and mx >= 140:      # 灰白背景
                continue
            if x < minx: minx = x
            if y < miny: miny = y
            if x > maxx: maxx = x
            if y > maxy: maxy = y
    if maxx <= minx or maxy <= miny:
        return None
    return (minx, miny, maxx + 1, maxy + 1)


def theme_color(url):
    """从横幅里挑一个能当主题色的颜色：够鲜艳、但压暗到白字读得清。"""
    try:
        import colorsys
        from PIL import Image
        import io as _io
        raw = get_bytes(url)
        im = Image.open(_io.BytesIO(raw)).convert('RGB')
        im.thumbnail((96, 96))

        buckets = {}
        px = im.tobytes()                    # RGB 连续排布，避开 getdata 的弃用警告
        for i in range(0, len(px) - 2, 3):
            r, g, b = px[i], px[i + 1], px[i + 2]
            mx, mn = max(r, g, b), min(r, g, b)
            if mx < 45 or mx > 235:      # 太黑 / 太白
                continue
            if mx - mn < 34:             # 太灰
                continue
            k = (r // 20, g // 20, b // 20)
            buckets[k] = buckets.get(k, 0) + 1
        if not buckets:
            return ''

        # 取占比最高的三个候选，选其中饱和度高、明度居中的
        top = sorted(buckets.items(), key=lambda x: -x[1])[:3]
        best, best_score = None, -1
        for (r20, g20, b20), cnt in top:
            r, g, b = r20 * 20 + 10, g20 * 20 + 10, b20 * 20 + 10
            h, l, sa = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
            score = sa * 2 - abs(l - 0.45)
            if score > best_score:
                best_score, best = score, (h, l, sa)
        if not best:
            return ''
        # 保留横幅本身的色相与饱和度，只把明度压到白字读得清为止。
        # 这样红横幅出深红、金横幅出深棕金，跟 wiki 那种横条一个观感，
        # 而不是所有活动都被拉成同一个亮度。
        h, l0, sa = best
        sa = max(0.58, min(1.0, sa * 1.25))
        def lum(c):
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
        r = g = b = 0
        for _ in range(40):
            r, g, b = colorsys.hls_to_rgb(h, l0, sa)
            lb = 0.2126 * lum(r) + 0.7152 * lum(g) + 0.0722 * lum(b)
            if (1.05) / (lb + 0.05) >= 4.8:   # 白字对比够读就停
                break
            l0 -= 0.012
            if l0 <= 0.14:
                break
        return '#%02x%02x%02x' % (int(r * 255), int(g * 255), int(b * 255))
    except Exception as e:
        say('主题色提取失败:', e)
        return ''


def to_data_url(url):
    """下载图片，裁掉空白后转成 56px WebP 的 base64 data URL。"""
    blob = get_bytes(url)
    mime = 'png'
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(blob)).convert('RGBA')
        b = im.getbbox()
        if b and b != (0, 0, im.width, im.height):
            im = im.crop(b)                       # 透明底道具：紧贴内容裁即可
        else:
            b = _tight_box(im)                    # 灰白底家具：保留一圈背景再放大
            if b:
                cx = (b[0] + b[2]) / 2.0
                cy = (b[1] + b[3]) / 2.0
                side = max(b[2] - b[0], b[3] - b[1]) * 1.15
                side = min(side, im.width, im.height)
                box = (int(cx - side / 2), int(cy - side / 2),
                       int(cx + side / 2), int(cy + side / 2))
                box = (max(0, box[0]), max(0, box[1]),
                       min(im.width, box[2]), min(im.height, box[3]))
                im = im.crop(box)
        im.thumbnail((48, 48), Image.LANCZOS)
        canvas = Image.new('RGBA', (48, 48), (0, 0, 0, 0))
        canvas.paste(im, ((48 - im.width) // 2, (48 - im.height) // 2), im)
        buf = io.BytesIO()
        canvas.save(buf, 'WEBP', quality=82, method=6)
        blob = buf.getvalue()
        mime = 'webp'
    except Exception:
        pass
    return 'data:image/%s;base64,%s' % (mime, base64.b64encode(blob).decode())


def shop_icon_urls(page, shop_name):
    """从商店章节渲染后的 HTML 抓「商品显示名 → 图标 URL」，家具在这里也有占位图。"""
    try:
        secs = api(action='parse', page=page, prop='sections')['parse']['sections']
    except Exception as e:
        print('  [warn] 取章节失败:', e)
        return {}
    idx = None
    for s in secs:
        if clean_text(s.get('line', '')) == shop_name:
            idx = s['index']
            break
    if not idx:
        return {}
    try:
        h = api(action='parse', page=page, prop='text', section=idx)['parse']['text']['*']
    except Exception as e:
        print('  [warn] 取商店 HTML 失败:', e)
        return {}

    out = {}
    # 按表格行切，行内同时能看到商品名和图标；家具行里带的是 torappu 的家具素材地址
    for row in re.split(r'<tr\b', h):
        m = re.search(r'title="([^"]+)"', row)
        if not m:
            continue
        name = _html_lib.unescape(m.group(1))
        tor = re.findall(r'//torappu\.prts\.wiki/assets/furniture/[^"\'\s<>]+', row)
        if tor:
            out.setdefault(name, 'https:' + _html_lib.unescape(tor[0]))
            continue
        im = re.search(r'<img[^>]+src="([^"]+)"', row)
        if not im:
            continue
        url = _html_lib.unescape(im.group(1)).replace('&amp;', '&')
        if url.startswith('//'):
            url = 'https:' + url
        elif url.startswith('/'):
            url = 'https://prts.wiki' + url
        elif not url.startswith('http'):
            url = 'https://media.prts.wiki/' + url
        out.setdefault(name, url)
    say('商店 HTML 图标：', len(out))
    return out


def image_urls(names):
    """批量把图片名换成真实 URL。返回 {规范化名字: url}。"""
    urls = {}
    keys = list(names)
    for i in range(0, len(keys), 40):
        chunk = keys[i:i + 40]
        titles = '|'.join('File:' + c for c in chunk)
        for attempt in range(3):
            try:
                d = api(action='query', titles=titles, prop='imageinfo', iiprop='url')
                for pg in d.get('query', {}).get('pages', {}).values():
                    if 'imageinfo' in pg:
                        url = pg['imageinfo'][0]['url']
                        if url.startswith('//'):
                            url = 'https:' + url
                        urls[_norm(pg['title'])] = url
                break
            except Exception as e:
                print('  [warn] 取图片地址失败:', e)
                time.sleep(2)
        time.sleep(0.3)
    return urls


def image_sizes(names):
    """批量取图片宽高，用来分辨横幅与图标。"""
    out = {}
    for i in range(0, len(names), 40):
        chunk = names[i:i + 40]
        try:
            d = api(action='query',
                    titles='|'.join('File:' + n for n in chunk),
                    prop='imageinfo', iiprop='size')
        except Exception:
            continue
        pages = (d or {}).get('query', {}).get('pages', {})
        for p in pages.values():
            if 'imageinfo' not in p:
                continue
            ii = p['imageinfo'][0]
            nm = p.get('title', '').replace('File:', '', 1)
            out[_norm(nm)] = (ii.get('width', 0), ii.get('height', 0))
    return out


def find_banner(imgs):
    """从页面图片列表里挑活动横幅。"""
    cands = [i for i in imgs if re.search(r'活动预告|活动图|宣传|banner|KV', i, re.I)]
    if cands:
        # 名字对得上就直接用，不折腾尺寸
        urls = image_urls(cands[:4])
        for c in cands[:4]:
            u = urls.get(_norm(c))
            if u:
                return u
        return ''
    if not cands:
        # 老活动没有「活动预告」这类图，退回按尺寸挑：只认够宽的，图标一律不要
        skip = ('图标', '头像', '道具', 'logo', '标志', '按钮', 'bg', '背景', '素材', '界面')
        cands = [i for i in imgs
                 if re.search(r'\.(jpg|jpeg|png)$', i, re.I)
                 and not any(k in i for k in skip)]
    if not cands:
        return ''
    sizes = image_sizes(cands[:24])
    big = sorted(cands[:24], key=lambda n: -sizes.get(n, (0, 0))[0])
    big = [n for n in big if sizes.get(n, (0, 0))[0] >= 600]
    if not big:
        return ''
    urls = image_urls(big[:4])
    for c in big[:4]:
        u = urls.get(_norm(c))
        if u:
            return u
    return ''


def furn_icon_url(name):
    """家具的真实缩略图不在 wiki 文件库，而在 torappu 子站的 assets/furniture 下。"""
    try:
        d = api(action='parse', page=name, prop='text')
    except Exception:
        return None
    if not isinstance(d, dict) or 'error' in d:
        return None
    body = d.get('parse', {}).get('text', {}).get('*', '')
    urls = [_html_lib.unescape(u) for u in
            re.findall(r'//torappu\.prts\.wiki/assets/furniture/[^"\'\s<>]+\.png', body)]
    return ('https:' + urls[0]) if urls else None


def fetch_icons(imgs, shop, html_urls=None):
    """按道具名匹配 wiki 图片，下载后转 base64 data URL。"""
    if not imgs and not html_urls:
        return {}
    names = set()
    for it in shop:
        n = base_name(it['name'])
        if n:
            names.add(n)

    picked = {}
    for n in names:
        cand = []
        if '专属时装' in n:
            op = n.split('专属时装')[0].strip()
            cand = [i for i in imgs if i.startswith('头像_' + op + '_skin')]
        if not cand:
            cand = [i for i in imgs if i.lower().endswith('.png')
                    and (re.sub(r'\.png$', '', i).endswith('_' + n) or re.sub(r'\.png$', '', i) == n)]
        if not cand:
            cand = [i for i in imgs if n in i and i.lower().endswith('.png')]
        if cand:
            # 带框版优先，观感更贴近游戏
            cand.sort(key=lambda x: 0 if '带框' in x else 1)
            picked[n] = cand[0]

    urls = image_urls(picked.values()) if picked else {}

    # 先把真正要下的清单列出来，进度条的分母才不会虚高
    jobs, seen = [], set()
    for n, t in picked.items():
        u = urls.get(_norm(t))
        if u:
            jobs.append((n, u))
            seen.add(n)
    if html_urls:
        for it in shop:
            n = base_name(it['name'])
            if not n or n in seen:
                continue
            u = html_urls.get(it['name']) or html_urls.get(n)
            if u:
                jobs.append((n, u))
                seen.add(n)

    out = {}
    total = len(jobs)
    pbar(0, total, '图标')
    for i, (n, u) in enumerate(jobs, 1):
        try:
            out[n] = to_data_url(u)
        except Exception as e:
            print('  [warn] 下载失败:', n, e)
        pbar(i, total, '图标')
        time.sleep(0.1)

    # 兜底：商店页没给图的家具，再去条目页找一次
    for it in shop:
        n = base_name(it['name'])
        if not n or n in out:
            continue
        if '专属时装' in n or '信物' in n:
            continue
        u = furn_icon_url(it['name']) or furn_icon_url(n)
        if not u:
            continue
        try:
            out[n] = to_data_url(u)
        except Exception as e:
            print('  [warn] 家具图下载失败:', n, e)
        time.sleep(0.1)

    ok('图标 %d/%d' % (len(out), len(names)))
    return out


PHASE_OPEN_RE = re.compile(
    r"开放时间：'''\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日\s*(\d{1,2}:\d{2})"
    r"\s*-\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日\s*(\d{1,2}:\d{2})"
    r"[\s\S]{0,120}?开放关卡：'''\s*【([^】]+)】"
)


def parse_phase_open(notice, year, month0):
    """从活动公告页读分段开放时间。返回 [{'name','start','end'}]。"""
    if not notice:
        return []
    notice = notice.split('#', 1)[0].strip()
    if not notice:
        return []
    try:
        wt = api(action='parse', page=notice, prop='wikitext')['parse']['wikitext']['*']
    except Exception as e:
        print('  [warn] 公告页读取失败:', e)
        return []
    # 公告里的月份不带年份，用活动开始的年月往前推
    out = []
    for m in PHASE_OPEN_RE.finditer(wt):
        m1, d1, t1, m2, d2, t2, nm = m.groups()
        y1 = year
        y2 = year
        if int(m1) < month0:      # 跨年
            y1 += 1
        if int(m2) < month0:
            y2 += 1
        out.append({
            'name': nm.strip(),
            'start': '%04d-%02d-%02d %s' % (y1, int(m1), int(d1), t1),
            'end': '%04d-%02d-%02d %s' % (y2, int(m2), int(d2), t2),
        })
    return out


def build(raw_name):
    note('读取活动主页面…')
    page = resolve_page(raw_name)
    say('页面：', page)
    s0, texts = fetch(page)

    note('解析商店…')
    shop, token, shop_name = '', '', ''
    for name, wt in texts.items():
        if 'EventShopList' in wt:
            it, tk = parse_shop(wt)
            if it:
                shop, token, shop_name = it, tk, name
                ok('商店「%s」%d 项' % (name, len(shop)))
                break
    if not shop:
        raise SystemExit('没找到活动商店（EventShopList）')
    if not token:
        raise SystemExit('没找到代币名')

    note('解析关卡…')
    stages = []
    for name, wt in texts.items():
        if name.startswith('关卡信息'):
            stages = parse_stages(wt, token)
            ok('关卡 %d 个' % len(stages))
            break

    note('解析里程碑…')
    miles, mtotal, msec = parse_milestones(texts, token)
    ok('里程碑 %d 条，合计 %d' % (len(miles), mtotal))

    phase_names, phase_of = [], {}
    try:
        secs = api(action='parse', page=page, prop='sections')['parse']['sections']
        for s in secs:
            if clean_text(s.get('line', '')) == '关卡信息':
                for gname, codes in parse_phases(page, s['index']):
                    phase_names.append(gname)
                    for c in codes:
                        phase_of[c] = gname
                break
    except Exception as e:
        print('  [warn] 解析关卡阶段失败:', e)
    say('关卡阶段：', [(n, len([k for k, v in phase_of.items() if v == n])) for n in phase_names])

    # 自检：每个阶段都得解析出关卡，不然就是又漏了页签
    if phase_names:
        got = {s.get('phase') for s in stages}
        lost = [n for n in phase_names
                if n and n not in got and any(phase_of.get(k) == n for k in phase_of)]
        if lost:
            print('  ' + red('⚠ 以下阶段没解析到关卡：' + '、'.join(lost)))


    banner = ''
    imgs = []
    try:
        note('下载图标（最慢的一步）…')
        imgs = api(action='parse', page=page, prop='images')['parse'].get('images', [])
        say('页面图片：', len(imgs))
        banner = find_banner(imgs)
        say('横幅：', banner or '未找到')
        html_urls = shop_icon_urls(page, shop_name)
        icons = fetch_icons(imgs, shop, html_urls)
    except Exception as e:
        print('  [warn] 取图失败:', e)
        icons = {}
    furn_names = set()
    if html_urls:
        for k, u in html_urls.items():
            if '家具' in urllib.parse.unquote(u) or '/assets/furniture/' in u:
                furn_names.add(k)
                furn_names.add(base_name(k))
    for it in shop:
        it['icon'] = icons.get(base_name(it['name']), '')
        nm = base_name(it['name'])
        # 家具零件、家具材料这类是道具，不是家具本体
        is_prop = ('零件' in nm) or ('材料' in nm)
        it['furniture'] = (not is_prop) and (
            (nm in furn_names) or (not it['icon'] and '时装' not in nm and '信物' not in nm))

    # 一次性代币来源：里程碑任务逐条 + 关卡首通逐条
    stage_codes = set(s['code'] for s in stages)
    one_time = []
    for m in miles:
        cond = m['cond']
        opened = True
        for c in re.findall(r'TL-[A-Z]*-?\d+', cond):
            if c not in stage_codes:
                opened = False
                break
        one_time.append({
            'name': cond,
            'token': m['token'],
            'kind': 'task',
            'open': opened,
            'src': msec,
        })
    for s in stages:
        if s.get('first'):
            one_time.append({
                'name': s['code'] + ' 首通',
                'token': s['first'],
                'kind': 'stage',
                'open': True,
                'src': '关卡信息',
                'phase': phase_of.get(s['code'], ''),
            })

    # 还没开放的关卡：任务里出现过、关卡表里没有，首通代币未知
    missing = []
    for m in miles:
        for c in re.findall(r'TL-[A-Z]+-?\d+', m['cond']):
            if c not in stage_codes and c not in missing:
                missing.append(c)
    for c in missing:
        one_time.append({
            'name': c + ' 首通',
            'token': None,
            'kind': 'stage',
            'open': False,
            'unknown': True,
            'src': '关卡信息',
            'phase': (phase_names[1] if (c.startswith('TL-EX') and len(phase_names) > 1) else (phase_names[2] if (c.startswith('TL-S') and len(phase_names) > 2) else '')),
        })
    if missing:
        say('未开放关卡（首通未知）：', len(missing), '个')

    notice = field(s0, '公告')
    phases = []
    try:
        st = field(s0, '活动开始时间') or '2026-01-01 00:00'
        year, month0 = int(st[:4]), int(st[5:7])
        phases = parse_phase_open(notice, year, month0)
        if phases:
            say('分段开放：', [(p['name'], p['start']) for p in phases])
        elif phase_names:
            # 公告里没有分段开放时间，但关卡表里有阶段名：
            # 用阶段名 + 活动开始时间兜底，弹窗与分组仍然能显示正确的阶段
            st_txt = field(s0, '活动开始时间') or ''
            phases = [{'name': n, 'start': st_txt, 'end': ''} for n in phase_names]
            say('分段开放：公告没读到时间，用阶段名兜底', [p['name'] for p in phases])
        else:
            say('分段开放：公告里没读到（可能是单段活动）')
    except Exception as e:
        print('  [warn] 分段开放解析失败:', e)

    theme = ''
    if banner:
        theme = theme_color(banner)
        if theme:
            say('主题色：', theme)

    data = {
        'theme': theme,
        'activity': {
            'title': page,
            'name': field(s0, '名称') or page,
            'subtitle': field(s0, '副标题'),
            'start': field(s0, '活动开始时间'),
            'end': field(s0, '活动结束时间'),
            'shopEnd': field(s0, '兑换结束时间'),
            'sanityPerRun': field(s0, '理智本消耗'),
            'banner': banner,
            'shopName': shop_name,
            'noticePage': (notice or '').split('#', 1)[0].strip(),
        },
        'phases': phases,
        'token': token,
        'stages': stages,
        'shop': shop,
        'milestones': miles,
        'milestoneTotal': mtotal,
        'oneTime': one_time,
    }
    return data


def list_activities(limit=500):
    """查 wiki 上带标准商店的 SideStory，最新的排在最前。"""
    q = ('[[分类:有活动信息的页面]]'
         '|?名称|?名称缩短|?活动开始时间#ISO|?活动结束时间#ISO'
         '|sort=活动开始时间|order=desc|limit=%d' % limit)
    try:
        d = api(action='ask', query=q)
    except Exception as e:
        print('  [warn] 活动列表查询失败:', e)
        return []
    import datetime
    out = []
    for key, v in ((d.get('query') or {}).get('results') or {}).items():
        p = v.get('printouts') or {}
        full = (p.get('名称') or [''])[0] or key          # SideStory「未许之地」
        if 'SideStory' not in full:                        # 只要和当前架构一致的活动
            continue
        short = (p.get('名称缩短') or [''])[0] or key      # 未许之地

        def _fmt(field):
            v = p.get(field)
            if v and isinstance(v[0], dict) and v[0].get('timestamp'):
                try:
                    return datetime.datetime.fromtimestamp(int(v[0]['timestamp'])).strftime('%Y-%m-%d')
                except Exception:
                    return ''
            return ''

        st = _fmt('活动开始时间')
        en = _fmt('活动结束时间')
        out.append({'page': key, 'name': full, 'short': short, 'start': st, 'end': en})
    return out


def dwidth(s):
    """按终端显示宽度算中文占位。"""
    import unicodedata
    return sum(2 if unicodedata.east_asian_width(c) in 'WF' else 1 for c in s)


def dpad(s, width):
    return s + ' ' * max(0, width - dwidth(s))


def _vt_on():
    """给 Windows 控制台打开 ANSI 转义，用来画反色高亮。"""
    if os.name != 'nt':
        return False
    try:
        import ctypes
        k = ctypes.windll.kernel32
        h = k.GetStdHandle(-11)
        m = ctypes.c_uint32()
        k.GetConsoleMode(h, ctypes.byref(m))
        k.SetConsoleMode(h, m.value | 0x0004)
        return True
    except Exception:
        return False


def choose(options, hint='↑↓ 选择 · 回车确认 · q 退出', back=False):
    """上下键选择列表，返回选中的下标；back=True 时 Esc/左键返回 -1。"""
    if not options:
        raise SystemExit('没有可选项')
    n = len(options)

    if not (IS_TTY and os.name == 'nt'):
        for i, o in enumerate(options, 1):
            print('  %2d  %s' % (i, o))
        tail = '（b 返回上级，q 退出）：' if back else '（q 退出）：'
        while True:
            raw = input('输入编号' + tail).strip().lower()
            if raw in ('q', 'quit', 'exit'):
                raise SystemExit(0)
            if back and raw in ('b', 'back'):
                return -1
            if raw.isdigit() and 1 <= int(raw) <= n:
                return int(raw) - 1
            print('  请输入 1 到 %d 之间的编号。' % n)

    import msvcrt
    _vt_on()
    idx = 0
    sys.stdout.write(dim('  ' + hint) + '\n')
    sys.stdout.flush()
    drawn = 0
    while True:
        if drawn:
            sys.stdout.write('\x1b[%dA' % drawn)
        for i, o in enumerate(options):
            body = ('  › ' if i == idx else '    ') + o
            if i == idx:
                body = '\x1b[7m' + body + '\x1b[0m'
            sys.stdout.write('\x1b[2K' + body + '\n')
        drawn = n
        sys.stdout.flush()

        ch = msvcrt.getch()
        if ch in (b'\xe0', b'\x00'):
            ch2 = msvcrt.getch()
            if ch2 == b'H':
                idx = (idx - 1) % n
            elif ch2 == b'P':
                idx = (idx + 1) % n
        elif ch in (b'\r', b'\n'):
            return idx
        elif ch in (b'q', b'Q'):
            raise SystemExit(0)
        elif ch in (b'\x1b',):
            if back:
                return -1
            raise SystemExit(0)


def _pick_from(group):
    """在一组活动里选一个；返回 None 表示退回上一层。"""
    opts = [dpad(a['name'][:32], 36) + ' ' + dim(a['start']) for a in group]
    i = choose(opts, '↑↓ 选择 · 回车确认 · Esc 返回', back=True)
    return None if i < 0 else group[i]


def pick_activity():
    import datetime
    title('活动代币计算器 · 数据更新')
    rule()
    print('  ' + dim('本功能需要 Python 环境，请确认您的计算机已配置。'))
    rule()

    _out('  正在查询活动列表…')
    acts = list_activities()
    if not acts:
        raise SystemExit('没有查到活动列表，检查一下网络再试。')

    today = datetime.date.today().strftime('%Y-%m-%d')
    past = [a for a in acts if a.get('end') and a['end'] <= today]

    while True:
        first = choose(['默认（最新活动数据）', '过往活动预览'])
        if first == 0:
            _out('  ' + dim('最新：' + acts[0]['name']))
            return acts[0]

        if not past:
            _out()
            _out('  ' + yellow('目前没有已结束的活动。'))
            continue

        # 年份 → 活动，一层就够
        years = sorted({a['start'][:4] for a in past if a['start']}, reverse=True)
        while True:
            _out()
            yopts = ['%s 年　%d 个活动' % (y, sum(1 for a in past if a['start'][:4] == y))
                     for y in years]
            yi = choose(yopts, '↑↓ 选择 · 回车确认 · Esc 返回', back=True)
            if yi < 0:
                break
            got = _pick_from([a for a in past if a['start'][:4] == years[yi]])
            if got:
                return got


def main():
    t0 = time.time()
    raw = ' '.join(sys.argv[1:]).strip()
    if raw:
        act = {'page': raw, 'name': raw, 'start': ''}
    else:
        act = pick_activity()

    print()
    title('正在更新：' + act['name'])
    note('开始抓取，请稍候…')
    try:
        data = build(act['page'])
    except SystemExit as e:
        print()
        print('  ' + red('这个活动没有标准商店（EventShopList），算不了。'))
        print('  ' + dim(str(e)))
        raise SystemExit(1)

    import datetime
    stamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    data['built'] = stamp

    with open(os.path.join(BASE, '活动数据.json'), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

    # 给页面用的可直接加载版本：本地页面和线上页面都靠它同步数据
    with open(os.path.join(BASE, '活动数据.js'), 'w', encoding='utf-8') as f:
        f.write('window.__ACTIVITY_DATA__ = ')
        json.dump(data, f, ensure_ascii=False)
        f.write(';\n')

    # 生成 HTML：复用 _gen_event_calc 的模板，它的日志不往用户面前糊
    import subprocess
    gen = os.path.join(_HERE, '_gen_event_calc.py')
    if os.path.exists(gen):
        r = subprocess.run([sys.executable, gen], capture_output=True, text=True,
                           encoding='utf-8', errors='replace')
        if r.returncode != 0:
            print(r.stdout or '')
            print(r.stderr or '')
            print('  ' + red('页面生成失败，上面是错误信息。'))
            raise SystemExit(1)

    rule()
    print('  %s 完成，用时 %.1f 秒' % (green('√'), time.time() - t0))
    print('  ' + dim('若计算器页面为开启状态可以直接刷新。'))
    print()


if __name__ == '__main__':
    main()
