"""从 SPeCTRUM (Moodle) 下载课程 PPT/PDF，只下载新增或更新过的文件。

用法：
1. 把 token 放进环境变量 MOODLE_TOKEN，或放在脚本同目录的 token.txt（不要上传到网上）
2. 运行脚本，在命令行里看课程列表，直接输入编号选课（如 1 3 5，或 all）
3. 选择会被记住，下次运行直接回车即可
4. 你在本地删掉/改名/移走的文件不会被重新下载（老师更新了该文件除外）；
   误删了想找回，运行时加 --restore-missing
"""
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ============ 配置 ============
DOMAIN = "https://spectrum.um.edu.my"
COURSE_IDS = []  # 留空 = 运行时在命令行里选；也可以写死，如 [12345, 23456]
EXTENSIONS = (".pdf", ".ppt", ".pptx")
# 在 Spectrum 上显示名以 "Tutorial" 开头的资料，额外允许 doc/docx（其他 doc 不下载）
TUTORIAL_EXTENSIONS = (".docx",)
TUTORIAL_RE = re.compile(r"^\s*tutorial", re.IGNORECASE)

# ---- 按 L1/L2/L3 把 "Lecture Notes" 分到每周文件夹 ----
# 课程的 shortname 或 fullname 里包含这些关键字时，启用该功能
WEEK_SORT_COURSES = ("WIX2001",)
# 只处理名字匹配这个正则的章节
LECTURE_SECTION_RE = re.compile(r"lecture\s*notes", re.IGNORECASE)
# 资料名以 L1 / L2 / Lecture 3 之类开头，就视为新一周的起点
WEEK_MARK_RE = re.compile(r"^\s*(?:L|Lecture)\s*0*(\d+)\b", re.IGNORECASE)
# 每周文件夹的名字（想叫 Week 01 / 第1周 之类，改这里）
WEEK_FOLDER_FMT = "Week {n}"
# ----------------------------------------------------

OUT_DIR = Path("UM_Courses")
DELAY = 1.5  # 每次下载之间的间隔（秒）
# ==============================

RESTORE_MISSING = "--restore-missing" in sys.argv  # 把本地已被删除/移走的文件重新下载回来
REST_URL = f"{DOMAIN}/webservice/rest/server.php"
MANIFEST = OUT_DIR / "downloaded.json"
SELECTION = OUT_DIR / "selected_courses.json"


def load_token():
    token = os.environ.get("MOODLE_TOKEN")
    if not token and Path("token.txt").exists():
        token = Path("token.txt").read_text(encoding="utf-8").strip()
    if not token:
        sys.exit("找不到 token：请设置环境变量 MOODLE_TOKEN，或把 token 放进 token.txt")
    return token


def make_session():
    s = requests.Session()
    retry = Retry(total=3, backoff_factor=2, status_forcelist=(429, 500, 502, 503, 504))
    s.mount("https://", HTTPAdapter(max_retries=retry))
    return s


def api(session, token, function, **params):
    data = {"wstoken": token, "wsfunction": function, "moodlewsrestformat": "json", **params}
    r = session.post(REST_URL, data=data, timeout=30)
    r.raise_for_status()
    result = r.json()
    if isinstance(result, dict) and "exception" in result:
        raise RuntimeError(f"{function} 失败: {result.get('message')}")
    return result


def safe(name):
    """去掉 Windows/Mac 文件名里不允许的字符。"""
    name = re.sub(r'[\\/:*?"<>|]', "_", name or "").strip(" .")
    return name or "unnamed"


def download(session, token, url, dest):
    """先写到 .part 临时文件，成功后再改名，避免留下半截文件。"""
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".part")
    with session.get(url, params={"token": token}, stream=True, timeout=(10, 60)) as r:
        r.raise_for_status()
        ctype = r.headers.get("Content-Type", "")
        if "json" in ctype or "html" in ctype:
            raise RuntimeError("服务器返回的不是文件（token 失效或无权限？）")
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(65536):
                f.write(chunk)
    tmp.replace(dest)


def save_manifest(manifest):
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def choose_courses(courses):
    """在命令行里让用户选课，并记住选择。"""
    if SELECTION.exists():
        saved = json.loads(SELECTION.read_text(encoding="utf-8"))
        valid = [c for c in courses if c["id"] in saved]
        if valid:
            print("上次选择的课程：")
            for c in valid:
                print(f"  {c.get('shortname', '')}  {c.get('fullname', '')}")
            if input("\n直接使用？（回车 = 是，输入 n = 重新选择）：").strip().lower() != "n":
                return [c["id"] for c in valid]

    print("你的课程：")
    for i, c in enumerate(courses, 1):
        print(f"  {i:>2}. {c.get('shortname', '')}  {c.get('fullname', '')}")
    raw = input("\n输入要下载的编号（空格或逗号分隔，如 1 3 5；all = 全部）：").strip().lower()

    if raw == "all":
        chosen = courses
    else:
        nums = {int(x) for x in re.findall(r"\d+", raw)}
        chosen = [c for i, c in enumerate(courses, 1) if i in nums]
    if not chosen:
        sys.exit("没有选中任何课程。")

    SELECTION.write_text(json.dumps([c["id"] for c in chosen]), encoding="utf-8")
    return [c["id"] for c in chosen]


def main():
    token = load_token()
    s = make_session()
    OUT_DIR.mkdir(exist_ok=True)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}

    info = api(s, token, "core_webservice_get_site_info")
    courses = api(s, token, "core_enrol_get_users_courses", userid=info["userid"])

    course_ids = COURSE_IDS or choose_courses(courses)

    names = {c["id"]: c.get("shortname", "") for c in courses}
    fullnames = {c["id"]: c.get("fullname", "") for c in courses}
    new_count = 0

    for cid in course_ids:
        course_dir = OUT_DIR / safe(f"{cid}_{names.get(cid, '')}")
        print(f"\n== 课程 {cid} {names.get(cid, '')} ==")
        try:
            sections = api(s, token, "core_course_get_contents", courseid=cid)
        except Exception as e:
            print(f"❌ 获取课程内容失败：{str(e).replace(token, '***')}")
            continue

        # 这门课是否启用 "Lecture Notes 按 L1/L2... 分周" 功能
        course_label = f"{names.get(cid, '')} {fullnames.get(cid, '')}".upper()
        week_course = any(k.upper() in course_label for k in WEEK_SORT_COURSES)

        for sec in sections:
            sec_name = sec.get("name", "")
            sort_by_week = week_course and bool(LECTURE_SECTION_RE.search(sec_name))
            current_week = None  # 还没遇到 L1 之前为 None

            for mod in sec.get("modules", []):
                # 按页面顺序扫描：遇到 L1 / L2 / L3... 就切换到对应的周
                if sort_by_week:
                    m = WEEK_MARK_RE.match(mod.get("name", ""))
                    if m:
                        current_week = int(m.group(1))

                if mod.get("modname") not in ("resource", "folder"):
                    continue

                if sort_by_week and current_week is not None:
                    target_dir = course_dir / safe(WEEK_FOLDER_FMT.format(n=current_week))
                else:
                    target_dir = course_dir / safe(sec_name)

                is_tutorial = bool(TUTORIAL_RE.match(mod.get("name", "")))
                allowed = EXTENSIONS + (TUTORIAL_EXTENSIONS if is_tutorial else ())
                for c in mod.get("contents", []):
                    fname = c.get("filename", "")
                    if c.get("type") != "file" or not fname.lower().endswith(allowed):
                        continue

                    key = f"{cid}:{mod['id']}:{fname}"
                    stamp = c.get("timemodified", 0)
                    entry = manifest.get(key)

                    # 之前已经下载到别的文件夹（比如旧的 Lecture Notes）-> 搬到对应的周文件夹
                    if entry and sort_by_week and current_week is not None:
                        old = Path(entry["path"])
                        new = target_dir / old.name
                        if old.exists() and old.parent != target_dir and not new.exists():
                            new.parent.mkdir(parents=True, exist_ok=True)
                            shutil.move(str(old), str(new))
                            entry["path"] = str(new)
                            save_manifest(manifest)
                            print(f"📂 移动：{old.name} -> {target_dir.name}/")

                    # 以前下载过、老师也没有更新 -> 跳过。
                    # 就算你把文件删了、改名了、移走了，也不会再下载回来（只有老师更新了才会重新下）。
                    # 想把误删的文件找回来：运行时加参数 --restore-missing
                    if entry and entry["time"] == stamp and not (RESTORE_MISSING and not Path(entry["path"]).exists()):
                        continue

                    if entry:  # 老师更新了同名文件 -> 覆盖原路径
                        dest = Path(entry["path"])
                    else:
                        disp = fname
                        if is_tutorial and "tutorial" not in fname.lower():
                            disp = f"{mod.get('name', '')} - {fname}"  # 文件名里补上 Spectrum 上的显示名
                        dest = target_dir / safe(disp)
                        used = {e["path"] for e in manifest.values()}
                        if str(dest) in used:  # 同文件夹出现同名文件，加模块 id 区分
                            dest = dest.with_name(f"{dest.stem}_{mod['id']}{dest.suffix}")

                    print(f"⬇️  {target_dir.name} / {fname}")
                    try:
                        download(s, token, c["fileurl"], dest)
                    except Exception as e:
                        print(f"   ❌ 失败：{str(e).replace(token, '***')}")
                        continue

                    manifest[key] = {"path": str(dest), "time": stamp}
                    save_manifest(manifest)
                    new_count += 1
                    time.sleep(DELAY)

    print(f"\n完成，新下载/更新了 {new_count} 个文件。")


if __name__ == "__main__":
    main()
