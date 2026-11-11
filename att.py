# -*- coding: utf-8 -*-
"""att - 一条命令直达 Spectrum 的 Attendance 页面（最后勾选 Present 并提交，仍由你自己在网页上完成）。

准备工作:
  1. 把本脚本和 token.txt 放在同一个文件夹。
  2. token.txt 内容: 只写一行就是 token 本身；
     想用别的 Moodle 站点，就写两行，第一行站点地址，第二行 token。
  3. 运行: python att.py sync   抓取所有未结束课程、且对你可见的 Attendance 页面。

日常使用:
  python att.py             只显示"现在正在上"的课，直接回车进入
  python att.py <关键词>     按名字模糊匹配并打开，例如 python att.py hsm

设置上课时间（一个活动可以设多个时间，比如一周上两次）:
  python att.py sched <序号或关键词> <mon..sun> <HH:MM>    添加一个时间
  python att.py unsched <序号或关键词> <mon..sun> <HH:MM>  删除其中一个时间
  python att.py unsched <序号或关键词> all                 清空这门课的所有时间

其他:
  python att.py list
  python att.py add <名字> <url>      手动补一个，例如 .../mod/attendance/view.php?id=1126419
  python att.py rm <序号或关键词>
"""
import argparse
import json
import re
import sys
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

SCRIPT_DIR = Path(__file__).resolve().parent
TOKEN_FILE = SCRIPT_DIR / "token.txt"
CFG = SCRIPT_DIR / ".att.json"
DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
DEFAULT_SITE = "https://spectrum.um.edu.my"


def load_auth():
    """每次运行都重新读取 token.txt，不缓存，改了 token 立刻生效。"""
    if not TOKEN_FILE.exists():
        sys.exit(f"找不到 {TOKEN_FILE.name}，请在脚本同目录下创建它，内容是你的 token。")
    lines = [l.strip() for l in TOKEN_FILE.read_text(encoding="utf-8").splitlines() if l.strip()]
    if not lines:
        sys.exit(f"{TOKEN_FILE.name} 是空的。")
    if len(lines) == 1:
        return {"site": DEFAULT_SITE, "token": lines[0]}
    return {"site": lines[0].rstrip("/"), "token": lines[1]}


def load_cfg():
    try:
        d = json.loads(CFG.read_text(encoding="utf-8"))
    except FileNotFoundError:
        d = {}
    d.setdefault("classes", {})
    for e in d["classes"].values():
        if "times" not in e:
            # 兼容旧版本：旧格式是单个 day/time，迁移成列表
            old_day, old_time = e.pop("day", None), e.pop("time", None)
            e["times"] = [{"day": old_day, "time": old_time}] if old_day and old_time else []
        e.setdefault("times", [])
    return d


def save_cfg(d):
    CFG.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")


def ws(auth, fn, **params):
    q = urlencode({"wstoken": auth["token"], "wsfunction": fn,
                   "moodlewsrestformat": "json", **params})
    with urlopen(f"{auth['site']}/webservice/rest/server.php?{q}", timeout=15) as r:
        out = json.load(r)
    if isinstance(out, dict) and "exception" in out:
        raise RuntimeError(f"{fn}: {out.get('message') or out['exception']}")
    return out


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def cmd_sync(d):
    auth = load_auth()
    info = ws(auth, "core_webservice_get_site_info")
    now = datetime.now().timestamp()
    n = 0
    skipped = 0
    for c in ws(auth, "core_enrol_get_users_courses", userid=info["userid"]):
        end = c.get("enddate") or 0
        if end and end < now:  # 跳过已经结束的课程
            continue
        try:
            sections = ws(auth, "core_course_get_contents", courseid=c["id"])
        except RuntimeError as e:
            print(f"跳过 {c.get('shortname')}: {e}")
            continue
        for s in sections:
            for m in s.get("modules", []):
                if m.get("modname") != "attendance" or not m.get("url"):
                    continue
                if m.get("uservisible") is False:
                    # 对我不可见/不可用的活动，比如分组限制（截图里那种 "Not available unless..."）
                    skipped += 1
                    continue
                key = slug(f"{c['shortname']}-{m['name']}")
                old_times = d["classes"].get(key, {}).get("times", [])
                d["classes"][key] = {
                    "url": m["url"],
                    "title": m["name"],  # 直接用 Moodle 上的活动名字，如截图里那种
                    "times": old_times,  # 已设置的上课时间保留，不会被同步清空
                }
                n += 1
    save_cfg(d)
    extra = f"（另有 {skipped} 个对你不可用的已跳过）" if skipped else ""
    print(f"同步完成，共 {n} 个 Attendance 页面。{extra}")


def ordered(d):
    return list(d["classes"].items())


def fmt_times(e):
    return ", ".join(f"{t['day']} {t['time']}" for t in e.get("times", []))


def show_numbered(items, marks=None):
    marks = marks or {}
    for i, (k, e) in enumerate(items, 1):
        when = f"  [{fmt_times(e)}]" if e.get("times") else ""
        flag = marks.get(k, "")
        print(f"{flag}{i}. {e['title']}{when}")


def current_matches(items):
    now = datetime.now()
    today = DAYS[now.weekday()]
    hits = []
    for k, e in items:
        for t in e.get("times", []):
            if t.get("day") != today or not t.get("time"):
                continue
            h, m = map(int, t["time"].split(":"))
            start = now.replace(hour=h, minute=m, second=0, microsecond=0)
            if start - timedelta(minutes=15) <= now <= start + timedelta(minutes=60):
                hits.append(k)
                break
    return hits


def open_entry(e):
    print(f"正在打开: {e['title']}")
    webbrowser.open(e["url"])


def resolve(items, token):
    """允许用序号或名字关键词定位一门课。"""
    for i, (k, e) in enumerate(items, 1):
        if token == str(i):
            return k, e
    hits = [(k, e) for k, e in items if token.lower() in k.lower() or token.lower() in e["title"].lower()]
    if len(hits) == 1:
        return hits[0]
    if len(hits) > 1:
        print(f'"{token}" 匹配到多个：')
        show_numbered(hits)
        try:
            return hits[int(input("选哪个？输入序号: ")) - 1]
        except (ValueError, IndexError):
            sys.exit("没选中。")
    return None


def interactive_default(d):
    items = ordered(d)
    if not items:
        print("还没有保存任何课。先运行: python att.py sync")
        return

    hit_keys = current_matches(items)
    current = [(k, e) for k, e in items if k in hit_keys]

    if not current:
        print("何必劳神苦思，代下司职？")
        return

    print("👑 皇上您不用排队 🙇")
    show_numbered(current)

    if len(current) == 1:
        raw = input(f"\n直接回车进入「{current[0][1]['title']}」，或输入其他序号: ").strip()
        if not raw:
            open_entry(current[0][1])
            return
    else:
        raw = input("\n请输入序号: ").strip()

    try:
        open_entry(current[int(raw) - 1][1])
    except (ValueError, IndexError):
        sys.exit("没有这个序号。")


def cmd_sched(d, rest):
    if len(rest) != 3 or rest[1] not in DAYS:
        sys.exit("用法: att sched <序号或关键词> <mon..sun> <HH:MM>")
    hit = resolve(ordered(d), rest[0])
    if not hit:
        sys.exit("找不到这门课，先用 list 看看有哪些。")
    key, e = hit
    day, time_ = rest[1], rest[2]
    if any(t["day"] == day and t["time"] == time_ for t in e["times"]):
        print(f"{e['title']} 已经有 {day} {time_} 这条了，没有重复添加。")
        return
    e["times"].append({"day": day, "time": time_})
    save_cfg(d)
    print(f"{e['title']} -> 现在的时间: {fmt_times(e)}")


def cmd_unsched(d, rest):
    if len(rest) < 2:
        sys.exit("用法: att unsched <序号或关键词> <mon..sun> <HH:MM>  或  att unsched <序号或关键词> all")
    hit = resolve(ordered(d), rest[0])
    if not hit:
        sys.exit("找不到这门课。")
    key, e = hit
    if rest[1] == "all":
        e["times"] = []
        save_cfg(d)
        print(f"{e['title']} 的所有时间都清空了。")
        return
    if len(rest) != 3 or rest[1] not in DAYS:
        sys.exit("用法: att unsched <序号或关键词> <mon..sun> <HH:MM>  或  att unsched <序号或关键词> all")
    day, time_ = rest[1], rest[2]
    before = len(e["times"])
    e["times"] = [t for t in e["times"] if not (t["day"] == day and t["time"] == time_)]
    save_cfg(d)
    if len(e["times"]) == before:
        print(f"{e['title']} 本来就没有 {day} {time_} 这条。")
    else:
        print(f"{e['title']} -> 现在的时间: {fmt_times(e) or '(空)'}")


def main():
    d = load_cfg()
    args = sys.argv[1:]

    if not args:
        interactive_default(d)
        return

    cmd, rest = args[0], args[1:]
    if cmd == "sync":
        cmd_sync(d)
    elif cmd == "list":
        show_numbered(ordered(d))
    elif cmd == "add":
        p = argparse.ArgumentParser(prog="att add")
        p.add_argument("name")
        p.add_argument("url")
        a = p.parse_args(rest)
        key = slug(a.name)
        old_times = d["classes"].get(key, {}).get("times", [])
        d["classes"][key] = {"url": a.url, "title": a.name, "times": old_times}
        save_cfg(d)
        print(f"已保存: {a.name}")
    elif cmd == "sched":
        cmd_sched(d, rest)
    elif cmd == "unsched":
        cmd_unsched(d, rest)
    elif cmd == "rm":
        if not rest:
            sys.exit("用法: att rm <序号或关键词>")
        hit = resolve(ordered(d), rest[0])
        if not hit:
            sys.exit("找不到这门课。")
        title = hit[1]["title"]
        del d["classes"][hit[0]]
        save_cfg(d)
        print(f"已删除: {title}")
    else:
        hit = resolve(ordered(d), cmd)
        if hit:
            open_entry(hit[1])
        else:
            print(f'没有匹配 "{cmd}" 的课。')
            show_numbered(ordered(d))


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        sys.exit(f"Spectrum 返回错误：{e}")
    except OSError as e:
        sys.exit(f"连接 Spectrum 失败（网络问题？）：{e}")
