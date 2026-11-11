"""
Spectrum (UM Moodle) announcement viewer.

- Reads the Moodle mobile web-service token from token.txt (or token.text)
- Shows "Today's News": announcements/replies from the last 48 hours (a, b, c ...)
- Then lists every in-progress course with its announcements from the last N days (1, 2, 3 ...)
- Type a letter or number to open that announcement in your browser

Usage:
    python spectrum_announcements.py            # last 14 days (default)
    python spectrum_announcements.py --days 7   # last 7 days
    python spectrum_announcements.py --all-courses   # include past courses too

Requires:  pip install requests
"""

import argparse
import html
import os
import re
import sys
import time
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path

import requests

BASE_URL = "https://spectrum.um.edu.my"
WS_URL = f"{BASE_URL}/webservice/rest/server.php"
TOKEN_FILENAMES = ["token.txt", "token.text"]
TIMEOUT = 30


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def load_token() -> str:
    """Look for the token file next to the script, then in the current folder."""
    folders = [Path(__file__).resolve().parent, Path.cwd()]
    for folder in folders:
        for name in TOKEN_FILENAMES:
            path = folder / name
            if path.is_file():
                token = path.read_text(encoding="utf-8").strip()
                if token:
                    return token
    sys.exit(
        "Could not find a token file. Put your token in token.txt "
        "(same folder as this script)."
    )


class MoodleError(Exception):
    pass


def ws_call(token: str, function: str, **params):
    """Call a Moodle web-service function and return the decoded JSON."""
    data = {
        "wstoken": token,
        "wsfunction": function,
        "moodlewsrestformat": "json",
    }
    data.update(params)
    resp = requests.post(WS_URL, data=data, timeout=TIMEOUT)
    resp.raise_for_status()
    result = resp.json()
    if isinstance(result, dict) and "exception" in result:
        raise MoodleError(f"{function}: {result.get('message', result)}")
    return result


def clean(text: str) -> str:
    """Strip HTML tags / entities and collapse whitespace."""
    text = html.unescape(re.sub(r"<[^>]+>", "", text or ""))
    return re.sub(r"\s+", " ", text).strip()


def get_courses(token: str, userid: int, all_courses: bool):
    """Return the list of courses (in-progress only unless all_courses=True)."""
    if not all_courses:
        try:
            res = ws_call(
                token,
                "core_course_get_enrolled_courses_by_timeline_classification",
                classification="inprogress",
            )
            courses = res.get("courses", [])
            if courses:
                return courses
        except (MoodleError, requests.RequestException):
            pass  # fall back to all enrolled courses
    return ws_call(token, "core_enrol_get_users_courses", userid=userid)


def is_announcement_forum(forum: dict) -> bool:
    name = (forum.get("name") or "").lower()
    return (
        forum.get("type") == "news"
        or "announcement" in name
        or "pengumuman" in name
    )


def get_discussions(token: str, forum_id: int, cutoff_ts: int):
    """Fetch discussions of a forum, newest first, stopping once past the cutoff."""
    found = []
    page, per_page = 0, 50
    while True:
        res = ws_call(
            token,
            "mod_forum_get_forum_discussions",
            forumid=forum_id,
            sortorder=-1,
            page=page,
            perpage=per_page,
        )
        discussions = res.get("discussions", [])
        if not discussions:
            break
        found.extend(discussions)
        if len(discussions) < per_page or page >= 9:
            break
        page += 1

    groups = []  # one group (list of entries) per discussion
    for d in found:
        # 'created' = when the topic was started (the "Started by" date)
        created = d.get("created") or d.get("timemodified") or 0
        modified = d.get("timemodified") or created
        if max(created, modified) < cutoff_ts:
            continue  # nothing new in this discussion within the window

        title = clean(d.get("name") or d.get("subject") or "(no title)")
        # 'discussion' is the id used in discuss.php?d=...
        url = f"{BASE_URL}/mod/forum/discuss.php?d={d['discussion']}"
        entries = []

        # The original post: only listed if it was posted inside the window
        if created >= cutoff_ts:
            entries.append({"title": title, "time": created, "url": url})

        # Replies: numbered in chronological order, only listed if inside the window
        if d.get("numreplies", 1) > 0:
            posts = [p for p in get_posts(token, d["discussion"]) if not p.get("deleted")]
            posts.sort(key=post_time)
            replies = [p for p in posts if post_parent(p)]
            for n, p in enumerate(replies, start=1):
                ts = post_time(p)
                if ts >= cutoff_ts:
                    entries.append(
                        {
                            "title": f"{title}-回帖{n}",
                            "time": ts,
                            "url": f"{url}#p{p['id']}",  # jump straight to that reply
                        }
                    )

        if entries:
            groups.append(entries)

    # Newest-active discussion first; inside a discussion: original, then replies in order
    groups.sort(key=lambda g: max(e["time"] for e in g), reverse=True)
    return groups


def get_posts(token: str, discussion_id: int):
    """All posts (original + replies) of one discussion."""
    try:
        res = ws_call(token, "mod_forum_get_discussion_posts", discussionid=discussion_id)
    except MoodleError:  # older Moodle versions
        res = ws_call(token, "mod_forum_get_forum_discussion_posts", discussionid=discussion_id)
    return res.get("posts", [])


def post_time(post: dict) -> int:
    return post.get("timecreated") or post.get("created") or 0


def post_parent(post: dict) -> int:
    """Parent post id; 0/None means this is the original post."""
    return post.get("parentid") or post.get("parent") or 0


# --------------------------------------------------------------------------- #
# Display helpers
# --------------------------------------------------------------------------- #
BIG_FONT = {
    "T": ["█████", "  █  ", "  █  ", "  █  ", "  █  "],
    "O": [" ███ ", "█   █", "█   █", "█   █", " ███ "],
    "D": ["████ ", "█   █", "█   █", "█   █", "████ "],
    "A": [" ███ ", "█   █", "█████", "█   █", "█   █"],
    "Y": ["█   █", " █ █ ", "  █  ", "  █  ", "  █  "],
    "S": [" ████", "█    ", " ███ ", "    █", "████ "],
    "N": ["█   █", "██  █", "█ █ █", "█  ██", "█   █"],
    "E": ["█████", "█    ", "████ ", "█    ", "█████"],
    "W": ["█   █", "█   █", "█ █ █", "██ ██", "█   █"],
    "'": ["█ ", "█ ", "  ", "  ", "  "],
    " ": ["   ", "   ", "   ", "   ", "   "],
}


def print_banner(text: str, emoji: str = ""):
    """Print `text` as big block letters (a terminal can't change its font size)."""
    rows = [""] * 5
    for ch in text.upper():
        glyph = BIG_FONT.get(ch, BIG_FONT[" "])
        for i in range(5):
            rows[i] += glyph[i] + " "
    rows[2] += "  " + emoji
    print()
    for row in rows:
        print(row.rstrip())
    print()


def entries_in_window(groups, cutoff_ts):
    """Keep only entries newer than cutoff; discussions with the latest activity first."""
    kept = []
    for g in groups:
        es = [e for e in g if e["time"] >= cutoff_ts]
        if es:
            kept.append(es)
    kept.sort(key=lambda g: max(e["time"] for e in g), reverse=True)
    return [e for g in kept for e in g]


SEPARATOR = "=" * 60


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
NEWS_HOURS = 48
BOLD_CYAN = "\033[1;36m"
RESET = "\033[0m"


def enable_ansi():
    """Make colours/bold work in the Windows terminal."""
    if os.name == "nt":
        os.system("")


def letter_label(i: int) -> str:
    """0 -> a, 1 -> b, ... 25 -> z, 26 -> aa, 27 -> ab ..."""
    label = ""
    i += 1
    while i > 0:
        i, rem = divmod(i - 1, 26)
        label = chr(ord("a") + rem) + label
    return label


def fmt_date(ts: int) -> str:
    return datetime.fromtimestamp(ts).strftime("%d %b %Y")


def fmt_datetime(ts: int) -> str:
    return datetime.fromtimestamp(ts).strftime("%d %b %Y %H:%M")


def main():
    parser = argparse.ArgumentParser(description="Spectrum announcement viewer")
    parser.add_argument("--days", type=int, default=14,
                        help="how many days back to show (default: 14)")
    parser.add_argument("--all-courses", action="store_true",
                        help="include courses that are not 'in progress'")
    args = parser.parse_args()

    token = load_token()
    enable_ansi()

    now = datetime.now()
    cutoff_days = int((now - timedelta(days=args.days)).timestamp())
    cutoff_news = int((now - timedelta(hours=NEWS_HOURS)).timestamp())
    fetch_cutoff = min(cutoff_days, cutoff_news)  # fetch once, filter twice

    print("Connecting to Spectrum ...")
    try:
        info = ws_call(token, "core_webservice_get_site_info")
        courses = get_courses(token, info["userid"], args.all_courses)
        if not courses:
            sys.exit("No courses found.")
        course_ids = [c["id"] for c in courses]
        forums = ws_call(
            token,
            "mod_forum_get_forums_by_courses",
            **{f"courseids[{i}]": cid for i, cid in enumerate(course_ids)},
        )
    except (MoodleError, requests.RequestException) as e:
        sys.exit(f"Error talking to Spectrum: {e}")

    forums_by_course = {}
    for f in forums:
        if is_announcement_forum(f):
            forums_by_course.setdefault(f["course"], []).append(f)

    # ---- collect everything first ------------------------------------------------
    collected = []  # one dict per course
    for course in sorted(courses, key=lambda c: c.get("fullname", "")):
        full_name = clean(course.get("fullname", "Unknown course"))
        info_row = {"name": full_name, "code": full_name.split()[0] if full_name else "",
                    "has_forum": False, "items": [], "errors": []}
        course_forums = forums_by_course.get(course["id"], [])
        if course_forums:
            info_row["has_forum"] = True
            groups = []
            for forum in course_forums:
                try:
                    groups.extend(get_discussions(token, forum["id"], fetch_cutoff))
                except (MoodleError, requests.RequestException) as e:
                    info_row["errors"].append(f"could not load '{forum.get('name')}': {e}")
            groups.sort(key=lambda g: max(e["time"] for e in g), reverse=True)
            info_row["items"] = [e for g in groups for e in g]
        collected.append(info_row)

    links = {}  # "a" / "1" -> url

    # ---- Part 1: Today's News (last 48 hours, lettered) --------------------------
    print()
    print(f"{BOLD_CYAN}📰  T O D A Y ' S   N E W S{RESET}")
    print()
    news = []
    for row in collected:
        for item in row["items"]:
            if item["time"] >= cutoff_news:
                news.append((row["code"], item))
    news.sort(key=lambda x: x[1]["time"], reverse=True)

    if not news:
        print("今晚是个平安夜😊")
    else:
        for i, (code, item) in enumerate(news):
            label = letter_label(i)
            print(f"  {label:>3}. [{code}] {item['title']}  [{fmt_datetime(item['time'])}]")
            links[label] = item["url"]

    # ---- divider -----------------------------------------------------------------
    print()
    print("=" * 60)
    print()

    # ---- Part 2: last N days, by course (numbered) -------------------------------
    print(f"Announcements from the last {args.days} days "
          f"(today: {now:%d %b %Y})\n")
    counter = 1
    for course_no, row in enumerate(collected, start=1):
        print(f"课程{course_no}：{row['name']}")

        if not row["has_forum"]:
            print("  (no announcement forum found)\n")
            continue
        for err in row["errors"]:
            print(f"  ({err})")

        items = [it for it in row["items"] if it["time"] >= cutoff_days]
        if not items:
            print("  (no announcements in this period)\n")
            continue

        for item in items:
            print(f"  {counter:>3}. {item['title']}  [{fmt_date(item['time'])}]")
            links[str(counter)] = item["url"]
            counter += 1
        print()

    if not links:
        print("Nothing to open. Bye!")
        return

    print("Enter a letter (a, b, ...) or number (1, 2, ...) to open it in your browser "
          "(several separated by space/comma are OK; q to quit).")
    while True:
        try:
            raw = input("> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if raw == "":
            continue
        if raw in {"q", "quit", "exit"}:
            break
        for part in re.split(r"[,\s]+", raw):
            if not part:
                continue
            if part in links:
                print(f"Opening {links[part]}")
                webbrowser.open(links[part])
                time.sleep(0.3)
            else:
                print(f"'{part}' is not a valid choice.")


if __name__ == "__main__":
    main()
