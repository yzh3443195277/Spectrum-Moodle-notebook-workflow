"""
列出 UM Spectrum (Moodle) 上本学期所有课程的作业 / Quiz，按紧急程度排序。

列表分三块（序号连续，可直接操作）:
    1. 待提交      —— 还没交、deadline 没过（按 deadline 从近到远，无 deadline 的在最后）
    2. 已过期未交  —— deadline 已过但没提交
    3. 已提交      —— 已提交（迟交的会标注）

用法:
    pip install requests
    python moodle_deadlines.py              # 显示全部三块
    python moodle_deadlines.py --pending    # 只显示【待提交】
    python moodle_deadlines.py --debug      # 排查"为什么作业这么少"：打印每门课的统计
    python moodle_deadlines.py --no-open    # 只显示列表，不进入交互

token 放在同目录的 token.txt / token.text 里（只放 token 一行）。

列表出来后可以在 > 提示符下输入:
    1 3        打开序号 1、3 的页面（也可写 1,3）
    d 2 4      删除（隐藏）序号 2、4：以后运行不再出现，记录保存在 hidden_tasks.json
    r          查看已删除的任务并恢复
    l          重新显示列表
    q / 回车   退出
"""

import argparse
import json
import re
import sys
import time
import unicodedata
import webbrowser
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

# ====== 需要你确认/修改的地方 ======
BASE_URL = "https://spectrum.um.edu.my"    # UM Spectrum（不带结尾斜杠），请确认
TOKEN_FILES = ["token.txt", "token.text"]  # 依次尝试读取
TZ = timezone(timedelta(hours=8))          # 马来西亚时间 UTC+8

# 如果自动识别出来的课程不是你这学期的 7 门，
# 把脚本打印出的课程 ID 填到这里，只查这些课程，例如 [1234, 1235, ...]
INCLUDE_COURSE_IDS = []

# deadline 已经过去超过这么多天的条目不显示（不管有没有提交）。设为 None 则不过滤。
MAX_PAST_DAYS = 200
# =================================

API_URL = f"{BASE_URL}/webservice/rest/server.php"
HIDDEN_FILE = Path(__file__).resolve().parent / "hidden_tasks.json"  # 被你删除的任务记录

CAT_PENDING, CAT_OVERDUE, CAT_SUBMITTED = 1, 2, 3
CAT_TITLES = {
    CAT_PENDING: "待提交",
    CAT_OVERDUE: "已过期未交",
    CAT_SUBMITTED: "已提交",
}


# ---------- 基础工具 ----------

def load_token() -> str:
    here = Path(__file__).resolve().parent
    for name in TOKEN_FILES:
        for folder in (Path.cwd(), here):
            p = folder / name
            if p.exists():
                token = p.read_text(encoding="utf-8").strip()
                if token:
                    return token
    sys.exit(f"找不到 token 文件，请把 token 放在 {' 或 '.join(TOKEN_FILES)} 里。")


TOKEN = load_token()


def call(function: str, **params):
    """调用 Moodle Web Service。数组参数传 list，会自动展开为 key[0]=...。"""
    data = {
        "wstoken": TOKEN,
        "wsfunction": function,
        "moodlewsrestformat": "json",
    }
    for key, value in params.items():
        if isinstance(value, (list, tuple)):
            for i, v in enumerate(value):
                data[f"{key}[{i}]"] = v
        else:
            data[key] = value

    r = requests.post(API_URL, data=data, timeout=30)
    r.raise_for_status()
    result = r.json()
    if isinstance(result, dict) and "exception" in result:
        raise RuntimeError(f"{function} 失败: {result.get('message')} ({result.get('errorcode')})")
    return result


def get_assign_submission(assign_id: int):
    """返回 (状态, 提交时间戳, 个人延期后的截止时间戳)。状态: submitted/draft/new/unknown"""
    try:
        data = call("mod_assign_get_submission_status", assignid=assign_id)
    except Exception:
        return "unknown", 0, 0
    last = data.get("lastattempt") or {}
    sub = last.get("teamsubmission") or last.get("submission") or {}
    return sub.get("status", "new"), sub.get("timemodified", 0), last.get("extensionduedate", 0) or 0


def quiz_finished_time(quiz_id: int, user_id: int) -> int:
    """返回最近一次已完成 attempt 的结束时间戳；没有则 0。"""
    try:
        data = call("mod_quiz_get_user_attempts", quizid=quiz_id, userid=user_id,
                    status="finished", includepreviews=0)
    except Exception:
        return 0
    times = [a.get("timefinish", 0) for a in data.get("attempts", [])]
    return max(times) if times else 0


# ---------- 显示相关 ----------

def humanize(delta: timedelta) -> str:
    total = int(delta.total_seconds())
    overdue = total < 0
    total = abs(total)
    days, rem = divmod(total, 86400)
    hours, rem = divmod(rem, 3600)
    minutes = rem // 60
    if days:
        text = f"{days}天{hours}小时"
    elif hours:
        text = f"{hours}小时{minutes}分"
    else:
        text = f"{minutes}分钟"
    return f"已过期{text}" if overdue else text


def urgency_icon(delta) -> str:
    if delta is None:
        return "⚪"
    if delta.total_seconds() < 0:
        return "⚫"
    if delta <= timedelta(days=1):
        return "🔴"
    if delta <= timedelta(days=3):
        return "🟠"
    if delta <= timedelta(days=7):
        return "🟡"
    return "🟢"


def disp_width(s: str) -> int:
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in s)


def pad(s: str, width: int) -> str:
    return s + " " * max(0, width - disp_width(s))


def trunc(s: str, width: int) -> str:
    if disp_width(s) <= width:
        return s
    out = ""
    for ch in s:
        if disp_width(out + ch) > width - 1:
            break
        out += ch
    return out + "…"


# ---------- 被删除任务的持久化 ----------

def load_hidden() -> dict:
    """返回 {key(str): {"course":..., "name":...}}。作业的 key 是作业 id，Quiz 的 key 是 quiz-<id>。"""
    if HIDDEN_FILE.exists():
        try:
            return json.loads(HIDDEN_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            print(f"⚠️  {HIDDEN_FILE.name} 读取失败，已忽略。")
    return {}


def save_hidden(hidden: dict):
    HIDDEN_FILE.write_text(json.dumps(hidden, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------- 列表显示 ----------

def sort_key(r):
    ts = r["due"].timestamp() if r["due"] else None
    if r["cat"] == CAT_PENDING:
        return (CAT_PENDING, ts is None, ts or 0)          # 越近越靠前
    return (r["cat"], ts is None, -(ts or 0))              # 过期/已提交：最近的靠前


def print_table(rows, now, hidden_count=0):
    W_REM, W_DUE, W_COURSE, W_NAME = 16, 18, 14, 52
    pending = [r for r in rows if r["cat"] == CAT_PENDING]
    print(f"\n===== 作业 / Quiz 列表（待提交 {len(pending)} 项）=====")

    if not rows:
        print("\n没有任何条目。")
    else:
        header = (
            f"\n{pad('#', 3)}{pad('剩余时间', W_REM + 3)}{pad('截止时间', W_DUE)}"
            f"{pad('课程', W_COURSE)}作业"
        )
        print(header)
        print("-" * (disp_width(header) + 10))

        last_cat = None
        for i, r in enumerate(rows, 1):
            if r["cat"] != last_cat:
                n = sum(1 for x in rows if x["cat"] == r["cat"])
                print(f"\n【{CAT_TITLES[r['cat']]}】({n})")
                last_cat = r["cat"]

            delta = (r["due"] - now) if r["due"] else None
            if r["cat"] == CAT_SUBMITTED:
                icon = "✅"
                remain = "已提交(迟交)" if r["late"] else "已提交"
            elif r["cat"] == CAT_OVERDUE:
                icon, remain = "⚫", humanize(delta)
            else:
                icon = urgency_icon(delta)
                remain = humanize(delta) if delta is not None else "无deadline"

            due_text = f"{r['due']:%m-%d %H:%M %a}" if r["due"] else "-"
            tags = ""
            if r["state"] == "draft":
                tags += "  [草稿未正式提交]"
            if r["extended"]:
                tags += "  [已延期]"
            title = f"[Quiz] {r['name']}" if r["kind"] == "quiz" else r["name"]
            print(
                f"{pad(str(i), 3)}{icon} {pad(remain, W_REM)}{pad(due_text, W_DUE)}"
                f"{pad(trunc(r['course'], W_COURSE - 1), W_COURSE)}"
                f"{trunc(title, W_NAME)}{tags}"
            )

        if pending:
            print("\n----- 各课程待提交数量 -----")
            counts = Counter(r["course"] for r in pending)
            for cname, n in counts.most_common():
                print(f"  {cname}: {n}")

        print("\n图例: 🔴<1天  🟠<3天  🟡<7天  🟢>7天  ⚪无deadline  ⚫已过期  ✅已提交")

    if hidden_count:
        print(f"（已隐藏 {hidden_count} 项，输入 r 可查看/恢复）")


# ---------- 交互 ----------

def parse_numbers(text: str, upper: int):
    """把 '1 3,5' 解析成合法序号列表；非法的会提示。"""
    nums = []
    for token in re.split(r"[,\s，]+", text):
        if not token:
            continue
        if not token.isdigit() or not 1 <= int(token) <= upper:
            print(f"  无效序号: {token}（范围 1-{upper}）")
            continue
        nums.append(int(token))
    return nums


def restore_menu(hidden: dict):
    if not hidden:
        print("  当前没有被删除的任务。")
        return
    items = list(hidden.items())
    print("\n  已删除的任务:")
    for i, (_, info) in enumerate(items, 1):
        print(f"   {i}. [{info.get('course', '?')}] {info.get('name', '?')}")
    try:
        text = input("  输入要恢复的序号（可多个，或输入 all 全部恢复，回车取消）> ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return
    if not text:
        return
    chosen = range(1, len(items) + 1) if text.lower() == "all" else parse_numbers(text, len(items))
    for n in chosen:
        key, info = items[n - 1]
        hidden.pop(key, None)
        print(f"  已恢复: [{info.get('course', '?')}] {info.get('name', '?')}")
    if chosen:
        save_hidden(hidden)
        print("  （恢复的任务会在下次运行脚本时重新出现在列表里）")


def interactive_loop(rows, hidden, now):
    print("\n命令: 序号=打开页面 | d 序号=删除 | r=恢复已删除 | l=重新显示列表 | q=退出")
    while True:
        try:
            text = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        low = text.lower()
        if low in ("", "q", "quit", "exit"):
            break
        if low in ("l", "list"):
            print_table(rows, now, len(hidden))
            continue
        if low in ("r", "restore"):
            restore_menu(hidden)
            continue

        m = re.match(r"^(d|del|delete|rm)\s*(.*)$", text, re.I)
        if m:
            nums = parse_numbers(m.group(2), len(rows))
            if not nums:
                print("  用法: d 序号 [序号 ...]，例如 d 2 4")
                continue
            for n in sorted(set(nums)):
                r = rows[n - 1]
                hidden[r["key"]] = {"course": r["course"], "name": r["name"]}
                print(f"  已删除: [{r['course']}] {r['name']}")
            save_hidden(hidden)
            gone = {n - 1 for n in nums}
            rows[:] = [r for i, r in enumerate(rows) if i not in gone]
            print_table(rows, now, len(hidden))   # 序号会变，所以重新显示
            continue

        for n in parse_numbers(text, len(rows)):
            r = rows[n - 1]
            if not r["url"]:
                print(f"  {r['course']} - {r['name']}: 没有拿到链接")
                continue
            print(f"  打开: [{r['course']}] {r['name']}")
            webbrowser.open(r["url"])


# ---------- 排查用 ----------

def debug_report(courses, assign_result, quiz_result):
    print("\n===== DEBUG：每门课程的统计 =====")
    a_count = {c["id"]: len(c.get("assignments", [])) for c in assign_result.get("courses", [])}
    q_count = Counter(q.get("course") for q in quiz_result.get("quizzes", []))
    for w in assign_result.get("warnings", []):
        print(f"  [assign warning] {w.get('item', '')} {w.get('message', '')}")
    for c in courses:
        print(f"\n[{c['id']}] {c.get('shortname', '')}")
        print(f"   作业(assign): {a_count.get(c['id'], 0)}   Quiz: {q_count.get(c['id'], 0)}")
        try:
            sections = call("core_course_get_contents", courseid=c["id"])
            mods = Counter(m.get("modname") for s in sections for m in s.get("modules", []))
            print("   课程里的活动类型: " + (", ".join(f"{k}×{v}" for k, v in mods.most_common()) or "(空)"))
        except Exception as e:
            print(f"   core_course_get_contents 失败: {e}")
    print("\n提示: 如果活动类型里有 assign/quiz 之外、跟提交有关的（如 turnitintooltwo、workshop、"
          "data、forum），说明它们不在作业接口里，需要另外加。把这段输出发给我即可。\n")


# ---------- 主流程 ----------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pending", action="store_true", help="只显示待提交的")
    parser.add_argument("--debug", action="store_true", help="打印每门课程的统计，排查条目太少的问题")
    parser.add_argument("--no-open", action="store_true", help="只显示列表，不进入交互")
    args = parser.parse_args()

    now = datetime.now(TZ)
    hidden = load_hidden()

    site = call("core_webservice_get_site_info")
    user_id = site["userid"]
    print(f"用户: {site.get('fullname')}  |  现在: {now:%Y-%m-%d %H:%M}\n")

    all_courses = call("core_enrol_get_users_courses", userid=user_id)

    # 选出本学期课程：手动指定 > 自动排除已结束的课程
    if INCLUDE_COURSE_IDS:
        courses = [c for c in all_courses if c["id"] in INCLUDE_COURSE_IDS]
    else:
        now_ts = time.time()
        courses = [
            c for c in all_courses
            if not (c.get("enddate") and c["enddate"] < now_ts) and not c.get("hidden")
        ]
    if not courses:
        sys.exit("没有找到符合条件的课程，请检查 INCLUDE_COURSE_IDS。")

    print(f"识别到 {len(courses)} 门课程（账号下共 {len(all_courses)} 门）:")
    for c in courses:
        print(f"  [{c['id']}] {c.get('shortname', '')} - {c.get('fullname', '')}")

    course_info = {c["id"]: c for c in courses}
    course_ids = list(course_info.keys())

    assign_result = call("mod_assign_get_assignments", courseids=course_ids)
    try:
        quiz_result = call("mod_quiz_get_quizzes_by_courses", courseids=course_ids)
    except Exception as e:
        print(f"（Quiz 接口不可用，已跳过: {e}）")
        quiz_result = {"quizzes": []}

    if args.debug:
        debug_report(courses, assign_result, quiz_result)

    def cname_of(course_id, fallback="?"):
        c = course_info.get(course_id, {})
        return c.get("shortname") or c.get("fullname") or fallback

    def categorize(row, submit_ts, now):
        """根据是否提交 / 是否过期，决定放在哪一块。"""
        if row["submitted"]:
            row["cat"] = CAT_SUBMITTED
            row["late"] = bool(row["due"] and submit_ts and submit_ts > row["due"].timestamp())
        elif row["due"] is not None and row["due"] < now:
            row["cat"] = CAT_OVERDUE
            row["late"] = False
        else:
            row["cat"] = CAT_PENDING
            row["late"] = False

    rows = []

    # --- 作业 ---
    for course in assign_result.get("courses", []):
        cname = cname_of(course["id"], course.get("shortname", "?"))
        for a in course.get("assignments", []):
            key = str(a["id"])
            if key in hidden:       # 被你删除的任务：直接跳过
                continue
            state, sub_ts, ext_ts = get_assign_submission(a["id"])
            due_ts = a.get("duedate", 0) or 0
            extended = bool(ext_ts and ext_ts > due_ts)
            if extended:
                due_ts = ext_ts
            cmid = a.get("cmid")
            row = {
                "key": key, "kind": "assign", "course": cname, "name": a["name"],
                "due": datetime.fromtimestamp(due_ts, TZ) if due_ts else None,
                "state": state, "submitted": state == "submitted", "extended": extended,
                "url": f"{BASE_URL}/mod/assign/view.php?id={cmid}" if cmid else None,
            }
            categorize(row, sub_ts, now)
            rows.append(row)

    # --- Quiz ---
    for q in quiz_result.get("quizzes", []):
        key = f"quiz-{q['id']}"
        if key in hidden:
            continue
        finish_ts = quiz_finished_time(q["id"], user_id)
        close_ts = q.get("timeclose", 0) or 0
        cmid = q.get("coursemodule")
        row = {
            "key": key, "kind": "quiz", "course": cname_of(q.get("course")), "name": q["name"],
            "due": datetime.fromtimestamp(close_ts, TZ) if close_ts else None,
            "state": "submitted" if finish_ts else "new", "submitted": bool(finish_ts),
            "extended": False,
            "url": f"{BASE_URL}/mod/quiz/view.php?id={cmid}" if cmid else None,
        }
        categorize(row, finish_ts, now)
        rows.append(row)

    # 过滤掉 deadline 早已过去很久的条目（比如上学期老师忘记删的）
    if MAX_PAST_DAYS is not None:
        cutoff = now - timedelta(days=MAX_PAST_DAYS)
        rows = [r for r in rows if r["due"] is None or r["due"] >= cutoff]

    if args.pending:
        rows = [r for r in rows if r["cat"] == CAT_PENDING]

    rows.sort(key=sort_key)

    print_table(rows, now, len(hidden))

    if not args.no_open and (rows or hidden):
        interactive_loop(rows, hidden, now)


if __name__ == "__main__":
    try:
        main()
    except requests.RequestException as e:
        sys.exit(f"网络请求出错: {e}")
    except RuntimeError as e:
        sys.exit(str(e))
