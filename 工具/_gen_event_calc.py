# -*- coding: utf-8 -*-
"""读取活动数据 JSON，生成活动代币计算器 HTML。

优先读「活动数据.json」（更新活动数据.py 的输出），没有则退回 _event_data.json。
"""
import json, io, sys, datetime, os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

_HERE = os.path.dirname(os.path.abspath(__file__))
# 三个脚本平时放在「工具」子目录里，工作目录要提到上一级（页面、数据都那儿）
BASE = os.path.dirname(_HERE) if os.path.basename(_HERE) == '工具' else _HERE
src = None
for cand in ('活动数据.json', '_event_data.json'):
    p = os.path.join(BASE, cand)
    if os.path.exists(p):
        src = p
        break
if not src:
    raise SystemExit('找不到活动数据.json 或 _event_data.json')
with open(src, encoding='utf-8') as f:
    data = json.load(f)

# 这些是开发期日志，默认不往用户脸上糊
VERSION = '1.0.1'
VERBOSE = bool(os.environ.get('ARK_VERBOSE'))
def say(*a):
    if VERBOSE:
        print(*a)

say('数据来源：', os.path.basename(src))

data['built'] = data.get('built') or datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
payload = json.dumps(data, ensure_ascii=False)

# 数据托管仓库（GitHub 用户名/仓库名），写在同目录「仓库配置.txt」里，一行即可
repo = ''
cfg = os.path.join(BASE, '仓库配置.txt')
if os.path.exists(cfg):
    with open(cfg, encoding='utf-8-sig') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                repo = line
                break
say('数据仓库：', repo or '（未配置，只用本地服务）')

# 分享卡片用的绝对地址（GitHub Pages 默认域名）
site_url = ''
og_url = 'og.jpg'
if repo and '/' in repo:
    _user, _name = [x.strip() for x in repo.split('/', 1)]
    if _user and _name:
        site_url = 'https://%s.github.io/%s/' % (_user, _name)
        og_url = site_url + 'og.jpg'

HTML = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="算清明日方舟活动还要刷多少把、多少理智。勾选想要的商品，填上已换数量，直接给出还差多少代币。">
<meta name="version" content="1.0.1">
<meta name="theme-color" content="#0488a9">
<meta property="og:type" content="website">
<meta property="og:site_name" content="活动代币计算器">
<meta property="og:title" content="活动代币计算器 · 明日方舟">
<meta property="og:description" content="勾选想要的商品，算清还差多少代币、还要刷几把、多少理智。">
<meta property="og:image" content="__OGURL__">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:url" content="__SITEURL__">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="活动代币计算器 · 明日方舟">
<meta name="twitter:description" content="勾选想要的商品，算清还差多少代币、还要刷几把、多少理智。">
<meta name="twitter:image" content="__OGURL__">
<title>活动代币计算器</title>
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAzMiAzMiI+PHJlY3QgeD0iMiIgeT0iMSIgd2lkdGg9IjI4IiBoZWlnaHQ9IjMwIiByeD0iNiIgZmlsbD0iIzA0ODhhOSIvPjxyZWN0IHg9IjciIHk9IjUuNSIgd2lkdGg9IjE4IiBoZWlnaHQ9IjcuNSIgcng9IjIuMiIgZmlsbD0iI2ZmZmZmZiIvPjxyZWN0IHg9IjciIHk9IjE3IiB3aWR0aD0iMTgiIGhlaWdodD0iMTAuNSIgcng9IjIuMiIgZmlsbD0iI2ZmZmZmZiIvPjwvc3ZnPg==">
<link rel="apple-touch-icon" sizes="180x180" href="icon.png">
<link rel="alternate icon" href="icon.png">
<style>
  :root{
    --bg:#f4f4f5; --card:#ffffff; --line:#e3e4e7; --line2:#c8cbd1;
    --text:#111417; --muted:#767c86; --accent:#0488a9; --good:#14804a; --warn:#0488a9;
    --gold:#c9a227; --purple:#8b5cf6; --blue:#3b82f6; --grey:#9ca3af; --rainbow:#d946ef;
    --th:#f7f8f9; --hover:#fafbfd; --note:#eef5fc; --note-bd:#bcd6ee; --note-tx:#1c4f7c;
  }
  html[data-theme="dark"]{
    --bg:#141619; --card:#1b1e23; --line:#2b2f36; --line2:#3b4149;
    --text:#e6e8eb; --muted:#98a0aa; --accent:#18d1ff;
    --th:#22262c; --hover:#232830; --note:#1b2a38; --note-bd:#2d4a66; --note-tx:#9cc6ea;
  }
  .themebtn{position:fixed;top:14px;right:14px;z-index:9600;width:38px;height:38px;
            border-radius:50%;border:1px solid var(--line2);background:var(--card);
            color:var(--text);cursor:pointer;display:flex;align-items:center;
            justify-content:center;font-size:17px;line-height:1;padding:0;
            box-shadow:0 2px 10px rgba(0,0,0,.13);transition:transform .15s,box-shadow .15s}
  .themebtn:hover{transform:scale(1.07);box-shadow:0 3px 14px rgba(0,0,0,.2)}
  .themebtn:active{transform:scale(.97)}
  .themebtn[data-mode="light"]::before{content:'☀'}
  .themebtn[data-mode="dark"]::before{content:'☾'}
  .notifybtn{position:fixed;top:14px;right:62px;z-index:9600;width:38px;height:38px;
             border-radius:50%;border:1px solid var(--line2);background:var(--card);
             color:var(--text);cursor:pointer;display:flex;align-items:center;
             justify-content:center;padding:0;font:800 19px/1 system-ui,sans-serif;
             box-shadow:0 2px 10px rgba(0,0,0,.13);transition:transform .15s,box-shadow .15s}
  .notifybtn:hover{transform:scale(1.07);box-shadow:0 3px 14px rgba(0,0,0,.2)}
  .notifybtn:active{transform:scale(.97)}
  .notifybtn.on{border-color:var(--accent);color:var(--accent)}
  .ndot{position:absolute;top:6px;right:7px;width:8px;height:8px;border-radius:50%;
        background:#e0453e;box-shadow:0 0 0 2px var(--card);display:none}
  .ndot.on{display:block}
  .np{position:fixed;top:60px;right:14px;z-index:9600;width:min(340px,calc(100vw - 28px));
      background:var(--card);border:1px solid var(--line2);border-radius:8px;
      box-shadow:0 10px 34px rgba(0,0,0,.22);display:none;overflow:hidden}
  .np.on{display:block}
  .nphead{display:flex;align-items:center;justify-content:space-between;
          padding:11px 14px;border-bottom:1px solid var(--line);
          font-size:13px;font-weight:700;letter-spacing:.03em;color:var(--text)}
  .npclose{border:0;background:none;cursor:pointer;color:var(--muted);
           font-size:18px;line-height:1;padding:0 2px}
  .npclose:hover{color:var(--text)}
  .npbody{max-height:min(420px,62vh);overflow-y:auto}
  .nitem{cursor:pointer;transition:background .12s}
  .nitem:hover{background:var(--hover)}
  .nitem.unread .nt2{color:var(--accent)}
  .nun{display:inline-block;font-size:10.5px;margin-left:7px;padding:0 5px;
       border-radius:3px;background:#e0453e;color:#fff;vertical-align:1px;font-weight:600}
  .nitem{padding:12px 14px;border-bottom:1px solid var(--line)}
  .nitem:last-child{border-bottom:0}
  .nitem .nt2{font-size:13px;font-weight:700;color:var(--text);margin-bottom:4px}
  .nitem .nb{font-size:12.5px;line-height:1.7;color:var(--muted)}
  .nitem .nk{display:inline-block;font-size:11px;padding:1px 6px;border-radius:3px;
             margin-right:6px;vertical-align:1px;background:var(--th);color:var(--muted)}
  .nitem.act .nk{background:#fdecea;color:#b3352c}
  .nitem.phase .nk{background:#fff5e6;color:#9a6212}
  .nempty{padding:22px 14px;text-align:center;font-size:12.5px;color:var(--muted)}
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--text);
       font-family:"Microsoft YaHei","PingFang SC",system-ui,sans-serif;font-size:14px;line-height:1.65}
  .wrap{max-width:1200px;margin:0 auto;padding:26px 20px 120px}
  .en{font-size:10.5px;letter-spacing:.2em;text-transform:uppercase;color:var(--muted);font-weight:500}
  .kicker{display:flex;align-items:center;gap:9px;margin-bottom:8px}
  .kicker::before{content:'';width:3px;height:13px;background:var(--accent);display:block;flex:none}
  .kicker .sl{color:var(--line2);font-size:11px}
  /* 入场动效：和官网一样，区块进入视口时轻轻浮上来 */
  .pre{opacity:0;transform:translateY(12px);
       transition:opacity .5s cubic-bezier(.22,.61,.36,1),transform .5s cubic-bezier(.22,.61,.36,1);
       transition-delay:var(--d,0ms)}
  .pre.in{opacity:1;transform:none}
  @keyframes bump{0%{transform:scale(1)}38%{transform:scale(1.055)}100%{transform:scale(1)}}
  .stat .v.bump{animation:bump .32s cubic-bezier(.22,.61,.36,1)}
  @media(prefers-reduced-motion:reduce){
    .pre{opacity:1;transform:none;transition:none}
    .stat .v.bump{animation:none}
    .group .body{transition:none}
  }
  /* 键盘可访问：焦点可见环 */
  a:focus-visible,button:focus-visible,input:focus-visible,select:focus-visible,
  .ghead:focus-visible,.bgt:focus-visible,.chip:focus-visible{
    outline:2px solid var(--accent);outline-offset:2px;border-radius:4px}
  .ghead{cursor:pointer}
  .ghead:focus-visible{background:#fafbfd}
  .sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;
           clip:rect(0 0 0 0);white-space:nowrap;border:0}
  /* 打印 */
  @media print{
    @page{margin:12mm}
    html,body{background:#fff!important}
    .wrap{max-width:none;padding:0}
    .banner,.notice,.bar,.tabs,.bonus,.mini-btn,.shopname,.hint,header button{display:none!important}
    header{border-bottom:1px solid #bbb;margin-bottom:10px;padding-bottom:8px}
    h1{font-size:17px}
    h1 .h1en{font-size:8px;letter-spacing:.12em}
    .subtitle{font-size:12px}
    .panel,.group{box-shadow:none!important;border:1px solid #ccc!important;break-inside:auto}
    .stats{gap:0!important;background:none!important}
    .stat{border:1px solid #ccc;margin-right:-1px}
    .stat .v{font-size:15px}
    .group{margin-bottom:8px}
    .group .body{display:block!important;overflow:visible!important;grid-template-rows:1fr!important}
    .group.collapsed .body{display:block!important}
    .group.collapsed .ghead .arrow{transform:none}
    .tscroll{overflow:visible!important}
    .tscroll table{min-width:0!important}
    th{background:#eee!important;color:#000!important;font-size:9px;padding:3px 5px;letter-spacing:0}
    td{font-size:9.5px;padding:3px 5px}
    .ico{width:18px;height:18px}
    tr,td,th{break-inside:avoid}
    a{color:#000;text-decoration:none}
    .ghead .arrow{display:none}
  }
  header{display:flex;align-items:flex-end;justify-content:space-between;gap:16px;margin-bottom:18px;
         padding-bottom:15px;border-bottom:1px solid var(--line2)}
  h1{font-size:26px;margin:0 0 7px;font-weight:600;letter-spacing:-.01em;line-height:1.2}
  h1 .h1en{font-size:10.5px;letter-spacing:.18em;font-weight:500;color:var(--muted);margin-left:11px;
           vertical-align:middle;text-transform:uppercase}
  .subtitle{font-size:15.5px;font-weight:600;margin:0 0 5px}
  .subtitle .shopname{margin-left:10px;padding-left:12px;border-left:1px solid var(--line2);font-size:13.5px;font-weight:500;color:#5c626c}
  .hacts{display:flex;gap:8px;flex:none;align-items:center}
  .warn{display:none;width:18px;height:18px;border-radius:50%;background:#e0a800;color:#fff;
        font-size:12px;font-weight:700;line-height:18px;text-align:center;cursor:help;
        position:relative;flex:none;user-select:none}
  .warn.on{display:inline-block}
  .warn::after{content:attr(data-tip);position:absolute;right:-4px;top:calc(100% + 9px);
        white-space:nowrap;background:#22262c;color:#fff;font-size:12px;font-weight:400;
        padding:6px 10px;border-radius:4px;opacity:0;pointer-events:none;z-index:99;
        transition:opacity .15s;box-shadow:0 4px 14px rgba(0,0,0,.18)}
  .warn:hover::after{opacity:1}
  /* 弹窗 */
  .modal{display:none;position:fixed;inset:0;z-index:9000}
  .modal.on{display:block}
  .mmask{position:absolute;inset:0;background:rgba(12,15,20,.55);backdrop-filter:blur(2px)}
  .mbox{position:relative;max-width:480px;margin:12vh auto 0;background:var(--card);
      display:flex;flex-direction:column;min-height:460px;
        border:1px solid var(--line2);border-radius:6px;padding:22px 24px 18px;
        box-shadow:0 18px 50px rgba(0,0,0,.28)}
  .mtt{font-size:16.5px;font-weight:600;margin-bottom:12px;padding-left:11px;position:relative}
  .mtt::before{content:'';position:absolute;left:0;top:4px;bottom:4px;width:3px;background:var(--accent)}
  .mbody{font-size:13.5px;line-height:1.85;color:var(--text)}
  .mbody p{margin:0 0 9px}
  .mbody b{font-weight:600;white-space:nowrap}
  .mbody code{background:var(--th);border:1px solid var(--line);border-radius:3px;
              padding:1px 5px;font-size:12.5px;font-family:ui-monospace,Consolas,monospace;
              white-space:nowrap}
  .mstep{position:relative;padding-left:26px;margin:0 0 9px}
  .mn{position:absolute;left:0;top:3px;flex:none;width:18px;height:18px;border-radius:50%;
      background:var(--accent);color:#fff;font-size:11.5px;line-height:18px;text-align:center}
  .mtip{color:var(--muted);font-size:12.5px;margin-top:4px}
  .mflash{display:flex;align-items:center;gap:8px;margin:10px 0 12px;padding:8px 11px;
    background:#fff4e5;border-left:3px solid #e8a020;border-radius:3px;
    color:#8a5200;font-size:13px;font-weight:600;animation:mpulse 1.8s ease-in-out infinite}
  .mflash .dot{width:8px;height:8px;border-radius:50%;background:#e8a020;flex:none;
    animation:mpulse 1.8s ease-in-out infinite}
  .flashline{animation:mpulse 1.8s ease-in-out infinite;font-weight:600;color:#8a5200}
  @keyframes mpulse{0%,100%{opacity:1}50%{opacity:.42}}
  .ver{color:var(--muted);font-size:11.5px;margin-left:8px;
       font-family:ui-monospace,Consolas,monospace;letter-spacing:.04em}
  .mignore{margin:10px 0 0;padding:8px 10px;background:var(--th);border-left:3px solid var(--line2);
           font-size:12.5px;color:#4f5560}
  .mnote{font-size:12px;color:#7c8290;line-height:1.7;border-top:1px dashed var(--line);
    padding-top:9px;margin-top:11px}
  .mnote a{color:var(--accent);text-decoration:none;border-bottom:1px solid currentColor}
  .mnote a:hover{opacity:.8}
  .mbody{flex:1 1 auto}
  .mact{margin-top:auto;display:flex;justify-content:flex-end;gap:9px;margin-top:16px;padding-top:14px;
        border-top:1px solid var(--line)}
  .meta{color:var(--muted);font-size:12.5px}
  .meta b{color:var(--text);font-weight:600}
  button{font-family:inherit;font-size:13px;border:1px solid var(--line2);background:var(--card);
         color:var(--text);padding:7px 14px;border-radius:4px;cursor:pointer;transition:.15s;letter-spacing:.02em}
  button:hover{border-color:#9aa0aa;background:#fafafb}
  button.primary{background:var(--accent);border-color:var(--accent);color:#fff}
  button.primary:hover{background:#8d161d;border-color:#8d161d}
  .panel{background:var(--card);border:1px solid var(--line);border-radius:4px;padding:18px 20px;margin-bottom:16px}
  .rows{display:flex;flex-wrap:wrap;gap:22px;align-items:flex-end}
  .field{display:flex;flex-direction:column;gap:6px}
  .field label{font-size:12.5px;color:#4f5560;font-weight:600;letter-spacing:.02em}
  .field input{width:140px;padding:8px 11px;border:1px solid var(--line2);border-radius:4px;
               font-family:ui-monospace,Consolas,monospace;font-size:15px;font-variant-numeric:tabular-nums}
  .field input:focus{outline:none;border-color:var(--accent);
                    box-shadow:0 0 0 3px color-mix(in srgb, var(--accent) 9%, transparent)}
  .field select{font-family:inherit;font-size:13.5px;padding:8px 10px;border:1px solid var(--line2);border-radius:4px;background:var(--card)}
  .field select:focus{outline:none;border-color:var(--accent)}
  .stats{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;margin-top:18px;
         background:var(--line);border:1px solid var(--line);border-radius:4px;overflow:hidden}
  .stat{background:var(--card);padding:13px 16px}
  .stat .k{font-size:11px;color:var(--muted);letter-spacing:.06em}
  .stat .v{font-size:24px;font-weight:600;font-variant-numeric:tabular-nums;margin-top:3px;letter-spacing:-.01em}
  .stat.need .v{color:var(--warn)}
  .stat.left{background:#fff7f7;border:1px solid #f0c9c9;box-shadow:inset 0 0 0 1px #fbe4e4}
  .stat .calc{font-size:12.5px;color:#9aa1ab;margin-top:3px;letter-spacing:.01em}
  .stat .calc b{font-weight:600;color:#6d747e}
  .stat.left .v{color:var(--accent);font-size:26px;font-weight:800}
  .stat.left .k{color:#a61b23;font-weight:600}
  .stat.left.uncertain .k::after{content:" · 估算";font-size:10.5px;font-weight:400;opacity:.75}
  .tabs{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:12px}
  .tabs button.on{background:#eef3ff;border-color:#b9cdfb;color:#1d4ed8}
  .group{margin-bottom:16px;background:var(--card);border:1px solid var(--line);border-radius:4px;overflow:hidden}
  .ghead{display:flex;align-items:center;gap:11px;padding:13px 18px;background:var(--card);
         border-bottom:1px solid var(--line);cursor:pointer;user-select:none}
  .ghead .idx{font-size:11px;letter-spacing:.14em;color:#8d939c;font-weight:700;font-variant-numeric:tabular-nums}
  .ghead .t{font-weight:600;font-size:14px}
  .ghead .n{color:var(--muted);font-size:11.5px}
  .ghead .sum{margin-left:auto;color:var(--muted);font-size:12.5px;font-variant-numeric:tabular-nums}
  .ghead .arrow{color:var(--muted);font-size:11px;transition:.2s}
  .group.collapsed .arrow{transform:rotate(-90deg)}
  .group .body{overflow:hidden}
  .group.collapsed .body{display:none}
  .group .body > *{min-height:0}
  table{width:100%;border-collapse:collapse}
  th,td{padding:10px 12px;text-align:left;border-bottom:1px solid #f1f2f4;font-size:13.5px}
  th{font-size:12.5px;color:#565c66;font-weight:600;background:#f7f8f9;letter-spacing:0;
     border-bottom:1px solid var(--line2)}
  tr:last-child td{border-bottom:none}
  tbody tr:hover{background:#fbfbfc}
  td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
  th.c,td.num,th.num{text-align:center}
  td.name{display:flex;align-items:center;gap:9px}
  .ladder{margin-top:3px;font-size:11.5px;color:#9aa0a8;font-variant-numeric:tabular-nums}
  .dot{width:7px;height:7px;border-radius:50%;flex:none;background:var(--grey)}
  .banner{display:none;margin:0 auto 22px;max-width:880px;border-radius:2px;overflow:hidden;background:transparent}
  .banner img{width:100%;height:auto;display:block}
  .notice{display:none;margin:0 0 20px;padding:13px 16px 13px 14px;border:1px solid #bcd6ee;background:#eef5fc;border-radius:3px;gap:11px;align-items:flex-start}  .notice.show{display:flex}
  .notice .ic{flex:none;width:22px;height:22px;border-radius:50%;background:#3576b8;color:#fff;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;line-height:1;margin-top:1px}
  .notice .ic svg{width:14px;height:14px;display:block}
  .notice .nt{flex:1 1 auto;min-width:0;font-size:13.5px;color:#1e3a56;line-height:1.75}
  .notice .nt b{font-weight:700}
  .notice .nt .sub{display:block;color:#5b7288;font-size:12.5px;margin-top:2px}
  .notice .nt .cd{font-size:16px;font-weight:700;color:#14416b;font-variant-numeric:tabular-nums;letter-spacing:.01em}
  .notice.notice-warn{border-color:#e6cfa4;background:#fdf7e9}
  .notice.notice-warn .ic{background:#b8862f}
  .notice.notice-warn .nt{color:#5a4416}
  .notice.notice-warn .nt .sub{color:#8a7440}
  .ico{width:32px;height:32px;object-fit:contain;vertical-align:middle;margin-right:8px;flex:none}
  .name{display:inline-flex;align-items:center}
  .tag{font-size:11px;color:#8a93a4;border:1px solid var(--line);border-radius:5px;padding:1px 5px;margin-left:7px;white-space:nowrap}
  .bonus{margin-top:14px;border-top:1px dashed var(--line);padding-top:12px}
  .bhead{display:flex;align-items:center;gap:10px;font-size:13.5px;color:#4f5560;margin-bottom:11px;flex-wrap:wrap}
  .bhead .bsum{color:var(--text);font-weight:700}
  .mini-btn{font-size:12.5px;padding:3px 10px;border:1px solid var(--line2);background:var(--card);border-radius:6px;color:var(--muted);cursor:pointer}
  .mini-btn:hover{background:#f2f5f9;color:var(--text);border-color:var(--muted)}
  .blist{display:flex;flex-wrap:wrap;gap:8px}
  .bgrp{margin-bottom:12px}
  .bgrp.fold .bwrap{display:none}
  .bph{font-size:12.5px;color:#5c626c;font-weight:700;margin:11px 0 6px;letter-spacing:.02em}
  .bph i{font-style:normal;color:#8d939c;font-weight:400;margin-left:9px;font-size:12px}
  .bgt{font-size:14px;color:var(--text);margin-bottom:8px;display:flex;gap:9px;align-items:center;cursor:pointer;user-select:none}
  .bgt .arw{font-size:10px;color:#8d939c;transition:transform .2s;display:inline-block}
  .bgrp.fold .bgt .arw{transform:rotate(-90deg)}
  .bgt .gt{color:#1b2027;font-weight:700}
  .bgt .gt i{font-style:normal;color:#b3bac6;font-weight:400;margin-left:8px}
  .chip.unlocked{opacity:.65;border-style:dashed}
  .chip.nodata{opacity:.5;cursor:default}
  .chip.nodata b{color:#aab1bd}
  .chip{display:inline-flex;align-items:center;gap:6px;padding:4px 9px;border:1px solid var(--line);border-radius:4px;font-size:12px;background:var(--card);color:var(--muted);cursor:pointer;user-select:none}
  .chip.on{border-color:#9dc2ee;background:#eff6ff;color:var(--text)}
  .chip b{font-weight:600;color:var(--text)}
  .tscroll th,.tscroll td{white-space:nowrap}
  .tscroll td:nth-child(2) .name{display:inline-flex;align-items:center;gap:5px;white-space:nowrap}
  .tscroll td:nth-child(2) .name img{flex:none}
  .tscroll td:nth-child(2),.tscroll th:nth-child(2){min-width:190px}
  .cbox{display:flex;align-items:center;gap:4px;white-space:nowrap;
    justify-content:center;position:relative;min-height:26px}
  .cbox input.mini{width:58px;min-width:0;text-align:center}
  .cbox select.mini-sel{width:58px}

    .mini-sel{font-size:12.5px;padding:3px 6px;border:1px solid var(--line);border-radius:6px;background:var(--card);min-width:58px;text-align:center}
  .tierrow td{background:#fafbfd}
  .q-彩 .dot,.dot.q-彩{background:var(--rainbow)}
  .dot.q-金{background:var(--gold)} .dot.q-紫{background:var(--purple)}
  .dot.q-蓝{background:var(--blue)} .dot.q-灰{background:var(--grey)}
  tr.want{background:#f7faff}
  input[type=checkbox]{width:16px;height:16px;accent-color:var(--accent);cursor:pointer}
  .mini{width:66px;padding:4px 7px;border:1px solid var(--line);border-radius:6px;
        font-family:inherit;font-size:13px;text-align:right;font-variant-numeric:tabular-nums}
  .mini:focus{outline:none;border-color:var(--accent)}
  .inf{color:var(--muted);font-size:12px}
  .bar{position:fixed;left:0;right:0;bottom:0;background:var(--card);border-top:1px solid var(--line2);
       padding:13px 20px;display:flex;align-items:center;gap:26px;justify-content:center;z-index:9}
  .bar .item{font-size:12px;color:var(--muted);letter-spacing:.04em}
  .bar .item b{color:var(--text);font-size:18px;font-variant-numeric:tabular-nums;margin-left:6px;letter-spacing:-.01em}
  .bar .item.hi b{color:var(--warn)}
  .hint{color:var(--muted);font-size:12.5px;margin-top:10px}
  .toast{position:fixed;left:50%;bottom:84px;transform:translateX(-50%);background:#1c2128;color:#fff;
         padding:9px 16px;border-radius:8px;font-size:13px;opacity:0;pointer-events:none;transition:.25s}
  .toast.show{opacity:1}
  @media(max-width:760px){
    .wrap{padding:14px 12px 120px}
    .banner{max-width:100%;margin-bottom:16px}
    header{flex-wrap:wrap;gap:12px}
    header>div:first-child{width:100%;min-width:0}
    header>div:last-child{flex:1 1 100%;flex-wrap:wrap}
    h1{font-size:23px}
    h1 .h1en{display:none}
    .subtitle{font-size:14.5px}
    .subtitle .shopname{display:inline-block;margin-left:8px;padding-left:9px}
    .meta{font-size:12px;line-height:1.8;word-break:break-word}
    .notice{padding:11px 12px}
    .notice .nt{font-size:12.5px;min-width:0;word-break:break-word}
    .notice .nt .cd{font-size:15px}
    .rows{gap:12px}
    .field{width:100%}
    .field input,.field select{width:100%}
    .stats{grid-template-columns:repeat(2,1fr)}
    .stat{padding:12px 12px}
    .stat .v{font-size:22px}
    .bhead{font-size:12.5px;gap:7px}
    .bhead span:first-child{flex:1 1 100%}
    .chip{font-size:11.5px;padding:3px 7px;gap:4px}
    .tabs{flex-wrap:wrap}
    .tabs button{font-size:12.5px;padding:5px 10px}
    .group{overflow:hidden;min-width:0}
    .group .body{overflow:hidden;min-width:0}
    .group.collapsed .body{display:none}
    .tscroll{overflow-x:auto;-webkit-overflow-scrolling:touch;min-width:0;max-width:100%;
      scrollbar-width:thin}
    /* 窄屏把表格压紧一点，滑动距离短些：820 左右，一屏半能滑完 */
    .tscroll table{min-width:820px!important}
    .tscroll th:nth-child(2),.tscroll td:nth-child(2){min-width:130px!important}
    .tscroll th:nth-child(3),.tscroll td:nth-child(3){width:54px!important}
    .tscroll th:nth-child(4),.tscroll td:nth-child(4){width:96px!important}
    .tscroll th:nth-child(5),.tscroll td:nth-child(5){width:124px!important}
    .tscroll th:nth-child(6),.tscroll td:nth-child(6){width:54px!important}
    .tscroll th:nth-child(7),.tscroll td:nth-child(7){width:58px!important}
    .tscroll input.mini,.tscroll select.mini-sel{width:52px!important}
    /* 表格给足最小宽度，让它横向滚动，别把名字挤成一字一行 */
    /* 提示框在窄屏一律换行，倒计时也允许折行 */
    #notice,#notice *{white-space:normal!important;word-break:break-word!important;
      overflow-wrap:anywhere!important}
    #notice{max-width:100%}
    #notice{overflow:hidden;max-width:100%}
    #notice .nt{display:block;flex:1 1 0;min-width:0;width:0;overflow:hidden}
    html,body{overflow-x:hidden}
    .wrap{overflow-x:hidden}
    .notice .nt,.notice .nt .sub,.hint,.meta,.lead{
      white-space:normal!important;word-break:break-word!important;overflow-wrap:anywhere!important}
    .notice .nt{min-width:0;flex:1 1 auto}
    .notice .nt .cd{white-space:normal!important}
    .bhead{flex-wrap:wrap;gap:6px}
    .ghead{row-gap:6px}
    .mbox{max-width:calc(100vw - 28px);min-height:0;margin:7vh auto 0;padding:20px 18px}
    .mtt{font-size:16px}
    .mbody{font-size:13px}
    .mact{flex-wrap:wrap;gap:8px}
    .mact button{flex:1 1 auto;min-width:0}
    .tscroll table{min-width:620px;table-layout:auto}
    .tscroll td:nth-child(2),.tscroll th:nth-child(2){min-width:150px}
    .tscroll td:nth-child(2){white-space:nowrap}
    .tscroll td:nth-child(2) .tag{white-space:nowrap}
    /* 右上角两个悬浮按钮在小屏会盖住分组标题，挪到右下 */
    #warnIcon,.themebtn,.theme-btn,#themeBtn{top:auto!important;bottom:64px!important}
    .tscroll th:nth-child(1),.tscroll td:nth-child(1){width:42px!important;padding-left:4px;padding-right:4px}
    .tscroll th:nth-child(3),.tscroll td:nth-child(3){width:56px!important;padding-left:4px;padding-right:4px}
    .tscroll table{min-width:1140px}
  .tscroll th:nth-child(4),.tscroll td:nth-child(4){width:112px!important;padding-left:4px;padding-right:4px}
    .tscroll th:nth-child(5),.tscroll td:nth-child(5){width:164px!important;padding-left:4px;padding-right:4px}
    .tscroll th:nth-child(6),.tscroll td:nth-child(6){width:60px!important;padding-left:4px;padding-right:4px}
    .tscroll th:nth-child(7),.tscroll td:nth-child(7){width:56px!important;padding-left:4px;padding-right:4px}
    .tscroll td{padding-top:8px;padding-bottom:8px;font-size:12.5px}
    .tscroll input[type=number],.tscroll select{width:100%;min-width:40px;padding:4px 6px;font-size:12.5px}
    .tscroll .ico{width:26px;height:26px;margin-right:5px}
    .ghead{flex-wrap:wrap;gap:6px 8px;padding:11px 12px}
    .ghead .t{font-size:14px}
    .bar{flex-wrap:wrap;gap:8px 14px;padding:10px 12px;overflow-x:auto}
    .bar .item{font-size:12px}
    .bar .item b{font-size:15px}
    .panel{padding:14px 12px}
  }
  /* ---------- 深色模式（放最后，保证覆盖上面的浅色规则） ---------- */
  html[data-theme="dark"] body{background:var(--bg);color:var(--text)}
  html[data-theme="dark"] header{border-bottom-color:var(--line2)}
  html[data-theme="dark"] h1 .h1en, html[data-theme="dark"] .en, html[data-theme="dark"] .kicker .sl{color:var(--muted)}
  html[data-theme="dark"] .subtitle .shopname{color:var(--muted);border-left-color:var(--line2)}
  html[data-theme="dark"] .syncstate{color:var(--muted)}
  html[data-theme="dark"] .panel, html[data-theme="dark"] .group, html[data-theme="dark"] .stat, html[data-theme="dark"] .ghead, html[data-theme="dark"] .mini-btn, html[data-theme="dark"] .chip, html[data-theme="dark"] .tabs button, html[data-theme="dark"] button, html[data-theme="dark"] input, html[data-theme="dark"] select, html[data-theme="dark"] .bar, html[data-theme="dark"] .toast{
  background:var(--card);color:var(--text)}
  html[data-theme="dark"] button, html[data-theme="dark"] .mini-btn, html[data-theme="dark"] .chip, html[data-theme="dark"] .tabs button{border-color:var(--line2)}
  html[data-theme="dark"] button.primary{background:var(--accent);color:#fff;border-color:var(--accent)}
  html[data-theme="dark"] .notice{background:var(--note);border-color:var(--note-bd);color:var(--note-tx)}
  html[data-theme="dark"] .notice .nt{color:var(--note-tx)}
  html[data-theme="dark"] .notice .nt .sub{color:#a9c9e2}
  html[data-theme="dark"] .notice .nt .cd{color:#bfdcf5}
  html[data-theme="dark"] .notice .ic{background:#2f6da3;color:#fff}
  html[data-theme="dark"] .notice.notice-warn{background:#3a2a12;border-color:#5c4318;color:#e8c27a}
  html[data-theme="dark"] .notice .badge{background:var(--note-bd)}
  html[data-theme="dark"] .banner{background:#0f1115}
  html[data-theme="dark"] .tscroll th{background:var(--th);color:#c3c9d2}
  html[data-theme="dark"] .tierrow td{background:var(--card)}
  html[data-theme="dark"] .tierrow td .tag{background:#2a2f36}
  html[data-theme="dark"] .mflash{background:#3a2c14;border-left-color:#c99a3e;color:#f0c674}
  html[data-theme="dark"] .flashline{color:#f0c674}
  html[data-theme="dark"] .mnote{color:#8f96a3;border-top-color:#343a42}
  html[data-theme="dark"] .group .body tbody tr:hover td{background:var(--hover)}
  html[data-theme="dark"] .tag{background:#2a2f36;color:var(--muted);border-color:var(--line2)}
  html[data-theme="dark"] .bgt{color:var(--text)}
  html[data-theme="dark"] .bgt .gt{color:var(--text)}
  html[data-theme="dark"] .bgt .arw, html[data-theme="dark"] .bph, html[data-theme="dark"] .bph i, html[data-theme="dark"] .bsum, html[data-theme="dark"] .bhead, html[data-theme="dark"] .hint, html[data-theme="dark"] .ghead .n, html[data-theme="dark"] .ghead .idx, html[data-theme="dark"] .ladder, html[data-theme="dark"] .stat .k{color:var(--muted)}
  html[data-theme="dark"] .ghead .t, html[data-theme="dark"] .name, html[data-theme="dark"] .name b{color:var(--text)}
  html[data-theme="dark"] .stat .v{color:var(--text)}
  html[data-theme="dark"] .stat.need .v{color:var(--accent)}
  html[data-theme="dark"] .chip{color:var(--muted)}
  html[data-theme="dark"] .chip.on{background:#2b1a1d;border-color:var(--accent);color:#f0c9cc}
  html[data-theme="dark"] .chip.nodata{opacity:.55}
  html[data-theme="dark"] .bgrp{border-color:var(--line)}
  html[data-theme="dark"] .tscroll td, html[data-theme="dark"] .tscroll tr{border-color:var(--line)}
  html[data-theme="dark"] .ghead:focus-visible{background:var(--hover)}
  html[data-theme="dark"] .banner img{opacity:.94}
  html[data-theme="dark"] .foot .item b{color:var(--text)}
  }

/* 数量与已换两列的控件布局：桌面和窄屏共用 */
.cbox{display:flex;align-items:center;gap:4px;white-space:nowrap;
  justify-content:center;position:relative;min-height:26px}
.cbox input.mini{width:58px;min-width:0;text-align:center}
.cbox select.mini-sel{width:58px}
.tscroll table{min-width:1140px}
.tscroll th:nth-child(4),.tscroll td:nth-child(4){width:104px;padding-left:4px;padding-right:4px}
.tscroll th:nth-child(5),.tscroll td:nth-child(5){width:146px;padding-left:4px;padding-right:4px}
.maxb{position:absolute;right:2px;top:50%;transform:translateY(-50%);background:none;border:none;padding:0;margin:0;font:9.5px/1 inherit;color:#c9ced6;cursor:pointer;letter-spacing:.02em}
</style>
<script>
(function(){
  var KEY = 'ark_theme';
  var mode = 'light';
  try { mode = localStorage.getItem(KEY) || 'light'; } catch(e){}
  if (mode !== 'dark') mode = 'light';
  function apply(){
    var dark = mode === 'dark';
    document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light');
    var b = document.getElementById('themeBtn');
    if (b){
      b.setAttribute('data-mode', mode);
      var tip = mode === 'dark' ? '深色' : '浅色';
      b.setAttribute('title', '当前：' + tip + '（点击切换）');
      b.setAttribute('aria-label', '配色：' + tip + '，点击切换');
    }
  }
  window.arkTheme = {
    get: function(){ return mode; },
    set: function(m){
      mode = m;
      try { localStorage.setItem(KEY, m); } catch(e){}
      apply();
    },
    cycle: function(){
      this.set(mode === 'dark' ? 'light' : 'dark');
    }
  };
  apply();
  document.addEventListener('DOMContentLoaded', function(){
    var b = document.getElementById('themeBtn');
    if (b) b.addEventListener('click', function(){ window.arkTheme.cycle(); });
    apply();
  });
})();
</script>
</head>
<body>
<div class="wrap">
  <div class="banner" id="banner"></div>
  <header>
    <div>
      <div class="kicker"><span class="en">SIDESTORY</span><span class="sl">//</span><span class="en" id="kickerDate">—</span></div>
      <h1 id="pageTitle">活动代币计算器<span class="h1en">EVENT TOKEN CALCULATOR</span></h1>
      <div class="subtitle" id="actName"></div>
      <div class="meta" id="meta"></div>
    </div>
    <div class="hacts">
      <span class="warn" id="warnIcon" role="img" aria-label="数据同步异常"></span>
      <button id="btnReload" class="primary">同步最新数据</button>
      <button id="btnImport">导入本地文件</button>
    </div>
  </header>

  <div class="notice" id="notice" role="status" aria-live="polite"></div>

  <div class="panel">
    <div class="rows">
      <div class="field">
        <label for="haveToken">当前持有代币</label>
        <input type="number" id="haveToken" value="0" min="0" step="1" inputmode="numeric">
      </div>
      <div class="field">
        <label for="stagePick">刷哪一关（每把代币 / 理智）</label>
        <select id="stagePick" style="width:230px"></select>
      </div>
    </div>
    <div class="bonus">
      <div class="bhead">
        <span>一次性代币来源（任务奖励 + 关卡首通），勾选已拿到的</span>
        <span class="bsum" id="bSum"></span>
        <button class="mini-btn" id="bAll">全选</button>
        <button class="mini-btn" id="bNone">全不选</button>
      </div>
      <div id="bonusList"></div>
    </div>
    <div class="stats">
      <div class="stat"><div class="k">勾选商品总价 <span class="en">TOTAL</span></div><div class="v" id="sTotal">0</div></div>
      <div class="stat"><div class="k">其中已换 <span class="en">OWNED</span></div><div class="v" id="sDone">0</div></div>
      <div class="stat need"><div class="k">还差代币 <span class="en">MISSING</span></div><div class="v" id="sLeft">0</div><div class="calc" id="sLeftCalc"></div></div>
      <div class="stat left"><div class="k">还需刷 <span class="en">RUNS</span></div><div class="v" id="sRuns">0</div></div>
    </div>
    <div class="hint" id="hint"></div>
  </div>

  <div class="tabs">
    <button data-act="all">全选</button>
    <button data-act="none">全不选</button>
    <button data-act="mats" title="不包括无限库存材料">只选材料</button>
    <button data-act="clearDone">清空已换</button>
    <button data-act="reset">重置</button>
  </div>

  <div id="shop"></div>

  <div class="panel" style="margin-top:18px;color:var(--muted);font-size:12.5px;line-height:1.9">
    <b style="color:var(--text)">说明</b><br>
    代币与理智 1:1，普通关每 1 理智掉 1 个「__TOKEN__」。首通奖励不计入刷取折算。<br>
    勾选「要换」＝这件算进计划；「已换」填你已经买掉的数量，会从还差里扣除。<br>
    数据来源 PRTS wiki。页面打开时会自动取一次最新数据，也可以手动点击「同步最新数据」。换活动时用「导入本地文件」。<br>
     非官方工具，不收费、无广告。游戏素材版权归鹰角网络，数据依 CC BY-NC-SA 4.0 使用，详细许可见仓库里的 LICENSE.md。<span class="ver">v1.0.2</span>
  </div>
</div>

<div class="bar">
  <div class="item">总需 <b id="bTotal">0</b></div>
  <div class="item">已换 <b id="bDone">0</b></div>
  <div class="item hi">还差 <b id="bLeft">0</b></div>
  <div class="item">还需刷 <b id="bRuns">0</b> 把</div>
  <div class="item">理智 <b id="bSanity">0</b></div>
</div>
<button id="notifyBtn" class="notifybtn" type="button" aria-label="通知" title="通知">!<span class="ndot" id="ndot"></span></button>
<div class="np" id="np" role="dialog" aria-label="通知">
  <div class="nphead"><span>通知</span><button class="npclose" id="npClose" type="button" aria-label="关闭">×</button></div>
  <div class="npbody" id="npBody"></div>
</div>
<div class="modal" id="nmodal">
  <div class="mmask" id="nmask"></div>
  <div class="mbox" role="dialog" aria-modal="true" aria-labelledby="ntt">
    <div class="mtt" id="ntt"></div>
    <div class="mbody" id="nbd"></div>
    <div class="mact"><button id="nOk" type="button">知道了</button><button id="nSync" class="primary" type="button">同步最新数据</button></div>
  </div>
</div>
</div>
<button id="themeBtn" class="themebtn" type="button"
        aria-label="切换深浅色" title="切换深浅色"></button>

<div class="toast" id="toast"></div>
<input type="file" id="fileInput" accept=".json" hidden>

<script id="DATA" type="application/json">__PAYLOAD__</script>
<script src="活动数据.js" onerror="void 0"></script>
<script>
var DATA = (window.__ACTIVITY_DATA__) || JSON.parse(document.getElementById('DATA').textContent);

function num(v){ v = parseFloat(v); return isFinite(v) ? v : 0; }
function fmt(n){ return (Math.round(n*100)/100).toLocaleString('zh-CN'); }
function toast(msg){
  var t = document.getElementById('toast');
  t.textContent = msg; t.classList.add('show');
  clearTimeout(t._h); t._h = setTimeout(function(){ t.classList.remove('show'); }, 2200);
}

/* ---------- 状态 ---------- */
var items = [];
function buildItems(){
  var raw = DATA.shop.map(function(it, i){
    return {
      id: i,
      group: it.group || '其他',
      name: it.name,
      qty: it.qty === -1 ? Infinity : it.qty,
      price: it.price,
      quality: it.quality || '',
      icon: it.icon || '',
      furniture: !!it.furniture,
      want: false,
      count: it.qty === -1 ? 1 : it.qty,
      done: 0
    };
  });

  // 「阶段商品1~N：同一件东西」是阶梯解锁，合并成一条带下拉的记录
  var out = [], i = 0;
  var TIER = /^阶段商品\s*\d+\s*[：:]\s*(.+)$/;
  while (i < raw.length){
    var m = TIER.exec(raw[i].name);
    if (m){
      var base = m[1].trim(), steps = [], j = i;
      while (j < raw.length){
        var m2 = TIER.exec(raw[j].name);
        if (!m2 || m2[1].trim() !== base) break;
        steps.push(raw[j]);
        j++;
      }
      if (steps.length > 1){
        out.push({
          id: -1,
          tier: base,
          group: steps[0].group,
          name: base,
          icon: steps[0].icon,
          quality: steps[0].quality,
          furniture: false,
          steps: steps.map(function(s){ return {price: s.price}; }),
          step: 0,
          doneStep: 0,
          price: steps[0].price,
          qty: steps.length,
          want: false,
          count: steps.length,
          done: 0
        });
        i = j;
        continue;
      }
    }
    out.push(raw[i]);
    i++;
  }
  items = out.map(function(it, k){ it.id = k; return it; });
}
/* 不保存任何状态：每次打开都是全不选、TL-1、代币 0 */
/* ---------- 本地保存 ---------- */
function stateKey(){ return 'ark_event_calc_' + ((DATA.activity && DATA.activity.title) || 'x'); }
function loadState(){
  try{
    var raw = localStorage.getItem(stateKey());
    if (!raw) return;
    var s = JSON.parse(raw);
    var h = document.getElementById('haveToken');
    if (h && s.have !== undefined) h.value = s.have;
    var p = document.getElementById('stagePick');
    if (p && s.stage){
      var hit = false;
      for (var i = 0; i < p.options.length; i++) if (p.options[i].value === s.stage) hit = true;
      if (hit) p.value = s.stage;
    }
    // 按名字取，活动数据更新导致条目增减也不会串位
    var bMap = {};
    (s.bonus || []).forEach(function(v){
      if (Array.isArray(v)) bMap[v[0]] = v[1];
      else if (typeof v === 'object' && v) bMap[v.n] = v.on;
    });
    bonusState.forEach(function(b){
      var key = b.nm || b.name || '';
      if (bMap[key] !== undefined) b.on = !!bMap[key];
    });
    var iMap = {};
    (s.items || []).forEach(function(v){
      if (Array.isArray(v)) iMap[v[0]] = v[1];
      else if (typeof v === 'object' && v) iMap[v.n] = v;
    });
    items.forEach(function(it){
      var v = iMap[it.name];
      if (!v) return;
      if (v.w !== undefined) it.want = !!v.w;
      if (v.c !== undefined) it.count = v.c;
      if (v.d !== undefined) it.done = v.d;
      if (v.s !== undefined) it.step = v.s;
      if (v.ds !== undefined) it.doneStep = v.ds;
    });
    syncStage();
  }catch(e){}
}
var _saveTimer = null;
function saveState(){
  if (_saveTimer) clearTimeout(_saveTimer);
  _saveTimer = setTimeout(function(){
    try{
      var p = document.getElementById('stagePick');
      localStorage.setItem(stateKey(), JSON.stringify({
        have: document.getElementById('haveToken').value,
        stage: p ? p.value : '',
        bonus: bonusState.map(function(b){ return [b.nm || b.name || '', b.on ? 1 : 0]; }),
        items: items.map(function(it){
          return [it.name, {w: it.want ? 1 : 0, c: it.count, d: it.done, s: it.step, ds: it.doneStep}];
        })
      }));
    }catch(e){}
  }, 250);
}
function resetAll(){
  try{ localStorage.removeItem(stateKey()); }catch(e){}
  document.getElementById('haveToken').value = 0;
  buildItems();
  buildBonus();
  renderMeta();
  renderBonus();
  renderShop();
  recalc();
  toast('已重置');
}

/* ---------- 动效 ---------- */
var lastVals = {};
function bump(ids, vals){
  ids.forEach(function(id, i){
    var el = document.getElementById(id);
    if (!el) return;
    if (lastVals[id] !== undefined && lastVals[id] !== vals[i]){
      el.classList.remove('bump');
      void el.offsetWidth;
      el.classList.add('bump');
    }
    lastVals[id] = vals[i];
  });
}
function watchReveal(){
  var nodes = [].slice.call(document.querySelectorAll('.panel, .group'));
  if (!('IntersectionObserver' in window) ||
      (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches)){
    nodes.forEach(function(el){ el.classList.add('in'); });
    return;
  }
  var io = new IntersectionObserver(function(es){
    es.forEach(function(e){
      if (e.isIntersecting){ e.target.classList.add('in'); io.unobserve(e.target); }
    });
  }, { threshold: 0.03, rootMargin: '0px 0px -30px 0px' });
  nodes.forEach(function(el, i){
    if (el.classList.contains('pre')) return;
    el.classList.add('pre');
    el.style.setProperty('--d', Math.min(i, 6) * 45 + 'ms');
    io.observe(el);
  });
  // 兜底：万一观察器没触发，两秒半后全部显示，不留白屏
  setTimeout(function(){
    document.querySelectorAll('.pre:not(.in)').forEach(function(el){ el.classList.add('in'); });
  }, 2500);
}

/* ---------- 渲染 ---------- */
function applyTheme(){
  var t = DATA.theme;
  if (!t || !/^#[0-9a-fA-F]{6}$/.test(t)) return;
  document.documentElement.style.setProperty('--accent', t);
  document.documentElement.style.setProperty('--warn', t);
  var m = document.querySelector('meta[name="theme-color"]');
  if (m) m.setAttribute('content', t);
}

function renderMeta(){
  var a = DATA.activity;
  var an = document.getElementById('actName');
  if (an){
    var nm = (a.name || a.title || '');
    if (a.shopName) nm += '<span class="shopname">' + a.shopName + '</span>';
    an.innerHTML = nm;
  }
  var kd = document.getElementById('kickerDate');
  if (kd) kd.textContent = (a.start || '').replace(/^\d{4}-/, '').replace(/-/g, ' / ') || '—';
  document.getElementById('meta').innerHTML =
    '代币 <b>' + DATA.token + '</b>　·　活动 ' + a.start + ' — ' + a.end +
    '　·　兑换截止 ' + a.shopEnd + '　·　数据更新于 ' + (DATA.built || '未知');

  var bn = document.getElementById('banner');
  if (a.banner){
    bn.innerHTML = '<img src="' + a.banner + '" alt="" referrerpolicy="no-referrer" onerror="this.parentNode.style.display=\'none\'">';
    bn.style.display = 'block';
  }

  // 刷关下拉：只列有常规掉落的关卡
  var regs = (DATA.stages || []).filter(function(s){ return s.regular && s.token > 0; });
  var pick = document.getElementById('stagePick');
  if (regs.length){
    pick.innerHTML = regs.map(function(s){
      return '<option value="' + s.code + '">' + s.code + '　' + s.sanity + ' 理智 / ' + s.token + ' 代币</option>';
    }).join('');
    var def = regs.filter(function(s){ return s.code === 'TL-1'; })[0] || regs[0];
    pick.value = def.code;
    pick.onchange = syncStage;
    syncStage();
  } else {
    pick.innerHTML = '<option>无常规掉落关卡</option>';
    window.BEST = {code:'', sanity:0, token:0};
  }
}
function syncStage(){
  var pick = document.getElementById('stagePick');
  var regs = (DATA.stages || []).filter(function(s){ return s.regular && s.token > 0; });
  var s = regs.filter(function(x){ return x.code === pick.value; })[0];
  window.BEST = s || {code: '', sanity: 0, token: 0};
  renderNotice();
  if (typeof recalc === 'function' && items.length) recalc();
}

function parseDT(s){
  if (!s) return null;
  var m = String(s).match(/(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})/);
  if (!m) return null;
  return new Date(+m[1], +m[2] - 1, +m[3], +m[4], +m[5]).getTime();
}
function fmtSpan(ms){
  if (ms <= 0) return '0 分';
  var d = Math.floor(ms / 86400000), h = Math.floor(ms % 86400000 / 3600000), mi = Math.floor(ms % 3600000 / 60000);
  if (d > 0) return d + ' 天 ' + h + ' 小时 ' + mi + ' 分';
  if (h > 0) return h + ' 小时 ' + mi + ' 分';
  return mi + ' 分';
}
function fmtCd(ms){
  if (ms <= 0) return '0 秒';
  var d = Math.floor(ms / 86400000), h = Math.floor(ms % 86400000 / 3600000),
      mi = Math.floor(ms % 3600000 / 60000), se = Math.floor(ms % 60000 / 1000);
  if (d > 0) return d + ' 天 ' + h + ' 小时 ' + mi + ' 分 ' + se + ' 秒';
  if (h > 0) return h + ' 小时 ' + mi + ' 分 ' + se + ' 秒';
  return mi + ' 分 ' + se + ' 秒';
}
var _cdTimer = null;
function tickCd(){
  var el = document.querySelector('#notice .cd');
  if (!el) return;
  var np = nextPhase(Date.now());
  if (!np || np.t - Date.now() <= 0){ renderNotice(); return; }
  el.textContent = fmtCd(np.t - Date.now());
}
function stopCd(){
  if (_cdTimer){ clearInterval(_cdTimer); _cdTimer = null; }
}
function nextPhase(now){
  var best = null;
  (DATA.phases || []).forEach(function(p){
    var t = parseDT(p.start);
    if (t && now < t && (!best || t < best.t)) best = {name: p.name, t: t, start: p.start};
  });
  return best;
}
function renderNotice(){
  var box = document.getElementById('notice');
  if (!box) return;
  var a = DATA.activity || {};
  var now = Date.now();
  var st = parseDT(a.start), en = parseDT(a.end), se = parseDT(a.shopEnd);
  var best = window.BEST || {};
  var sanity = best.sanity || 21, code = best.code || '当前关卡';
  var html = '', warn = false;

  var np = nextPhase(now);
  var isCd = !!np && (!en || now < en);
  if (isCd){
    var left = np.t - now;
    warn = left < 3600000;
    html = '距离「<b>' + np.name + '</b>」开放还有 ' +
      '<span class="cd">' + fmtCd(left) + '</span>' +
      '<span class="sub">开放时间 ' + np.start + '。届时请点击「同步最新数据」按钮，新关卡的掉落数据才会进来。</span>';
  } else if (en && now > en){
    warn = true;
    if (se && now <= se){
      html = '<b>活动关卡已关闭，商店兑换还剩 ' + fmtSpan(se - now) + '。</b>' +
        '<span class="sub">兑换截止 ' + a.shopEnd + '，手上的代币还能用。</span>';
    } else {
      html = '<b>该活动已经结束。</b><span class="sub">页面数据仅供存档参考。</span>';
    }
  } else if (st && now < st){
    html = '<b>活动还没有开始。</b><span class="sub">开始时间 ' + a.start + '。</span>';
  } else {
    // 没有下一阶段、也没结束：不显示任何提示
    box.className = 'notice';
    box.innerHTML = '';
    return;
  }

  // 只在「真落后」时提醒：有阶段已经开放，但数据里还没有它的关卡。
  // 单纯数据放了一天不算落后——活动数据本来就不天天变，天天喊反而让人以为永远不是最新的。
  var lag = (typeof staleKind === 'function') ? staleKind() : null;
  if (lag)
    html += '<span class="sub">数据抓取自 ' + (DATA.built || '较早') + '，新开放的阶段还没进来，请点击「同步最新数据」按钮。</span>';
  box.className = 'notice show' + (warn ? ' notice-warn' : '');
  var ico = isCd
    ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round"><circle cx="12" cy="13.4" r="7.2"/><path d="M12 9.9v3.7l2.4 1.5"/><path d="M5.2 4.6 7 2.9M18.8 4.6 17 2.9"/></svg>'
    : '!';
  box.innerHTML = '<div class="ic">' + ico + '</div><div class="nt">' + html + '</div>';
  if (isCd){
    if (!_cdTimer) _cdTimer = setInterval(tickCd, 1000);
  } else {
    stopCd();
  }
}

function renderShop(){
  var box = document.getElementById('shop');
  var groups = [], map = {};
  items.forEach(function(it){
    if (!map[it.group]) { map[it.group] = []; groups.push(it.group); }
    map[it.group].push(it);
  });
  var html = '';
  groups.forEach(function(g, gi){
    var list = map[g];
    html += '<div class="group" data-g="' + gi + '">' +
      '<div class="ghead" role="button" tabindex="0" aria-expanded="true"' +
      ' aria-label="展开或收起 ' + g.replace('无限库存区', '无限库存') + '"><span class="arrow">▼</span>' +
      '<span class="idx">' + ('0' + (gi + 1)).slice(-2) + '</span>' +
      '<span class="t">' + g.replace('无限库存区', '无限库存') + '</span>' +
      '<span class="n">' + list.length + ' 项</span><span class="sum" data-sum="' + gi + '"></span></div>' +
      '<div class="body"><div class="tscroll"><table><thead><tr>' +
      '<th class="c" style="width:58px">要换</th><th>商品名称</th><th class="c" style="width:74px">单价</th>' +
      '<th class="c" style="width:120px">数量</th>' +
      '<th class="c" style="width:96px">已换</th>' +
      '<th class="c" style="width:76px">剩余</th>' +
      '<th class="c" style="width:76px">小计</th></tr></thead><tbody>';
    list.forEach(function(it){
      var q = it.quality ? ' dot q-' + it.quality : ' dot';
      var mark = it.icon
        ? '<img class="ico" src="' + it.icon + '" alt="">'
        : '<span class="' + q.trim() + '" style="margin-right:8px"></span>';
      if (it.tier){
        var N = it.steps.length;
        var opts = '';
        for (var k = 0; k <= N; k++){
          opts += '<option value="' + k + '"' + (k === it.step ? ' selected' : '') + '>' + (k === 0 ? '不换' : k + ' 档') + '</option>';
        }
        var dop = '';
        for (var k2 = 0; k2 <= it.step; k2++){
          dop += '<option value="' + k2 + '"' + (k2 === it.doneStep ? ' selected' : '') + '>' + (k2 === 0 ? '未换' : k2 + ' 档') + '</option>';
        }
        var ladder = it.steps.map(function(s){ return s.price; }).join(' / ');
        html += '<tr data-id="' + it.id + '" class="tierrow">' +
          '<td><input type="checkbox" data-role="want"' + (it.want ? ' checked' : '') + '></td>' +
          '<td><div class="name">' + mark + '<b>' + it.tier + '</b>' +
            '<span class="tag">阶梯兑换，共 ' + N + ' 档</span></div>' +
            '<div class="ladder" title="' + ladder + '">' + ladder + '</div></td>' +
          '<td class="num">起 ' + it.steps[0].price + '</td>' +
          '<td class="num" style="text-align:center"><select class="mini-sel" data-role="step">' + opts + '</select></td>' +
          '<td class="num" style="text-align:center"><select class="mini-sel" data-role="doneStep">' + dop + '</select></td>' +
          '<td class="num" data-role="remain">' + (it.step - it.doneStep) + ' 档</td>' +
          '<td class="num" data-role="sub">—</td></tr>';
        return;
      }
      var doneCell;
      if (it.qty === 1){
        doneCell = '<td class="num"><div class="cbox"><input type="checkbox" data-role="done1"' + (it.done >= 1 ? ' checked' : '') + '>' + '</div></td>';
      } else if (it.qty !== Infinity && it.qty < 10){
        var dopts = '';
        for (var q = 0; q <= it.qty; q++){
          dopts += '<option value="' + q + '"' + (q === it.done ? ' selected' : '') + '>' + q + '</option>';
        }
        doneCell = '<td class="num"><div class="cbox"><select class="mini-sel" data-role="doneSel">' + dopts + '</select>' + '</div></td>';
      } else {
        doneCell = '<td class="num"><div class="cbox"><input class="mini" data-role="done" type="number" step="1" min="-1"' +
          ' max="' + it.count + '" value="' + it.done + '">' +
          '<button type="button" class="maxb" data-role="max" title="填到上限 ' + it.qty + '"' +
          (it.qty !== Infinity && it.qty > 5 ? '' : ' style="visibility:hidden"') + '>max</button>' +
          '</div></td>';
      }
      html += '<tr data-id="' + it.id + '">' +
        '<td><input type="checkbox" data-role="want"' + (it.want ? ' checked' : '') + '></td>' +
        '<td><span class="name">' + mark + it.name +
          (it.furniture ? '<span class="tag">活动家具</span>' : '') + '</span></td>' +
        '<td class="num">' + it.price + '</td>' +
        '<td class="num"><div class="cbox"><input class="mini" data-role="count" type="number" step="1" min="-1"' +
          (it.qty !== Infinity ? ' max="' + it.qty + '"' : '') +
          ' value="' + it.count + '"></div></td>' +
        doneCell +
        '<td class="num" data-role="remain">' + Math.max(0, it.count - it.done) + '</td>' +
        '<td class="num" data-role="sub">0</td></tr>';
    });
    html += '</tbody></table></div></div></div>';
  });
  box.innerHTML = html;

  box.querySelectorAll('.ghead').forEach(function(h){
    function toggle(){
      h.parentNode.classList.toggle('collapsed');
      h.setAttribute('aria-expanded', h.parentNode.classList.contains('collapsed') ? 'false' : 'true');
    }
    h.addEventListener('click', toggle);
    h.addEventListener('keydown', function(e){
      if (e.key === 'Enter' || e.key === ' ' || e.key === 'Spacebar'){
        e.preventDefault(); toggle();
      }
    });
  });
  box.querySelectorAll('tr[data-id]').forEach(function(tr){
    var id = +tr.getAttribute('data-id');
    var it = items[id];
    if (!it) return;
    var w = tr.querySelector('[data-role=want]');
    if (w) w.addEventListener('change', function(e){
      if (it.tier){
        it.step = e.target.checked ? 1 : 0;
        it.want = it.step > 0;
        var st0 = tr.querySelector('[data-role=step]');
        if (st0) st0.value = it.step;
        if (typeof refillDoneStep === 'function') refillDoneStep();
      } else {
        it.want = e.target.checked;
      }
      recalc();
    });
    var c = tr.querySelector('[data-role=count]');
    function clampCount(el){
      var v = Math.floor(num(el.value));
      // 已经是 0 还往下减（变成负数）：跳到上限
      if (isFinite(v) && v < 0 && it.qty !== Infinity && it.qty > 0){
        it.count = it.qty;
        el.value = it.qty;
        recalc();
        return;
      }
      if (!isFinite(v) || v < 0) v = 0;
      if (it.qty !== Infinity && v > it.qty) v = it.qty;
      it.count = v;
      if (String(el.value) !== String(v)) el.value = v;
      recalc();
    }
    function fillMax(){
      if (it.qty === Infinity || it.qty < 1) return;
      it.want = true;
      if (w) w.checked = true;
      it.count = it.qty;
      if (c) c.value = it.qty;
      if (it.tier){
        if (!it.step) it.step = 1;
        it.doneStep = it.step;
        var st1 = tr.querySelector('[data-role=step]');
        var dst1 = tr.querySelector('[data-role=doneStep]');
        if (st1) st1.value = it.step;
        if (dst1) dst1.value = it.doneStep;
      } else {
        it.done = it.count;
        var d1x = tr.querySelector('[data-role=done1]');
        var dsx = tr.querySelector('[data-role=doneSel]');
        var dnx = tr.querySelector('[data-role=done]');
        if (d1x) d1x.checked = it.done >= 1;
        if (dsx) dsx.value = it.done;
        if (dnx) dnx.value = it.done;
      }
      recalc();
      saveState();
    }
    var mb = tr.querySelector('[data-role=max]');
    if (mb) mb.addEventListener('click', function(e){ e.stopPropagation(); fillMax(); });

    if (c){
      c.addEventListener('input', function(e){ clampCount(e.target); });
      c.addEventListener('blur', function(e){ clampCount(e.target); });
      c.addEventListener('keydown', function(e){
        if (it.qty === Infinity || it.qty < 1) return;
        var v = Math.floor(num(c.value));
        if (e.key === 'ArrowDown' && v <= 0){
          e.preventDefault(); it.count = it.qty; c.value = it.qty; recalc();
        } else if (e.key === 'ArrowUp' && v >= it.qty){
          e.preventDefault(); it.count = 0; c.value = 0; recalc();
        }
      });
    }

    var d = tr.querySelector('[data-role=done]');
    function clampDone(el){
      var v = Math.floor(num(el.value));
      // 已经是 0 还往下减：跳到当前数量
      if (isFinite(v) && v < 0){
        it.done = it.count;
        el.value = it.count;
        recalc();
        return;
      }
      if (!isFinite(v) || v < 0) v = 0;
      if (it.qty !== Infinity && v > it.qty) v = it.qty;
      it.done = v;
      if (String(el.value) !== String(v)) el.value = v;
      recalc();
    }
    if (d){
      d.addEventListener('input', function(e){ clampDone(e.target); syncWant(); });
      d.addEventListener('blur', function(e){ clampDone(e.target); syncWant(); });
    }
    // 填了「已换」就说明确实要换，顺手把左边的「要换」勾上
    function syncWant(){
      if ((it.count > 0 || it.done > 0 || it.doneStep > 0) && !it.want){
        it.want = true;
        if (w) w.checked = true;
      }
    }
    var d1 = tr.querySelector('[data-role=done1]');
    if (d1) d1.addEventListener('change', function(e){
      it.done = e.target.checked ? 1 : 0; syncWant(); recalc();
    });
    var ds = tr.querySelector('[data-role=doneSel]');
    if (ds) ds.addEventListener('change', function(e){
      it.done = Math.max(0, num(e.target.value)); syncWant(); recalc();
    });
    var st = tr.querySelector('[data-role=step]');
    var dst = tr.querySelector('[data-role=doneStep]');
    function refillDoneStep(){
      if (!dst) return;
      if (it.doneStep > it.step) it.doneStep = it.step;
      var o = '';
      for (var j = 0; j <= it.step; j++){
        o += '<option value="' + j + '"' + (j === it.doneStep ? ' selected' : '') + '>' +
          (j === 0 ? '未换' : j + ' 档') + '</option>';
      }
      dst.innerHTML = o;
    }
    if (st) st.addEventListener('change', function(e){
      it.step = +e.target.value;
      it.want = it.step > 0;
      if (w) w.checked = it.want;
      refillDoneStep();
      recalc();
    });
    if (dst) dst.addEventListener('change', function(e){
      it.doneStep = +e.target.value;
      // 已换档数不能超过要换档数，超了就把它顶上去
      if (it.doneStep > it.step){
        it.step = it.doneStep;
        if (st) st.value = it.step;
      }
      syncWant();
      recalc();
    });
  });
  if (typeof watchReveal === 'function') watchReveal();
}

/* ---------- 一次性代币来源 ---------- */
var bonusState = [];
function buildBonus(){
  bonusState = (DATA.oneTime || []).map(function(b){
    return {
      name: b.name, token: (b.token === null || b.token === undefined) ? null : b.token,
      kind: b.kind, open: b.open !== false, unknown: !!b.unknown, on: false,
      src: b.src || '', phase: b.phase || ''
    };
  });
  renderBonus();
}
var _foldState = {task: true, stage: true};
function renderBonus(){
  var box = document.getElementById('bonusList');
  if (!bonusState.length){
    box.innerHTML = '<span style="color:#98a2b3;font-size:12.5px">这个活动没有可单独列出的一次性来源</span>';
    return;
  }
  var groups = [{k: 'task', label: '任务奖励'}, {k: 'stage', label: '关卡首通'}];
  var html = '';
  var foldState = _foldState;
  groups.forEach(function(g){
    var idx = [];
    bonusState.forEach(function(b, i){ if (b.kind === g.k) idx.push(i); });
    if (!idx.length) return;
    var sum = idx.reduce(function(s, i){
      var t = bonusState[i].token;
      return s + ((bonusState[i].on && t !== null) ? t : 0);
    }, 0);
    var picked = idx.filter(function(i){ return bonusState[i].on && bonusState[i].token !== null; }).length;
    var src = bonusState[idx[0]].src || '';
    var chip = function(i){
      var b = bonusState[i];
      var lab = (b.token === null) ? '?' : fmt(b.token);
      var dis = (b.token === null) ? ' disabled' : '';
      return '<label class="chip' + (b.on ? ' on' : '') + (b.open ? '' : ' unlocked') +
        (b.token === null ? ' nodata' : '') + '" data-b="' + i + '">' +
        '<input type="checkbox"' + (b.on ? ' checked' : '') + dis + '> ' +
        b.name + ' <b>' + lab + '</b>' +
        (b.open ? '' : '<span class="tag">未开放</span>') + '</label>';
    };
    var inner;
    if (g.k === 'stage'){
      // 关卡按游戏内的阶段按钮分桶
      var order = [], buckets = {};
      idx.forEach(function(i){
        var p = bonusState[i].phase || '其他';
        if (!buckets[p]){ buckets[p] = []; order.push(p); }
        buckets[p].push(i);
      });
      inner = order.map(function(p){
        if (order.length === 1 && p === '其他')
          return '<div class="blist">' + buckets[p].map(chip).join('') + '</div>';
        var s2 = buckets[p].reduce(function(s, i){
          var t = bonusState[i].token;
          return s + ((bonusState[i].on && t !== null) ? t : 0);
        }, 0);
        var n2 = buckets[p].filter(function(i){ return bonusState[i].on && bonusState[i].token !== null; }).length;
        return '<div class="bph">' + p + '<i>已选 ' + n2 + ' / ' + buckets[p].length + ' 项 · 合计 ' + fmt(s2) + '</i></div>' +
          '<div class="blist">' + buckets[p].map(chip).join('') + '</div>';
      }).join('');
    } else {
      inner = '<div class="blist">' + idx.map(chip).join('') + '</div>';
    }
    html += '<div class="bgrp' + (foldState[g.k] ? ' fold' : '') + '" data-g="' + g.k + '"><div class="bgt">' +
      '<span class="arw">▼</span>' +
      '<span class="gt">' + (src && g.k !== 'stage' ? src + ' · ' : '') + g.label +
      '<i>已选 ' + picked + ' / ' + idx.length + ' 项 · 合计 ' + fmt(sum) + '</i></span>' +
      '<button class="mini-btn" data-ball="' + g.k + '">全选</button>' +
      '<button class="mini-btn" data-bnone="' + g.k + '">全不选</button></div>' +
      '<div class="bwrap">' + inner + '</div></div>';
  });
  box.innerHTML = html;
  box.querySelectorAll('[data-b]').forEach(function(el){
    el.addEventListener('change', function(){
      var i = +el.getAttribute('data-b');
      var on = el.querySelector('input').checked;
      bonusState[i].on = on;
      el.classList.toggle('on', on);
      updateBonusSum();
      recalc();
    });
  });
  box.querySelectorAll('.bgt').forEach(function(t){
    t.addEventListener('click', function(e){
      if (e.target.closest('button')) return;
      var g = t.parentNode.getAttribute('data-g');
      foldState[g] = !foldState[g];
      t.parentNode.classList.toggle('fold', foldState[g]);
    });
  });
  box.querySelectorAll('[data-ball]').forEach(function(btn){
    btn.addEventListener('click', function(){
      var k = btn.getAttribute('data-ball');
      // 没开放的关卡拿不到，全选时跳过
      bonusState.forEach(function(b){ if (b.kind === k && b.token !== null && b.open !== false) b.on = true; });
      renderBonus(); recalc();
    });
  });
  box.querySelectorAll('[data-bnone]').forEach(function(btn){
    btn.addEventListener('click', function(){
      var k = btn.getAttribute('data-bnone');
      bonusState.forEach(function(b){ if (b.kind === k) b.on = false; });
      renderBonus(); recalc();
    });
  });
  updateBonusSum();
}
function bonusTotal(){
  return bonusState.reduce(function(s, b){
    return s + ((b.on && b.token !== null) ? b.token : 0);
  }, 0);
}
// 还没拿到的一次性代币：全部有数的减去已经勾上的
function bonusUnclaimed(){
  return bonusState.reduce(function(s, b){
    return s + ((!b.on && b.token !== null) ? b.token : 0);
  }, 0);
}
function updateBonusSum(){
  var el = document.getElementById('bSum');
  if (el){
    var closed = bonusState.reduce(function(s, b){
      return s + ((!b.open && b.on && b.token !== null) ? b.token : 0);
    }, 0);
    el.textContent = '已选 ' + fmt(bonusTotal()) + (closed ? '（其中未开放 ' + fmt(closed) + '）' : '');
  }
  document.querySelectorAll('.bgrp').forEach(function(g){
    var k = g.getAttribute('data-g');
    var idx = [];
    bonusState.forEach(function(b, i){ if (b.kind === k) idx.push(i); });
    var sum = 0, picked = 0;
    idx.forEach(function(i){
      var b = bonusState[i];
      if (b.on && b.token !== null){ sum += b.token; picked++; }
    });
    var t = g.querySelector('.gt i');
    if (t) t.textContent = '已选 ' + picked + ' / ' + idx.length + ' 项 · 合计 ' + fmt(sum);
  });
}

/* ---------- 计算 ---------- */
function recalc(){
  var total = 0, done = 0;
  var gsum = {};
  items.forEach(function(it){
    var sub = 0, subDone = 0;
    if (it.tier){
      function cum(k){
        var s = 0;
        for (var j = 0; j < k && j < it.steps.length; j++) s += it.steps[j].price;
        return s;
      }
      var need = cum(it.step), got = cum(it.doneStep);
      subDone = Math.max(0, need - got);
      total += need;
      done += got;
    } else {
      var remain = Math.max(0, it.count - it.done);
      sub = remain * it.price;
      subDone = Math.min(it.done, it.count) * it.price;
      if (it.want) { total += sub + subDone; done += subDone; }
    }
    var tr = document.querySelector('tr[data-id="' + it.id + '"]');
    var on = it.tier ? (it.step > 0) : (it.want && it.count > 0);
    if (tr){
      tr.classList.toggle('want', !!on);
      var cell = tr.querySelector('[data-role=sub]');
      if (cell) cell.textContent = on ? fmt(it.tier ? subDone : sub) : '—';
      if (it.tier){
        var cb = tr.querySelector('[data-role=want]');
        if (cb) cb.checked = it.step > 0;
      }
      var rc = tr.querySelector('[data-role=remain]');
      if (rc) rc.textContent = it.tier
        ? Math.max(0, it.step - it.doneStep) + ' 档'
        : String(Math.max(0, it.count - it.done));
    }
    gsum[it.group] = (gsum[it.group] || 0) + (it.tier ? ((it.step > 0) ? subDone : 0) : (it.want ? sub + subDone : 0));
  });

  var have = num(document.getElementById('haveToken').value);
  var mile = bonusTotal();
  var unclaimed = bonusUnclaimed();          // 还没拿到的一次性代币
  // 有关卡还没开放、或首通代币还不知道，结果就只能估
  var unsure = bonusState.some(function(b){ return b.open === false || b.token === null; });
  var left = Math.max(0, total - done - have);   // 一次性来源不参与计算
  // 还得自己刷的部分：还差里扣掉将来能白拿的那一份
  var needFarm = Math.max(0, left - unclaimed);
  var best = window.BEST || {sanity: 0, token: 0};
  var runs = best.token ? needFarm / best.token : 0;

  document.getElementById('sTotal').textContent = fmt(total);
  document.getElementById('sDone').textContent = fmt(done);
  document.getElementById('sLeft').textContent = fmt(left);
  var lc = document.getElementById('sLeftCalc');
  if (lc){
    lc.innerHTML = unclaimed > 0
      ? '-' + (unsure ? '（约）' : '') + fmt(unclaimed) + ' = <b>' + fmt(needFarm) + '</b>'
      : '';
  }
  var leftBox = document.querySelector('.stat.left');
  if (leftBox) leftBox.classList.toggle('uncertain', unsure);
  document.getElementById('sRuns').innerHTML = Math.ceil(runs) + ' <i style="font-style:normal;font-size:13px;font-weight:500;color:var(--muted);margin-left:3px">把</i>';
  document.getElementById('bTotal').textContent = fmt(total);
  document.getElementById('bDone').textContent = fmt(done);
  document.getElementById('bLeft').textContent = fmt(left);
  document.getElementById('bRuns').textContent = Math.ceil(runs);
  document.getElementById('bSanity').textContent = Math.ceil(runs) * best.sanity;
  bump(['sTotal','sDone','sLeft','sRuns'], [total, done, left, Math.ceil(runs)]);

  document.getElementById('hint').textContent =
    '还差 ' + fmt(left) + ' 代币，按 ' + (best.code || '当前关卡') + (unsure ? ' 估算约 ' : ' 折算约 ') +
    Math.ceil(runs) + ' 把 / ' + Math.ceil(runs) * best.sanity + ' 理智。' +
    '（一次性来源已计入 ' + fmt(unclaimed) + ' 代币，已获取就勾选）';

  updateBonusSum();

  document.querySelectorAll('[data-sum]').forEach(function(el){
    var g = el.getAttribute('data-sum');
    var lists = {};
    items.forEach(function(it){ (lists[it.group] = lists[it.group] || []).push(it); });
    var gname = Object.keys(lists)[+g];
    var v = gsum[gname] || 0;
    el.textContent = v ? ('已选 ' + fmt(v)) : '';
  });

  saveState();
}

/* ---------- 快捷操作 ---------- */
document.querySelectorAll('.tabs button').forEach(function(b){
  b.addEventListener('click', function(){
    var act = b.getAttribute('data-act');
    if (act === 'all') items.forEach(function(it){
      it.want = true;
      if (it.tier) it.step = it.steps.length;   // 阶梯商品全选＝换满
    });
    if (act === 'none') items.forEach(function(it){
      it.want = false;
      if (it.tier) it.step = 0;
    });
    if (act === 'mats'){
      var matRe = /(固源岩|异铁|聚酸酯|糖|酮凝集|装置|溶剂|纤维|合金|原液|预制体|吸聚体|凝晶|数据增补|芯片|RMA70|研磨石|轻锰矿|扭转醇)/;
      items.forEach(function(it){
        it.want = (it.qty !== Infinity) && matRe.test(it.name);
        if (it.tier) it.step = 0;
      });
    }
    if (act === 'clearDone') items.forEach(function(it){
      it.done = 0;
      if (it.tier) it.doneStep = 0;
    });
    if (act === 'reset'){
      if (!confirm('清空所有勾选和填写内容，恢复到刚打开时的样子？')) return;
      resetAll();
      return;
    }
    renderShop(); recalc();
  });
});

document.getElementById('bAll').addEventListener('click', function(){
  // 没开放的一律不勾，免得算出一个拿不到的进度
  bonusState.forEach(function(b){ if (b.token !== null && b.open !== false) b.on = true; }); renderBonus(); recalc();
});
document.getElementById('bNone').addEventListener('click', function(){
  bonusState.forEach(function(b){ b.on = false; }); renderBonus(); recalc();
});

function clampHave(){
  var el = document.getElementById('haveToken');
  var v = Math.floor(num(el.value));
  if (!isFinite(v) || v < 0) v = 0;
  if (String(el.value) !== String(v)) el.value = v;
  recalc();
}
document.getElementById('haveToken').addEventListener('input', clampHave);
document.getElementById('haveToken').addEventListener('blur', clampHave);

/* ---------- 导入 ---------- */
function applyData(newData, quiet){
  if (newData && newData.theme !== undefined) DATA.theme = newData.theme;
  var oldTitle = DATA && DATA.activity ? DATA.activity.title : '';
  noteActivitySwitch((newData.activity || {}).title);
  DATA = newData;
  applyTheme();
  var switched = oldTitle && oldTitle !== DATA.activity.title;
  buildItems();
  buildBonus();
  renderMeta();
  renderNotice();
  renderShop();
  recalc();
  if (switched && !quiet){
    toast('已换成「' + (DATA.activity.name || DATA.activity.title) + '」，上一个活动的勾选和数量不通用，已经清空');
  } else if (!quiet){
    toast('已载入：' + (DATA.activity.name || DATA.activity.title));
  }
}

/* ---------- 更新活动数据 ---------- */
var REPO = '__REPO__';   // 数据托管仓库，形如 用户名/仓库名；留空则只用本地服务
function apiBase(){
  // 用本地服务打开时同源；直接双击 HTML 打开时指向默认端口
  return (location.protocol === 'file:') ? 'http://127.0.0.1:8765' : '';
}
/* 远程数据：脚本标签不受跨域限制，直接拉活动数据.js 覆盖 window.__ACTIVITY_DATA__ */
function remoteSources(){
  if (!REPO || REPO.indexOf('__') === 0) return [];
  var t = '?t=' + Date.now();
  return [
    'https://cdn.jsdelivr.net/gh/' + REPO + '@main/活动数据.js' + t,
    'https://raw.githubusercontent.com/' + REPO + '/main/活动数据.js' + t
  ];
}
function loadScript(url, timeout){
  return new Promise(function(resolve, reject){
    var s = document.createElement('script');
    var done = false;
    var timer = setTimeout(function(){ if (!done){ done = true; s.remove(); reject(new Error('timeout')); } }, timeout || 6000);
    s.src = url;
    s.onload = function(){ if (!done){ done = true; clearTimeout(timer); resolve(); } };
    s.onerror = function(){ if (!done){ done = true; clearTimeout(timer); s.remove(); reject(new Error('error')); } };
    document.head.appendChild(s);
  });
}
function fetchRemote(){
  var list = remoteSources();
  if (!list.length) return Promise.reject(new Error('no repo'));
  return list.reduce(function(p, url){
    return p.catch(function(){
      return loadScript(url, 6000).then(function(){
        if (!window.__ACTIVITY_DATA__) throw new Error('empty');
      });
    });
  }, Promise.reject(new Error('start')));
}
function reloadData(silent){
  var btn = document.getElementById('btnReload');
  var old = btn ? btn.textContent : '';
  if (btn && !silent){ btn.disabled = true; btn.textContent = '同步中…'; }
  function finish(msg){
    if (btn){ btn.disabled = false; btn.textContent = old; }
    if (msg) toast(msg);
  }
  var name = (DATA.activity && (DATA.activity.title || DATA.activity.name)) || '';
  // 第一优先：本地服务直接去 wiki 抓最新的
  fetch(apiBase() + '/api/update?name=' + encodeURIComponent(name))
    .then(function(r){ return r.json(); })
    .then(function(j){
      if (!j || !j.ok) throw new Error('bad');
      applyData(j.data, silent);
      setSyncState('', '');
      finish(silent ? '' : '已从 wiki 更新，用时 ' + (j.seconds || '?') + ' 秒');
    })
    .catch(function(){
      // 第二优先：从线上仓库拉已经生成好的数据
      return fetchRemote().then(function(){
        var d = window.__ACTIVITY_DATA__;
        if (!d || !d.shop || !d.activity) throw new Error('bad');
        // 线上那份要是比手里这份还旧，就别拿它覆盖（比如刚在本地重新抓过、还没上传）
        var dB = parseDT(d.built), cB = parseDT(DATA.built);
        if (dB && cB && dB <= cB){
          setSyncState('', '');
          return finish(silent ? '' : '线上数据还是 ' + (d.built || '旧的') + '，比本地这份旧，已保留本地数据');
        }
        applyData(d, silent);
        setSyncState('', '');
        finish(silent ? '' : '已同步到 ' + (d.built || '最新数据'));
      });
    })
    .catch(function(){
      // 裸双击打开、又没配任何数据源时，连不上属于常态，不弹警告
      var hasSource = (location.protocol !== 'file:') || (REPO && REPO.indexOf('__') !== 0);
      if (hasSource) setSyncState('warn', '连不上数据源，仍在用 ' + (DATA.built || '旧') + ' 的数据');
      finish(silent ? '' : '同步失败：本地服务和线上数据都连不上');
    });
}
function setSyncState(kind, text){
  var el = document.getElementById('warnIcon');
  if (!el) return;
  if (kind){
    el.classList.add('on');
    el.setAttribute('data-tip', text || '数据同步异常');
    el.setAttribute('aria-label', text || '数据同步异常');
  } else {
    el.classList.remove('on');
    el.removeAttribute('data-tip');
    el.setAttribute('aria-label', '数据同步正常');
  }
}
document.getElementById('btnReload').addEventListener('click', function(){ reloadData(false); });

/* ---------- 定时轮询：每 10 分钟静默看一次远程数据 ---------- */
var POLL_MS = 10 * 60 * 1000;
var _polling = false;
function pollRemote(){
  if (_polling || document.hidden) return;
  if (!remoteSources().length) return;          // 没配仓库就不轮询
  _polling = true;
  fetchRemote().then(function(){
    _polling = false;
    var d = window.__ACTIVITY_DATA__;
    if (!d || !d.shop || !d.activity) return;
    if (d.built && d.built === DATA.built) return;   // 数据没变，什么都不做
    var nm = d.activity.name || d.activity.title || '';
    applyData(d, true);
    pushNotice({
      id: 'poll:' + (d.built || String(Date.now())),
      act: d.activity.title || '',
      kind: 'info',
      k: '数据',
      t: '已自动更新到最新',
      b: '页面数据已经换成了 ' + (d.built || '最新') + ' 抓的版本。'
    });
    renderNotices(collectNotices());
    toast('检测到新数据，已自动更新');
  }).catch(function(){ _polling = false; });
}
setInterval(pollRemote, POLL_MS);
document.addEventListener('visibilitychange', function(){
  if (!document.hidden) pollRemote();          // 切回页面时顺手看一眼
});

document.getElementById('btnImport').addEventListener('click', function(){
  document.getElementById('fileInput').click();
});
document.getElementById('fileInput').addEventListener('change', function(e){
  var f = e.target.files[0];
  if (!f) return;
  var rd = new FileReader();
  rd.onload = function(){
    try {
      var d = JSON.parse(rd.result);
      if (!d.shop || !d.activity) throw new Error('格式不对');
      applyData(d);
    } catch(err){ toast('读取失败：' + err.message); }
  };
  rd.readAsText(f, 'utf-8');
  e.target.value = '';
});

document.getElementById('btnRefresh') && document.getElementById('btnRefresh').addEventListener('click', function(){
  location.reload();
});

/* ---------- 启动 ---------- */
applyTheme();
buildItems();
buildBonus();
renderMeta();
renderNotice();
loadState();
renderBonus();
renderShop();
recalc();
setInterval(renderNotice, 60000);   // 每分钟刷新剩余理智与倒计时
// 黄点只表示「同步真的失败了」。数据新旧由顶部提示负责，这里不再挂黄点。
// 打开后静默同步一次：本地服务或线上仓库有新数据就换上，失败就沿用内嵌这份
setTimeout(function(){
  var dirty = items.some(function(it){
    return (it.step !== undefined && (it.step > 0 || it.doneStep > 0)) || it.want || it.done > 0;
  });
  if (dirty) return;
  reloadData(true);
}, 1500);
/* ---------- 新阶段开放但数据没更新时的提醒 ---------- */
var FORCE_SYNC_POPUP = false;       // 调试开关，发布版固定 false
function phaseHasData(nm){
  // 该阶段里的关卡有没有出现在「可刷常规掉落」列表里
  var codes = (DATA.oneTime || []).filter(function(o){
    return o.kind === 'stage' && o.phase === nm;
  }).map(function(o){ return String(o.name || '').split(' ')[0]; });
  if (!codes.length) return false;
  return codes.some(function(c){
    return (DATA.stages || []).some(function(s){
      return s.code === c && s.regular && s.token > 0;
    });
  });
}
function firstStageCode(){
  var o = (DATA.oneTime || []).filter(function(x){ return x.kind === 'stage'; })[0];
  if (o && o.name) return String(o.name).split(' ')[0];
  return '第一个关卡';
}
function staleKind(){
  var phases = DATA.phases || [];
  var now = Date.now();
  var started = parseDT(DATA.activity.start);

  // 调试：'newact' 演示第一套，'phase' 演示第二套，false 走真实判断
  if (FORCE_SYNC_POPUP === 'newact') return { type: 'newact' };

  // 第一套：活动已经开了，但页面里一个能刷的关卡都没有 → 大活动更新
  var anyStage = (DATA.stages || []).some(function(s){ return s.regular && s.token > 0; });
  if (!anyStage && started && now >= started) return { type: 'newact' };

  // 第二套：从最后一个阶段往前找，报最新的那个
  // （抓数据是全量抓，更新最新的一次，前面缺的会一并补上）
  for (var i = phases.length - 1; i >= 0; i--){
    if (FORCE_SYNC_POPUP !== 'phase'){
      var t = parseDT(phases[i].start);
      if (!t || now < t) continue;
    }
    if (!phaseHasData(phases[i].name)) return { type: 'phase', name: phases[i].name };
  }
  return null;
}
function openModal(){
  var m = document.getElementById('modal');
  if (m) m.classList.add('on');
}
function closeModal(){
  var m = document.getElementById('modal');
  if (m) m.classList.remove('on');
}
function showSyncModal(forceType, forceName){
  var info = forceType ? {type: forceType, name: forceName || ''} : staleKind();
  if (!info){ closeModal(); return false; }
  var line1 = document.getElementById('modalLine1');
  var t1    = document.getElementById('modalTitle');
  var title = DATA.activity.title || '当前活动';

  if (info.type === 'newact'){
    var p0 = (DATA.phases || [])[0] || {};
    var nm0 = p0.name || firstStageCode();
    var st0 = p0.start || DATA.activity.start || '—';
    var dl = document.getElementById('modalDl');
  if (dl){
    var rp2 = (typeof REPO === 'string' && REPO && REPO.indexOf('__') !== 0) ? REPO : '';
    dl.innerHTML = rp2
      ? '去 <a href="https://github.com/' + rp2 + '/blob/main/' +
        encodeURIComponent('活动数据.json') + '" target="_blank" rel="noopener">仓库页面</a>' +
        ' 下载 <code>活动数据.json</code>，再选中这个文件。'
      : '去项目仓库下载 <code>活动数据.json</code>，再选中这个文件。';
  }
  if (t1) t1.innerHTML = 'SideStory「' + title + '」现已开启 · <b>请更新数据</b>';
    if (line1) line1.innerHTML = '剧情关卡「<b>' + nm0 + '</b>」的开放时间是 <b>' + st0 + '</b>，现已开启。';
  } else {
    var hit = (DATA.phases || []).filter(function(x){ return x.name === info.name; })[0];
    if (t1) t1.innerHTML = 'SideStory「' + title + '」<b>新关卡开启</b>';
    if (line1) line1.innerHTML = '关卡「<b>' + info.name + '</b>」现已开启，开放时间 <b>' +
      (hit ? hit.start : '—') + '</b>。';
  }
  if (line1){ line1.style.display = ''; line1.classList.add('flashline'); }
  var _sb = document.getElementById('modalSteps');
  var _gb = document.getElementById('modalGeneric');
  if (_sb) _sb.style.display = '';
  if (_gb) _gb.style.display = 'none';
  // 取列表里那条通知的真实 id（可能是 act: / first: / phase: 三种之一）
  var _k = (info.type === 'phase') ? 'phase' : 'act';
  var _c = collectNotices().filter(function(n){ return n.kind === _k; })[0];
  window._curNoticeId = _c ? _c.id : '';
  openModal();
  refreshModalNext();
  return true;
}
/* 大弹窗底部「下一条」：还有没读的就显示，点了一条条看完 */
function refreshModalNext(){
  var btn = document.getElementById('modalNext');
  if (!btn) return;
  var read = _readIds();
  var un = collectNotices().filter(function(n){ return read.indexOf(n.id) < 0; });
  // 当前这条正在弹，剩下的是它之外还没读的
  var cur = window._curNoticeId || '';
  var left = un.filter(function(n){ return n.id !== cur; }).length;
  btn.style.display = un.length ? '' : 'none';
  btn.textContent = left > 0 ? ('下一条（还有 ' + left + ' 条）') : '下一条';
}
setTimeout(function(){
  if (typeof collectNotices !== 'function') return;
  var read = _readIds();
  var un = collectNotices().filter(function(n){ return read.indexOf(n.id) < 0; });
  if (!un.length) return;
  var n0 = un[0];
  if (n0.kind === 'act' || n0.kind === 'phase'){
    showSyncModal(n0.kind === 'phase' ? 'phase' : 'newact', n0.nm || '');
  } else {
    openNoticeDetail(n0);
  }
}, 2600);


/* ---------- 通知 ---------- */
var NOTICE_READ = 'ark_read_notice', NOTICE_WELCOME = 'ark_welcomed';
function _ls(k, v){
  try{
    if (v === undefined) return localStorage.getItem(k);
    localStorage.setItem(k, v);
  }catch(e){}
  return null;
}
function _readIds(){
  try{ return JSON.parse(_ls(NOTICE_READ) || '[]'); }catch(e){ return []; }
}
function purgeOldNotes(){
  try{
    var arr = JSON.parse(localStorage.getItem('ark_notices') || '[]');
    var keep = arr.filter(function(x){ return !/^newact:/.test(String(x.id)); });
    if (keep.length !== arr.length){
      localStorage.setItem('ark_notices', JSON.stringify(keep));
    }
  }catch(e){}
}
function _storedNotes(){
  try{ return JSON.parse(localStorage.getItem('ark_notices') || '[]'); }catch(e){ return []; }
}
function pushNotice(n){
  if (!n || !n.id) return;
  var list = _storedNotes();
  if (list.some(function(x){ return x.id === n.id; })) return;
  list.push({id: n.id, act: n.act || '', kind: n.kind || 'tip',
             k: n.k || '通知', t: n.t || '', b: n.b || '',
             nm: n.nm || '', at: Date.now()});
  if (list.length > 24) list = list.slice(-24);
  try{ localStorage.setItem('ark_notices', JSON.stringify(list)); }catch(e){}
}
function noteActivitySwitch(newTitle){
  if (!newTitle) return;
  try{ localStorage.setItem('ark_notice_act', JSON.stringify({name: newTitle, at: Date.now()})); }catch(e){}
}
function collectNotices(){
  var out = [];
  var curAct = (DATA.activity && DATA.activity.title) || '';
  // 弹过又关掉的，都留在这儿
  _storedNotes().forEach(function(x){
    if (/^newact:/.test(String(x.id))) return;   // 旧版本留下的重复通知，直接丢
    if (x.act && x.act !== curAct) return;       // 只留当前活动的
    out.push(x);
  });
  // 同步时发现活动换了，记一条
  var sw = null;
  try{ sw = JSON.parse(localStorage.getItem('ark_notice_act') || 'null'); }catch(e){}
  var title0 = (DATA.activity && DATA.activity.title) || '';
  // 先判断这次是不是「活动开了但数据还旧」，是的话只留那一条，不重复报「活动已开启」
  var info0 = (typeof staleKind === 'function') ? staleKind() : null;
  // 这个活动是第一次见：记一条，之后不再重复
  if (title0 && !(info0 && info0.type === 'newact')){
    var seen = [];
    try{ seen = JSON.parse(localStorage.getItem('ark_seen_act') || '[]'); }catch(e){}
    if (seen.indexOf(title0) < 0){
      seen.push(title0);
      try{ localStorage.setItem('ark_seen_act', JSON.stringify(seen)); }catch(e){}
      pushNotice({id: 'first:' + title0, act: title0, kind: 'act', k: '活动',
        t: '活动已开启',
        b: '「' + title0 + '」的数据已经载入。想确认是不是最新的，点击「同步最新数据」按钮再取一次。'});
    }
  }
  var info = (typeof staleKind === 'function') ? staleKind() : null;
  var title = (DATA.activity && DATA.activity.title) || '活动';
  if (info && info.type === 'newact'){
    pushNotice({id: 'act:' + title, act: title, kind: 'act', k: '活动',
      t: '新活动已开启',
      b: '「' + title + '」已经开放了，但页面里的数据可能还是旧的。点击「同步最新数据」按钮，最新的商店和关卡才会进来。'});
    out.push({id: 'act:' + title, kind: 'act', k: '活动',
      t: '新活动已开启',
      b: '「' + title + '」已经开放了，但页面里的数据可能还是旧的。点击「同步最新数据」按钮，最新的商店和关卡才会进来。'});
  } else if (info && info.type === 'phase'){
    pushNotice({id: 'phase:' + info.name, act: title, kind: 'phase', nm: info.name, k: '新关卡',
      t: '新关卡已开启',
      b: '「' + info.name + '」已经开放。点击「同步最新数据」按钮，新关卡的掉落数据才会进来，否则算出来的结果会偏小。'});
    out.push({id: 'phase:' + info.name, kind: 'phase', k: '新关卡',
      t: '新关卡已开启',
      b: '「' + info.name + '」已经开放。点击「同步最新数据」按钮，新关卡的掉落数据才会进来，否则算出来的结果会偏小。'});
  }
  {
    var rp = (typeof REPO === 'string' && REPO && REPO.indexOf('__') !== 0) ? REPO : '';
    var wb = '';
    if (rp){
      wb = '项目地址：<a href="https://github.com/' + rp +
           '" target="_blank" rel="noopener">github.com/' + rp + '</a>';
      wb += '<br>发现问题：<a href="https://github.com/' + rp +
            '/issues" target="_blank" rel="noopener">去提一个 issue</a>';
    } else {
      wb = '项目地址与反馈入口会在正式发布后补上。';
    }
    out.push({id: 'welcome', kind: 'welcome', k: '提示', t: '第一次来？', b: wb});
  }
  var seen = {}, uniq = [];
  out.forEach(function(n){ if (!seen[n.id]){ seen[n.id] = 1; uniq.push(n); } });
  // 同一个活动里，「act:」与「first:」讲的是同一件事，只留 act:
  var hasAct = uniq.some(function(n){ return /^act:/.test(String(n.id)); });
  if (hasAct) uniq = uniq.filter(function(n){ return !/^first:/.test(String(n.id)); });
  return uniq;
}
function renderNotices(list){
  var body = document.getElementById('npBody');
  var dot = document.getElementById('ndot');
  if (!body) return;
  var read = _readIds();
  var unread = list.filter(function(n){ return read.indexOf(n.id) < 0; }).length;
  if (dot) dot.className = 'ndot' + (unread ? ' on' : '');
  if (!list.length){
    body.innerHTML = '<div class="nempty">暂时没有新通知</div>';
    return;
  }
  body.innerHTML = list.map(function(n, i){
    var un = read.indexOf(n.id) < 0;
    return '<div class="nitem ' + n.kind + (un ? ' unread' : '') + '" data-i="' + i + '" tabindex="0">' +
      '<div class="nt2"><span class="nk">' + n.k + '</span>' + n.t +
      (un ? '<span class="nun">未读</span>' : '') + '</div>' +
      '<div class="nb">' + (function(){
        var plain = String(n.b).replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').trim();
        return plain.slice(0, 46) + (plain.length > 46 ? '…' : '');
      })() + '</div></div>';
  }).join('');
  window._noticeList = list;
  body.querySelectorAll('.nitem').forEach(function(el){
    el.addEventListener('click', function(){
      openNoticeItem(window._noticeList[+el.getAttribute('data-i')]);
    });
    el.addEventListener('keydown', function(e){
      if (e.key === 'Enter' || e.key === ' '){
        e.preventDefault();
        openNoticeItem(window._noticeList[+el.getAttribute('data-i')]);
      }
    });
  });
}
function openNoticeItem(n){
  if (!n) return;
  closeNotice();
  if (n.kind === 'act' || n.kind === 'phase'){
    showSyncModal(n.kind === 'phase' ? 'phase' : 'newact', n.nm || '');
  } else {
    openNoticeDetail(n);
  }
}
function openNotice(force){
  var p = document.getElementById('np');
  var btn = document.getElementById('notifyBtn');
  if (!p) return;
  var list = collectNotices();
  renderNotices(list);
  p.classList.add('on');
  if (btn) btn.classList.add('on');
}
function closeNotice(){
  var p = document.getElementById('np');
  var btn = document.getElementById('notifyBtn');
  if (p) p.classList.remove('on');
  if (btn) btn.classList.remove('on');
}

function markReadOne(id){
  var read = _readIds();
  if (read.indexOf(id) < 0){
    read.push(id);
    _ls(NOTICE_READ, JSON.stringify(read));
  }
  renderNotices(collectNotices());
}
function openNoticeDetail(n){
  markReadOne(n.id);
  window._curNoticeId = n.id;
  var tt = document.getElementById('modalTitle');
  var l1 = document.getElementById('modalLine1');
  var sb = document.getElementById('modalSteps');
  var gb = document.getElementById('modalGeneric');
  if (tt) tt.innerHTML = '<span class="nk" style="display:inline-block;margin-right:8px">' +
    n.k + '</span>' + n.t;
  if (l1){ l1.style.display = 'none'; l1.innerHTML = ''; l1.classList.remove('flashline'); }
  if (sb) sb.style.display = 'none';
  if (gb){ gb.style.display = ''; gb.innerHTML = '<p>' + n.b + '</p>'; }
  closeNotice();
  openModal();
  refreshModalNext();
}
function closeNoticeDetail(){
  closeModal();
}
function initNotify(){
  purgeOldNotes();
  var btn = document.getElementById('notifyBtn');
  var close = document.getElementById('npClose');
  if (btn) btn.addEventListener('click', function(e){
    e.stopPropagation();
    var p = document.getElementById('np');
    if (p && p.classList.contains('on')) closeNotice();
    else openNotice();
  });
  if (close) close.addEventListener('click', closeNotice);
  document.addEventListener('click', function(e){
    var p = document.getElementById('np');
    if (!p || !p.classList.contains('on')) return;
    if (p.contains(e.target) || (btn && btn.contains(e.target))) return;
    closeNotice();
  });
  document.addEventListener('keydown', function(e){
    if (e.key === 'Escape') closeNotice();
  });
  var nmask = document.getElementById('nmask');
  var nOk = document.getElementById('nOk');
  var nSync = document.getElementById('nSync');
  if (nmask) nmask.addEventListener('click', closeNoticeDetail);
  if (nOk) nOk.addEventListener('click', closeNoticeDetail);
  if (nSync) nSync.addEventListener('click', function(){
    closeNoticeDetail();
    var b = document.getElementById('btnReload');
    if (b) b.click();
  });
  renderNotices(collectNotices());
}

function bindModal(){
  var c = document.getElementById('modalClose');
  if (c) c.addEventListener('click', function(){
    if (window._curNoticeId){
      markReadOne(window._curNoticeId);   // 大弹窗点知道了也算读过
      window._curNoticeId = '';
    }
    closeModal();
  });
  var nx = document.getElementById('modalNext');
  if (nx) nx.addEventListener('click', function(){
    if (window._curNoticeId){
      markReadOne(window._curNoticeId);
      window._curNoticeId = '';
    }
    var read = _readIds();
    var un = collectNotices().filter(function(n){ return read.indexOf(n.id) < 0; });
    if (!un.length){ closeModal(); return; }
    var n = un[0];
    if (n.kind === 'act' || n.kind === 'phase'){
      showSyncModal(n.kind === 'phase' ? 'phase' : 'newact', n.nm || '');
    } else {
      openNoticeDetail(n);
    }
  });
  var m = document.getElementById('modalMask');
  if (m) m.addEventListener('click', function(){
    if (window._curNoticeId){
      markReadOne(window._curNoticeId);
      window._curNoticeId = '';
    }
    closeModal();
  });
}
document.addEventListener('keydown', function(e){
  if (e.key === 'Escape') closeModal();
});
</script>

<div class="modal" id="modal">
  <div class="mmask" id="modalMask"></div>
  <div class="mbox" role="dialog" aria-modal="true" aria-labelledby="modalTitle">
    <div class="mtt" id="modalTitle">SideStory「时间啊，向前！」<b>新关卡开启</b></div>
    <div class="mbody">
      <p id="modalLine1">关卡「<b id="modalPhase">—</b>」现已开启，开放时间 <b id="modalWhen">—</b>。</p>
      <div id="modalSteps">
      <p class="mstep"><span class="mn">1</span>请点击<b>「同步最新数据」</b>按钮，更新数据。</p>
      <p class="mstep"><span class="mn">2</span>若更新数据失败，请点击<b>「导入本地文件」</b>手动更新：<span id="modalDl">去项目仓库下载 <code>活动数据.json</code>，再选中这个文件。</span></p>
      <p class="mignore">如果页面上的数据已经是最新的，忽略这条提醒。</p>
      <p>若都无法更新成功，请等待网站作者更新数据，或前往仓库下载完整文件运行脚本。</p>
      <p class="mnote">运行 .py 需要先装 Python，安装时务必勾选「Add Python to PATH」。
        <a href="https://www.python.org/downloads/" target="_blank" rel="noopener">下载 Python</a> ·
        <a href="https://www.runoob.com/python3/python3-install.html" target="_blank" rel="noopener">中文安装教程</a>
      </p>
      </div>
      <div id="modalGeneric" style="display:none"></div>
    </div>
    <div class="mact">
      <button id="modalNext" style="display:none">下一条</button>
      <button id="modalClose">知道了</button>
    </div>
  </div>
</div>
<script>bindModal();initNotify();</script>
</body>
</html>
'''

html = HTML.replace('__NAME__', data['activity'].get('name') or data['activity']['title'])
html = html.replace('__TOKEN__', data.get('token') or '代币')
html = html.replace('__PAYLOAD__', payload)
html = html.replace('__REPO__', repo)
html = html.replace('__OGURL__', og_url)
html = html.replace('__SITEURL__', site_url)

out = os.path.join(BASE, 'index.html')
with open(out, 'w', encoding='utf-8') as f:
    f.write(html)
say('written:', out, len(html), 'chars')

# 老版本会同时生成一份中文名的副本，现在不再生成；若还存在就一并删除
_stale = os.path.join(BASE, '活动代币计算器.html')
if os.path.exists(_stale):
    try:
        os.remove(_stale)
    except OSError:
        pass
