# -*- coding: utf-8 -*-
"""把 PRTS wiki 上所有 SideStory 活动的数据抓下来，一个活动存一个文件。

用法：
    python 打包全部活动.py

产物：同目录下的「活动存档」文件夹，里面每个活动一个 json，
文件名就是活动名，内容与「活动数据.json」格式完全一致（含商品图标）。

中途按 Ctrl+C 随时能停，下次再跑会跳过已有文件，接着往下抓。
想重新抓某个活动，把它的 json 删掉再跑即可。
"""
import datetime
import importlib.util
import io
import json
import os
import re
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
# 三个脚本平时放在「工具」子目录里，工作目录要提到上一级（页面、数据都那儿）
BASE = os.path.dirname(_HERE) if os.path.basename(_HERE) == '工具' else _HERE
OUT_DIR = os.path.join(BASE, '活动存档')
MOD_PATH = os.path.join(_HERE, '更新活动数据.py')

# Windows 文件名里不能出现的字符
_BAD = re.compile(r'[\\/:*?"<>|]')


def _fix_console():
    """把控制台和 Python 都改成 UTF-8，避免中文在 cmd 里变成方块。

    只改 Python 的输出编码不够——cmd 自己的代码页还停在 GBK 时，
    它会把 UTF-8 的字节按 GBK 解释，照样是乱码。所以两边一起改。
    这个函数必须在「更新活动数据.py」加载之后调用，否则会被它设回 GBK。
    """
    if os.name == 'nt':
        try:
            import ctypes
            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
            ctypes.windll.kernel32.SetConsoleCP(65001)
        except Exception:
            pass
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


def load_mod():
    """「更新活动数据.py」是中文名，普通 import 用不了，走 importlib。"""
    if not os.path.exists(MOD_PATH):
        raise SystemExit('找不到「更新活动数据.py」，请把它和本脚本放同一目录。')
    spec = importlib.util.spec_from_file_location('arkfetch', MOD_PATH)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _fmt_span(sec):
    if sec < 60:
        return '%d 秒' % sec
    if sec < 3600:
        return '%d 分钟' % (sec // 60)
    return '%d 小时 %d 分' % (sec // 3600, (sec % 3600) // 60)


def safe_name(s):
    return _BAD.sub('_', str(s)).strip().rstrip('.') or '未命名'


def main():
    mod = load_mod()
    _fix_console()
    print('正在向 wiki 取活动列表…')
    acts = mod.list_activities(limit=500)
    if not acts:
        print('没取到活动列表，检查网络后重试。')
        return 1

    if not os.path.isdir(OUT_DIR):
        os.makedirs(OUT_DIR)
        print('已创建文件夹：' + OUT_DIR)

    todo = []
    for a in acts:
        p = os.path.join(OUT_DIR, safe_name(a['short']) + '.json')
        if not os.path.exists(p):
            todo.append(a)

    print('活动总数 %d，已有 %d，本次要抓 %d 个。'
          % (len(acts), len(acts) - len(todo), len(todo)))
    if not todo:
        print('已经全部抓过了，不用再跑。')
        print('文件夹：' + OUT_DIR)
        return 0

    # 每个活动带图标约 120 KB，先按这个估个总量给用户看
    est_mb = len(todo) * 0.12
    est_min = len(todo) * 0.4
    print()
    print('-' * 56)
    print('  即将开始抓取')
    print('-' * 56)
    print('  抓取范围：过往全部活动，本次 %d 个' % len(todo))
    print('  存放位置：本文件夹下的「活动存档」')
    print('  预计大小：约 %.0f MB（每个活动一个 json，带商品图标）' % est_mb)
    print('  预计耗时：约 %.0f 分钟（每个 20~30 秒）' % est_min)
    print('  中途可随时按 Ctrl+C 停止，已抓完的会保留')
    print('-' * 56)
    print()
    try:
        ans = input('按回车开始，输入 n 取消：').strip().lower()
    except (EOFError, KeyboardInterrupt):
        print('\n已取消。')
        return 0
    if ans in ('n', 'no', 'q', 'quit'):
        print('已取消，什么都没抓。')
        return 0
    print()

    t0 = time.time()
    ok = 0
    fail = []
    for i, a in enumerate(todo, 1):
        name = a['short']
        print()
        print('── [%d/%d] %s ──' % (i, len(todo), name))
        try:
            data = mod.build(a['page'])
        except KeyboardInterrupt:
            print('\n手动中断。已抓到的都存好了，下次接着来。')
            return 0
        except SystemExit:
            print('  跳过：这个活动没有标准商店，算不了。')
            fail.append(name)
            continue
        except Exception as e:
            print('  失败：%s' % e)
            fail.append(name)
            continue

        data['built'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
        p = os.path.join(OUT_DIR, safe_name(name) + '.json')
        tmp = p + '.tmp'
        with io.open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        os.replace(tmp, p)
        ok += 1
        print('  已存 %s（%.0f KB）' % (os.path.basename(p), os.path.getsize(p) / 1024.0))

    print()
    print('完成：本次抓到 %d 个，跳过 %d 个，用时 %.1f 分钟。'
          % (ok, len(fail), (time.time() - t0) / 60))
    if fail:
        print('没抓成的：' + '、'.join(fail))
        print('（大多是老活动没有标准商店，属于正常）')
    print('文件夹：' + OUT_DIR)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print('\n已中断。')
        sys.exit(0)
