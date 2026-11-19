<div align="center">

# 🥔 Spectrum Toolbox · 哦~土豆~~ 妙妙工具箱

**One menu for UM Spectrum (Moodle): check in, read announcements, track deadlines, download slides, and sync them to NotebookLM.**

[English](#english) · [中文](#中文)

</div>

---

<a id="english"></a>

# English

## What's in the box

| Menu # | Tool | Script | What it does |
|:--:|------|--------|--------------|
| 1 | Check-in | `att.py` | Opens the right **Attendance** page for the class that is on *right now*. You still tick "Present" and submit yourself. |
| 2 | Announcements | `spectrum_announcements.py` | "Today's News" (last 48 h) + announcements per course for the last N days. Type a number to open one. |
| 3 | Deadlines | `moodle_deadlines.py` | All assignments / quizzes sorted by urgency (pending, overdue, submitted). |
| 4 | Download materials | `spectrum_download.py` | Downloads new or updated PDF / PPT / PPTX into `UM_Courses/`. Never re-downloads what you already have. |
| 5 | Update NotebookLM | `notebooklm_pipeline.py` | Makes your NotebookLM notebooks mirror the local `Week N` folders, then generates a quiz and flashcards per week. |
| – | Launcher | `哦~土豆~~.py` + `start.bat` | The menu that runs the five tools above. Double-click `start.bat` and you're in. |

> [!NOTE]
> This is an unofficial, personal-use project. It is not affiliated with Universiti Malaya, Moodle, Google or NotebookLM. Tool 1 only **opens** the attendance page; it never marks attendance for you. Tool 5 relies on the unofficial [`notebooklm-py`](https://pypi.org/project/notebooklm-py/) library, which uses undocumented Google APIs and may break at any time. Use at your own risk and follow your university's rules.

---

## Part 1 · Quick Start (step by step)

> Written for **Windows**. On macOS/Linux the Python scripts work the same way, but use `python3` instead of `python`, and run the launcher with `python3 "哦~土豆~~.py"` instead of `start.bat`.

### Step 1 · Install Python (3.10 or newer)

1. Download Python from <https://www.python.org/downloads/>.
2. Run the installer and **tick "Add python.exe to PATH"** on the first screen. This is the step people forget.
3. Open a new Command Prompt (press `Win + R`, type `cmd`, press Enter) and check:

```cmd
python --version
```

You should see something like `Python 3.12.x`. If you get *"'python' is not recognized"*, re-run the installer and tick the PATH box.

### Step 2 · Get the files

Either clone the repo:

```cmd
git clone https://github.com/YOUR_NAME/YOUR_REPO.git
```

or click **Code → Download ZIP** on GitHub and unzip it anywhere (e.g. `D:\spectrum-toolbox`).

Then open a Command Prompt **inside that folder**:

```cmd
cd /d "D:\spectrum-toolbox"
```

> 💡 Shortcut: open the folder in File Explorer, click the address bar, type `cmd`, press Enter.

### Step 3 · Install the libraries

Tools 1–4 need only one library:

```cmd
pip install requests
```

Tool 5 (NotebookLM) needs two more steps. **Skip them if you don't use NotebookLM.**

```cmd
pip install "notebooklm-py[browser]"
playwright install chromium
```

The second command downloads a ~170 MB browser used for Google sign-in and prints no progress bar, so be patient (30–90 s).

> If `pip` is not recognized, use `python -m pip install requests` instead (same for the other two commands).

### Step 4 · Add your Moodle token

The tools talk to Spectrum with a personal **Moodle mobile web-service token** instead of your password.

1. Log in to Spectrum in your browser.
2. Open your profile menu → **Preferences → Security keys** and copy the key for **Moodle mobile web service**. The exact location can differ between Moodle versions and sites.
3. Create `token.txt` **in the project folder** and paste the token on a single line:

```cmd
notepad token.txt
```

(Click **Yes** when Notepad asks to create the file, paste the token, save.)

> [!WARNING]
> - **One line, token only.** Don't add a site URL or comments. (`att.py` alone accepts an optional two-line format, but the other scripts would read the whole file as the token and fail.)
> - Your token is as powerful as your password. **Never upload `token.txt` to GitHub** and never share it. See [Security](#security--before-you-push-to-github).

### Step 5 · Launch

Double-click **`start.bat`**, or run:

```cmd
python "哦~土豆~~.py"
```

You'll see:

```
====================================
        哦~土豆~~  妙妙工具箱
====================================
请选择您的妙妙工具：
  1. 签到
  2. 看公告
  3. 查ddl
  4. 下载课程资料
  5. 更新notebook
  0. 退出
```

Type a number and press Enter. When a tool finishes, press Enter to return to the menu. `0` or `q` quits.

### Step 6 · First-time setup for each tool

Do these once, in this order:

| Order | Tool | What to do |
|:--:|------|------------|
| ① | **4 · Download** | Choose it from the menu. Type the numbers of your courses (e.g. `1 3 5`, or `all`). Your choice is remembered; next time just press Enter. |
| ② | **3 · Deadlines** / **2 · Announcements** | Nothing to set up. Just run them. |
| ③ | **1 · Check-in** | Needs a one-time setup in cmd (the menu can't take arguments): `python att.py sync`, then `python att.py sched ...` for each class. See [att.py](#1--attpy--check-in). |
| ④ | **5 · NotebookLM** | Needs the NotebookLM install from Step 3, a prompts folder, and a Google login. See [notebooklm_pipeline.py](#5--notebooklm_pipelinepy--notebooklm-sync). |

### What your folder will look like

```
spectrum-toolbox/
├─ start.bat                    ← double-click me
├─ 哦~土豆~~.py                  ← the menu
├─ att.py
├─ spectrum_announcements.py
├─ moodle_deadlines.py
├─ spectrum_download.py
├─ notebooklm_pipeline.py
├─ token.txt                    ← YOU create this (never commit it)
├─ .att.json                    ← auto-created: saved attendance pages + class times
├─ hidden_tasks.json            ← auto-created: deadlines you hid
├─ prompts/                     ← YOU create this (for NotebookLM)
│  ├─ quiz.txt
│  └─ flashcards.txt
└─ UM_Courses/                  ← auto-created by the downloader
   ├─ downloaded.json           ← the downloader's memory (don't delete)
   ├─ selected_courses.json     ← your course selection
   └─ 129_WIA2001/
      ├─ Week 1/
      ├─ Week 2/
      └─ EXAM/
```

---

## Part 2 · Tool reference

> **Important:** the menu runs every script **without arguments**. To use flags or sub-commands, open cmd **in the project folder** and run the script directly, as shown below. Always run from the project folder, because several scripts find `token.txt` and `UM_Courses/` relative to where you launch them.

### 1 · `att.py` — Check-in

Opens the Attendance page of the class that is currently in session. **You** still choose *Present* and submit in the browser.

**One-time setup**

```cmd
python att.py sync
```

Fetches every Attendance page you can see in your non-finished courses. Re-run it each semester; times you already set are kept.

Then tell it when each class happens (24-hour `HH:MM`, days are `mon tue wed thu fri sat sun`). A class can have several time slots:

```cmd
python att.py list
python att.py sched 1 mon 10:00
python att.py sched wia2001 thu 14:00
```

(`1` is the number from `list`; a name keyword like `wia2001` also works.)

**Daily use**

| Command | What it does |
|---------|--------------|
| `python att.py` (or menu **1**) | Shows classes in session now (from **15 min before** to **2 h after** the start time). Press Enter to open it. |
| `python att.py hsm` | Fuzzy-match by name and open it, regardless of time. |
| `python att.py list` | List all saved attendance pages. |
| `python att.py sched <no./keyword> <day> <HH:MM>` | Add a class time. |
| `python att.py unsched <no./keyword> <day> <HH:MM>` | Remove one time. |
| `python att.py unsched <no./keyword> all` | Clear all times of that class. |
| `python att.py add <name> <url>` | Add a page manually, e.g. `.../mod/attendance/view.php?id=1126419`. |
| `python att.py rm <no./keyword>` | Remove a saved page. |

**Notes**
- Uses your **computer's clock and time zone**. Make sure they're right.
- If no class is in session, it just prints a (silly) message and exits. That's normal.
- Settings live in `.att.json` next to the script.

### 2 · `spectrum_announcements.py` — Announcements

```cmd
python spectrum_announcements.py              :: last 14 days (default)
python spectrum_announcements.py --days 7     :: last 7 days
python spectrum_announcements.py --all-courses   :: include courses that are not "in progress"
```

- **Today's News** (last 48 h) is listed with letters `a, b, c…`; the per-course list for the last N days uses numbers `1, 2, 3…`.
- Type a letter or number and press Enter to open it in your browser. You can open several at once (`a 2 5` or `a,2,5`). `q` quits.
- Replies are shown as `Title-回帖1`, `Title-回帖2`… (回帖 = "reply") and open straight at that reply.

### 3 · `moodle_deadlines.py` — Deadlines

```cmd
python moodle_deadlines.py              :: all three blocks
python moodle_deadlines.py --pending    :: only things you still have to submit
python moodle_deadlines.py --no-open    :: print the list and exit (no prompt)
python moodle_deadlines.py --debug      :: per-course stats, for "why are there so few assignments?"
```

The list has three blocks: **Pending** → **Overdue, not submitted** → **Submitted** (late ones are marked). Colour legend: 🔴 < 1 day · 🟠 < 3 days · 🟡 < 7 days · 🟢 > 7 days · ⚪ no deadline · ⚫ overdue · ✅ submitted.

At the `>` prompt:

| Type | Effect |
|------|--------|
| `1 3` or `1,3` | Open items 1 and 3 in the browser |
| `d 2 4` | **Hide** items 2 and 4 forever (saved in `hidden_tasks.json`) |
| `r` | Show hidden items and restore them (they reappear on the next run) |
| `l` | Re-print the list |
| `q` or Enter | Quit |

**Notes**
- Times are shown in Malaysia time (UTC+8).
- Items whose deadline is more than 200 days in the past are hidden. Change `MAX_PAST_DAYS` at the top of the script to alter this.
- If it picks up the wrong courses, put the right course IDs in `INCLUDE_COURSE_IDS` at the top of the script (the script prints the IDs it found).
- Deleting `hidden_tasks.json` un-hides everything.

### 4 · `spectrum_download.py` — Download materials

```cmd
python spectrum_download.py
python spectrum_download.py --restore-missing
```

First run: pick your courses by number. Next runs: press Enter to reuse the last selection, or type `n` to choose again.

- Downloads **only new or updated** files, into `UM_Courses/<courseID>_<shortname>/<section name>/`.
- File types: `.pdf`, `.ppt`, `.pptx`. Items whose Spectrum name starts with **"Tutorial"** may also be `.docx`.
- **WIX2001 special case:** the *Lecture Notes* section is automatically split into `Week 1`, `Week 2`… by the `L1`, `L2`… labels. To enable this for another course, add its code to `WEEK_SORT_COURSES` at the top of the script.
- Waits 1.5 s between downloads (be nice to the server). Half-finished downloads end in `.part` and are cleaned up on success.
- **Deleted a file by mistake?** Run with `--restore-missing` to bring back anything that's missing locally. Without that flag, deleted/renamed/moved files are **not** re-downloaded (unless the teacher updates them).
- Alternative to `token.txt`: set the `MOODLE_TOKEN` environment variable.

### 5 · `notebooklm_pipeline.py` — NotebookLM sync

Makes the cloud match your local folders and generates **one quiz + one flashcard set per week**. There is no state file: every run compares *what's local* with *what's in the cloud* and fills in the gaps. If it's interrupted, just run it again.

**Before the first run**

1. Install the extras (Step 3 above): `notebooklm-py[browser]` + `playwright install chromium`.
2. Download some slides with tool 4, so there are `Week N` folders.
3. Create a `prompts` folder with two plain-text files holding your instructions to NotebookLM:

   ```cmd
   mkdir prompts
   notepad prompts\quiz.txt
   notepad prompts\flashcards.txt
   ```

   Example `quiz.txt`: *"Write 15 multiple-choice questions covering the key concepts in these slides. Include explanations."*
   If a file is missing, the script warns you and uses NotebookLM's defaults.
4. Make sure the `notebooklm` command works: `notebooklm --help`.

**Running**

```cmd
python notebooklm_pipeline.py --dry-run   :: show the plan only, change nothing  (do this first!)
python notebooklm_pipeline.py             :: do it (asks before deleting anything)
python notebooklm_pipeline.py --yes       :: do it, don't ask before deleting
```

Every run starts with `notebooklm login`: a browser window opens for your Google account, so follow the prompts in the terminal. This avoids "Authentication expired" errors.

**How it decides what to do**

| Local folder (directly under the course folder) | Behaviour |
|---|---|
| Name contains `week` + number (`Week 3`, `week 03`, `Week 3 (F2F)`) | Uploaded, and a **quiz + flashcards** are generated for that week from that week's files. |
| Name contains `exam` (`EXAM`) | **Upload only**. No quiz/flashcards are generated, so you can make your own. |
| Anything else (`Introduction`, `General`, …) | Ignored. |
| Course folder name contains `GKU` | Whole course skipped. |

- One notebook per course, named by the course code (`129_WIA2001` → notebook **`WIA2001`**). It's found by name, or created if missing.
- Supported files: `.pdf`, `.ppt`, `.pptx`, `.docx` (others are skipped with a warning). Files starting with `~` or `.` are ignored.
- Cloud sources are titled `filename [#a1b2c3]`: the tag is a fingerprint of the file's **content**, which is how the script knows two files are the same.
- Weeks are processed smallest first across all courses (all Week 1s, then all Week 2s…), so if your daily quota runs out you have the early weeks done.
- Uploads run up to 6 at a time, 60 s each, 3 tries; a file that keeps failing is skipped without blocking the others.
- If NotebookLM rate-limits you, it waits 5 s, retries once, then stops. **Run it again after your quota resets**, and it picks up where it left off.
- Quiz/flashcards are regenerated only when that week's cloud files actually changed.

#### ⚠️ Cloud NotebookLM: things to watch out for

1. **Don't rename sources in the NotebookLM website.** The `[#hash]` in the title is how files are recognised. A source without it is treated as "extra" and deleted.
2. **Don't add your own sources (links, YouTube, pasted text, extra files) to these notebooks.** Anything the script didn't put there is considered extra and **will be deleted** on the next run. Use a separate notebook for your own stuff.
3. **Don't name your own quizzes `Week N - Quiz` / `Week N - Flashcards`.** The script treats those names as its own and may overwrite or delete them. For safety, build hand-made quizzes in a different notebook, or from `EXAM` sources (which the script never touches).
4. **Deleting happens in the cloud too.** If a file is gone locally, its cloud source is deleted at the next sync (you're asked to confirm unless you pass `--yes`). Always `--dry-run` first if you've been tidying your folders.
5. **Don't rename the course folder** (see the table below), since the notebook name comes from it.
6. **The first login and quota:** NotebookLM has per-notebook and daily generation limits that depend on your plan. If you hit them, wait and re-run.
7. Only **quiz and flashcards** are managed. Audio overviews, mind maps, etc. are never touched.

---

## Part 3 · Working inside `UM_Courses/` (add / delete / rename / look)

Your local `UM_Courses/` folder is the **source of truth**: tool 5 makes NotebookLM mirror it. Tool 4 keeps a diary in `UM_Courses/downloaded.json`. Here's what each action does:

| You do this | Tool 4 (download) | Tool 5 (NotebookLM) |
|---|---|---|
| **Look around** | — | — (just use File Explorer, or `tree /F UM_Courses`) |
| **Add your own file** (PDF/PPT/PPTX/DOCX) into `Week N/` | Ignores it. | Next sync uploads it and **regenerates** that week's quiz + flashcards. |
| **Add a file to `EXAM/`** | Ignores it. | Uploaded only. |
| **Delete a file** | **Not** re-downloaded (unless the teacher updates it). `--restore-missing` brings it back. | Its cloud source is deleted and that week's quiz + flashcards are regenerated. 👍 *This is how you keep a file out of your quizzes.* |
| **Rename a file** (content unchanged) | Not re-downloaded. | No change (recognised by content). The cloud keeps the old title. |
| **Edit a file** (e.g. annotate a PDF and save) | Not re-downloaded, but if the teacher later updates it, the download **overwrites your edit**. | Content changed → old source deleted, new one uploaded, that week **regenerated**. Keep annotated copies in a folder whose name has no "week"/"exam" (e.g. `My Notes/`) to avoid this. |
| **Move a file** to another `Week N/` | Not re-downloaded. If the teacher later updates it, the new version is written to the **original** location (so you may end up with two copies). | Both weeks are regenerated. |
| **Rename a week folder**, e.g. `Week 3` → `Week 03` | New files go to the section's name on Spectrum again. | Fine. Same week number = same week. Changing the *number* moves all its files to another week. |
| **Rename the course folder** (`129_WIA2001`) | Breaks the link with `downloaded.json`. | The notebook name comes from the part after `129_`, so a **new notebook** is created and the old one is left alone. **Don't rename it.** |
| **Remove a whole course folder** (e.g. old semester) | Not re-downloaded unless you select the course again *and* `downloaded.json` has no record of it. | That course is no longer scanned. Its notebook is left untouched in the cloud. |
| **Delete `downloaded.json`** | Everything is downloaded again. | Re-uploads are skipped for identical content. |
| **Delete the whole `UM_Courses/`** | Everything is downloaded again and your course selection is forgotten. | Local copy is gone, so run `--dry-run` before syncing! |

**Golden rules**
1. 🗂️ Run everything **from the project folder**.
2. ✅ Download first (tool 4), then sync (tool 5).
3. 🧹 Tidy local files **before** syncing, then `--dry-run` to preview.
4. 🔒 Keep personal notes in folders **not** called "Week …" or "EXAM …".
5. 🚫 Never hand-edit `downloaded.json`, and never rename sources in the NotebookLM web UI.

---

## Security — before you push to GitHub

Add a `.gitignore` next to the scripts **before your first commit**:

```gitignore
token.txt
token.text
.att.json
hidden_tasks.json
UM_Courses/
prompts/
__pycache__/
```

- `token.txt` is your key to your Spectrum account. If you ever leak it, regenerate it in your Spectrum security-keys page.
- Your NotebookLM/Google login is stored by `notebooklm-py` in your user profile folder, outside this project, so it won't be committed. Still, never share it.
- Course slides belong to your lecturers. Don't publish `UM_Courses/`.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `'python' is not recognized` | Re-install Python and tick **Add python.exe to PATH**; open a *new* cmd window. |
| `'pip' is not recognized` | Use `python -m pip install ...`. |
| `No module named 'requests'` | `pip install requests` |
| Double-clicking `start.bat` flashes and closes | Python isn't on PATH (see above), or the `.bat` isn't in the same folder as the scripts. Run `python "哦~土豆~~.py"` in cmd to see the error. |
| 找不到 token / Token file not found | `token.txt` must be in the project folder, and you must run from that folder. |
| `invalidtoken` / "not a file (token invalid?)" | Your token is wrong or expired. Get a new one and replace the content of `token.txt`. |
| Chinese text looks garbled | Run `chcp 65001` first, or use Windows Terminal. The launcher already sets UTF-8 for child scripts. |
| `'notebooklm' is not recognized` | The library isn't installed, or Python's `Scripts` folder isn't on PATH. Reinstall with `python -m pip install "notebooklm-py[browser]"`, then restart cmd. |
| `Authentication expired` | Just run tool 5 again; it logs in each time. If it still fails, run `notebooklm login` manually. |
| NotebookLM says rate-limited / stops early | Quota used up. Wait, then run again. It resumes automatically. |
| A file never uploads | It's skipped after 3 tries (too big, corrupted, or unsupported). Check it opens locally; re-run later. |
| Python says `unsupported operand type(s) for \|` | Your Python is older than 3.10. Upgrade. |

---

<div align="center">

Made with 🥔 for surviving university. PRs and issues welcome.

[↑ Back to top](#-spectrum-toolbox--哦土豆-妙妙工具箱) · [中文](#中文)

</div>

---
---

<a id="中文"></a>

# 中文

## 这个工具箱有什么

| 菜单编号 | 工具 | 脚本 | 功能 |
|:--:|------|------|------|
| 1 | 签到 | `att.py` | 自动打开"**现在正在上**的那门课"的 Attendance 页面。最后勾选 Present 并提交，仍由你自己在网页上完成。 |
| 2 | 看公告 | `spectrum_announcements.py` | "Today's News"（近 48 小时）+ 各课程近 N 天公告，输入序号即可在浏览器打开。 |
| 3 | 查 ddl | `moodle_deadlines.py` | 所有作业 / Quiz 按紧急程度排序（待提交 / 已过期未交 / 已提交）。 |
| 4 | 下载课程资料 | `spectrum_download.py` | 把新增或更新过的 PDF / PPT / PPTX 下载到 `UM_Courses/`，已有的不会重复下载。 |
| 5 | 更新 notebook | `notebooklm_pipeline.py` | 让 NotebookLM 云端和本地 `Week N` 文件夹保持一致，并按周生成 quiz 和闪卡。 |
| – | 启动菜单 | `哦~土豆~~.py` + `start.bat` | 一键菜单，双击 `start.bat` 即可进入。 |

> [!NOTE]
> 这是个人自用的非官方项目，与马来亚大学、Moodle、Google、NotebookLM 均无关联。"签到"只是**打开**签到页面，不会替你签到。"更新 notebook"依赖非官方库 [`notebooklm-py`](https://pypi.org/project/notebooklm-py/)，它使用的是未公开的 Google 接口，随时可能失效。使用风险自负，并请遵守学校规定。

---

## 第一部分 · 快速开始（手把手）

> 以下以 **Windows** 为例。macOS / Linux 上脚本同样能跑，只是把 `python` 换成 `python3`，用 `python3 "哦~土豆~~.py"` 代替 `start.bat` 启动。

### 第 1 步 · 安装 Python（3.10 或更新）

1. 到 <https://www.python.org/downloads/> 下载 Python。
2. 运行安装程序，第一页**务必勾选 "Add python.exe to PATH"**（最容易漏的一步）。
3. 新开一个命令提示符（按 `Win + R`，输入 `cmd`，回车），检查：

```cmd
python --version
```

看到类似 `Python 3.12.x` 就对了。如果提示 *"'python' 不是内部或外部命令"*，说明没勾 PATH，重新安装并勾上。

### 第 2 步 · 获取文件

可以用 git 克隆：

```cmd
git clone https://github.com/YOUR_NAME/YOUR_REPO.git
```

也可以在 GitHub 页面点 **Code → Download ZIP**，解压到任意位置（比如 `D:\spectrum-toolbox`）。

然后在**这个文件夹里**打开命令提示符：

```cmd
cd /d "D:\spectrum-toolbox"
```

> 💡 小技巧：在资源管理器里打开该文件夹，点地址栏，输入 `cmd` 回车，就会直接在此处打开。

### 第 3 步 · 安装依赖库

工具 1–4 只需要一个库：

```cmd
pip install requests
```

工具 5（NotebookLM）还需要下面两步，**不用 NotebookLM 的话可以跳过**：

```cmd
pip install "notebooklm-py[browser]"
playwright install chromium
```

第二条命令会下载约 170 MB 的浏览器（用于登录 Google），不显示进度条，请耐心等 30–90 秒。

> 如果提示找不到 `pip`，把命令改成 `python -m pip install requests`（另外两条同理）。

### 第 4 步 · 放入你的 Moodle token

脚本通过你的个人 **Moodle 移动端 web service token**（而不是密码）访问 Spectrum。

1. 在浏览器登录 Spectrum。
2. 打开个人菜单 → **Preferences（偏好设置）→ Security keys（安全密钥）**，复制 **Moodle mobile web service** 对应的密钥。不同版本/站点的位置可能略有差异。
3. 在**项目文件夹**里新建 `token.txt`，把 token 粘贴成**一行**：

```cmd
notepad token.txt
```

（记事本询问是否创建文件时点"是"，粘贴 token，保存。）

> [!WARNING]
> - **只写一行，只写 token**，不要加网址或注释。（只有 `att.py` 支持可选的"两行格式"，其他脚本会把整个文件当成 token，导致失败。）
> - token 的权限等同于你的密码。**绝对不要把 `token.txt` 上传到 GitHub**，也不要发给别人。详见 [安全提醒](#安全提醒上传-github-之前)。

### 第 5 步 · 启动

双击 **`start.bat`**，或者在 cmd 里运行：

```cmd
python "哦~土豆~~.py"
```

你会看到菜单：

```
====================================
        哦~土豆~~  妙妙工具箱
====================================
请选择您的妙妙工具：
  1. 签到
  2. 看公告
  3. 查ddl
  4. 下载课程资料
  5. 更新notebook
  0. 退出
```

输入编号回车即可。工具运行结束后按回车返回菜单；输入 `0` 或 `q` 退出。

### 第 6 步 · 每个工具的首次设置

按下面的顺序，每个只需做一次：

| 顺序 | 工具 | 怎么做 |
|:--:|------|--------|
| ① | **4 · 下载资料** | 菜单里选 4，输入要下载的课程编号（如 `1 3 5`，或 `all`）。选择会被记住，下次直接回车。 |
| ② | **3 · 查 ddl** / **2 · 看公告** | 不需要设置，直接运行。 |
| ③ | **1 · 签到** | 需要在 cmd 里做一次性设置（菜单不能传参数）：先 `python att.py sync`，再对每门课 `python att.py sched ...`。见 [att.py](#1--attpy--签到)。 |
| ④ | **5 · NotebookLM** | 需要第 3 步里的 NotebookLM 依赖、`prompts` 文件夹和 Google 登录。见 [notebooklm_pipeline.py](#5--notebooklm_pipelinepy--同步-notebooklm)。 |

### 文件夹最终长这样

```
spectrum-toolbox/
├─ start.bat                    ← 双击我
├─ 哦~土豆~~.py                  ← 菜单
├─ att.py
├─ spectrum_announcements.py
├─ moodle_deadlines.py
├─ spectrum_download.py
├─ notebooklm_pipeline.py
├─ token.txt                    ← 你自己创建（千万别提交）
├─ .att.json                    ← 自动生成：保存的签到页面和上课时间
├─ hidden_tasks.json            ← 自动生成：你隐藏的 ddl
├─ prompts/                     ← 你自己创建（给 NotebookLM 用）
│  ├─ quiz.txt
│  └─ flashcards.txt
└─ UM_Courses/                  ← 下载脚本自动生成
   ├─ downloaded.json           ← 下载脚本的"记忆"（别删）
   ├─ selected_courses.json     ← 你选的课程
   └─ 129_WIA2001/
      ├─ Week 1/
      ├─ Week 2/
      └─ EXAM/
```

---

## 第二部分 · 各脚本使用说明

> **重要：** 菜单运行脚本时**不带任何参数**。想用参数或子命令，请在**项目文件夹**里打开 cmd，直接运行对应脚本（见下）。务必在项目文件夹里运行，因为好几个脚本是按"当前文件夹"去找 `token.txt` 和 `UM_Courses/` 的。

### 1 · `att.py` — 签到

打开"当前正在上的课"的 Attendance 页面。勾选 *Present* 并提交仍然由**你**在网页上完成。

**一次性设置**

```cmd
python att.py sync
```

抓取你所有未结束课程里对你可见的 Attendance 页面。每个学期重新跑一次即可，已设置的上课时间会保留。

然后告诉它每门课什么时候上（24 小时制 `HH:MM`，星期用 `mon tue wed thu fri sat sun`）。一门课可以设置多个时间：

```cmd
python att.py list
python att.py sched 1 mon 10:00
python att.py sched wia2001 thu 14:00
```

（`1` 是 `list` 里的序号，也可以用课程名关键词，如 `wia2001`。）

**日常使用**

| 命令 | 作用 |
|------|------|
| `python att.py`（或菜单 **1**） | 只显示"现在正在上"的课（上课前 **15 分钟**到开始后 **2 小时**内），回车即可打开。 |
| `python att.py hsm` | 按名字模糊匹配并直接打开，不看时间。 |
| `python att.py list` | 列出所有已保存的签到页面。 |
| `python att.py sched <序号/关键词> <星期> <HH:MM>` | 添加一个上课时间。 |
| `python att.py unsched <序号/关键词> <星期> <HH:MM>` | 删除其中一个时间。 |
| `python att.py unsched <序号/关键词> all` | 清空这门课的所有时间。 |
| `python att.py add <名字> <url>` | 手动补一个页面，如 `.../mod/attendance/view.php?id=1126419`。 |
| `python att.py rm <序号/关键词>` | 删除一个已保存的页面。 |

**注意事项**
- 用的是**你电脑的系统时间和时区**，请确认它们没错。
- 现在没有课的时候，它只会打印一句（搞怪的）话然后退出，属于正常现象。
- 设置保存在脚本同目录的 `.att.json`。

### 2 · `spectrum_announcements.py` — 看公告

```cmd
python spectrum_announcements.py                :: 最近 14 天（默认）
python spectrum_announcements.py --days 7       :: 最近 7 天
python spectrum_announcements.py --all-courses  :: 连"非进行中"的课程也包含
```

- **Today's News**（近 48 小时）用字母 `a, b, c…` 编号；下面按课程列出的近 N 天公告用数字 `1, 2, 3…` 编号。
- 输入字母或数字回车，就会在浏览器里打开。可以一次开多个（`a 2 5` 或 `a,2,5`），`q` 退出。
- 回帖会显示为 `标题-回帖1`、`标题-回帖2`…，打开后直接跳到那一条回复。

### 3 · `moodle_deadlines.py` — 查 ddl

```cmd
python moodle_deadlines.py              :: 显示全部三块
python moodle_deadlines.py --pending    :: 只显示还没交的
python moodle_deadlines.py --no-open    :: 只显示列表，不进入交互
python moodle_deadlines.py --debug      :: 打印每门课的统计，用来排查"为什么作业这么少"
```

列表分三块：**待提交** → **已过期未交** → **已提交**（迟交的会标注）。图例：🔴 <1 天 · 🟠 <3 天 · 🟡 <7 天 · 🟢 >7 天 · ⚪ 无 deadline · ⚫ 已过期 · ✅ 已提交。

在 `>` 提示符下可以输入：

| 输入 | 效果 |
|------|------|
| `1 3` 或 `1,3` | 在浏览器打开第 1、3 项 |
| `d 2 4` | **隐藏**第 2、4 项，以后都不再出现（记录在 `hidden_tasks.json`） |
| `r` | 查看已隐藏的任务并恢复（下次运行时重新出现） |
| `l` | 重新显示列表 |
| `q` 或直接回车 | 退出 |

**注意事项**
- 时间按马来西亚时间（UTC+8）显示。
- deadline 已经过去超过 200 天的条目不会显示，可在脚本顶部修改 `MAX_PAST_DAYS`。
- 如果识别出来的课程不对，把正确的课程 ID 填到脚本顶部的 `INCLUDE_COURSE_IDS`（脚本运行时会打印它识别到的课程 ID）。
- 删除 `hidden_tasks.json` 就等于取消所有隐藏。

### 4 · `spectrum_download.py` — 下载课程资料

```cmd
python spectrum_download.py
python spectrum_download.py --restore-missing
```

首次运行：按编号选课。之后运行：直接回车沿用上次的选择，输入 `n` 重新选择。

- **只下载新增或更新过的文件**，存放在 `UM_Courses/<课程ID>_<简称>/<章节名>/`。
- 文件类型：`.pdf`、`.ppt`、`.pptx`。在 Spectrum 上显示名以 **"Tutorial"** 开头的资料，额外允许 `.docx`。
- **WIX2001 特例：** *Lecture Notes* 章节会按 `L1`、`L2`… 的标记自动分到 `Week 1`、`Week 2`… 文件夹。想给其他课程也启用，把课程代码加到脚本顶部的 `WEEK_SORT_COURSES`。
- 每次下载之间间隔 1.5 秒（对服务器友好）。没下完的文件以 `.part` 结尾，成功后自动改名。
- **误删了文件？** 加参数 `--restore-missing`，把本地缺失的文件重新下载回来。不加这个参数的话，你删掉 / 改名 / 移走的文件**不会**被重新下载（除非老师更新了它）。
- 除了 `token.txt`，也可以用环境变量 `MOODLE_TOKEN` 提供 token。

### 5 · `notebooklm_pipeline.py` — 同步 NotebookLM

让云端和本地文件夹保持一致，并**按周生成一份 quiz + 一份闪卡**。它不依赖任何状态文件：每次运行都是"看本地有什么、看云端有什么、把差的补齐"。中途被打断的话，重新运行就好。

**第一次运行之前**

1. 安装依赖（上面第 3 步）：`notebooklm-py[browser]` + `playwright install chromium`。
2. 先用工具 4 下载一些课件，让本地有 `Week N` 文件夹。
3. 新建 `prompts` 文件夹，里面放两个纯文本文件，写你给 NotebookLM 的指令：

   ```cmd
   mkdir prompts
   notepad prompts\quiz.txt
   notepad prompts\flashcards.txt
   ```

   `quiz.txt` 示例：*"根据这些课件的核心概念出 15 道选择题，并附上解析。"*
   如果文件不存在，脚本会提醒你，并使用 NotebookLM 的默认设置。
4. 确认 `notebooklm` 命令可用：`notebooklm --help`。

**运行**

```cmd
python notebooklm_pipeline.py --dry-run   :: 只显示计划，不做任何改动（第一次务必先跑这个！）
python notebooklm_pipeline.py             :: 正式执行（有删除操作时会先问你）
python notebooklm_pipeline.py --yes       :: 正式执行，删除时不再询问
```

每次运行一开始都会执行 `notebooklm login`：会弹出浏览器让你登录 Google 账号，按终端里的提示操作即可。这样可以避免 "Authentication expired" 报错。

**它怎么判断该做什么**

| 本地文件夹（必须直接位于课程文件夹下） | 行为 |
|---|---|
| 名字里带 `week` + 数字（`Week 3`、`week 03`、`Week 3 (F2F)`） | 上传，并用这一周的文件生成该周的 **quiz + 闪卡**。 |
| 名字里带 `exam`（如 `EXAM`） | **只上传**，不生成 quiz/闪卡，留给你自己处理。 |
| 其他（`Introduction`、`General` 等） | 忽略。 |
| 课程文件夹名里带 `GKU` | 整门课跳过。 |

- 每门课一个笔记本，名字 = 课程代码（`129_WIA2001` → 笔记本 **`WIA2001`**），按名字查找，没有就新建。
- 支持的文件：`.pdf`、`.ppt`、`.pptx`、`.docx`（其他类型会跳过并提示）。以 `~` 或 `.` 开头的文件会被忽略。
- 云端来源的标题格式是 `文件名 [#a1b2c3]`，这个标签是文件**内容**的指纹，脚本靠它判断两个文件是不是同一个。
- 处理顺序：先做所有课的最小周（所有课的 Week 1，再所有课的 Week 2……），这样就算当天额度用完，前面的周也已经做好了。
- 最多同时上传 6 个文件，单个文件最多等 60 秒、最多试 3 次；一直传不上去的文件会先跳过，不影响其他文件。
- 被 NotebookLM 限速时，会等 5 秒重试一次，仍不行就终止。**等额度恢复后重新运行**，会自动接着做。
- 只有当某一周云端的文件真的变了，才会重新生成 quiz/闪卡。

#### ⚠️ 使用云端 NotebookLM 的注意事项

1. **不要在 NotebookLM 网页上给来源改名。** 标题里的 `[#哈希]` 是识别文件的依据，没有它的来源会被当成"多余的"删掉。
2. **不要往这些笔记本里手动添加自己的来源**（链接、YouTube、粘贴的文字、额外文件）。凡是脚本没放进去的，都会被当成多余内容，下次运行时**会被删除**。想放自己的东西，请另建一个笔记本。
3. **不要把自己做的 quiz 命名为 `Week N - Quiz` / `Week N - Flashcards`。** 脚本会把这种名字认成自己生成的，可能覆盖或删除。为保险起见，手动生成的 quiz 请放在别的笔记本里，或者基于 `EXAM` 来源制作（脚本从不碰这些）。
4. **删除操作也会发生在云端。** 本地文件没了，下次同步就会删掉它对应的云端来源（除非加 `--yes`，否则会先让你确认）。整理过文件夹之后，务必先 `--dry-run`。
5. **不要给课程文件夹改名**（见下方表格），因为笔记本名字是从它推出来的。
6. **额度：** NotebookLM 对每个笔记本和每天的生成次数有限制，具体取决于你的套餐。用完了就等一等再运行。
7. 脚本**只管理 quiz 和闪卡**，音频概览、思维导图等从不触碰。

---

## 第三部分 · 在 `UM_Courses/` 里增删改查要注意什么

本地的 `UM_Courses/` 就是**"唯一真相"**：工具 5 会让 NotebookLM 向它看齐；工具 4 则在 `UM_Courses/downloaded.json` 里记着一本"日记"。下面是每种操作的影响：

| 你的操作 | 工具 4（下载） | 工具 5（NotebookLM） |
|---|---|---|
| **查看** | — | —（用资源管理器，或 `tree /F UM_Courses` 即可） |
| **往 `Week N/` 里添加自己的文件**（PDF/PPT/PPTX/DOCX） | 不管它。 | 下次同步会上传，并**重新生成**该周的 quiz + 闪卡。 |
| **往 `EXAM/` 里添加文件** | 不管它。 | 只上传。 |
| **删除文件** | **不会**重新下载（除非老师更新了它）；用 `--restore-missing` 可找回。 | 云端对应来源被删除，该周 quiz + 闪卡重新生成。👍 *想让某个文件不参与出题，就这样做。* |
| **重命名文件**（内容不变） | 不会重新下载。 | 无变化（按内容识别），云端保留旧标题。 |
| **修改文件**（如在 PDF 上做批注再保存） | 不会重新下载；但老师之后若更新了该文件，下载会**覆盖你的修改**。 | 内容变了 → 删旧来源、传新来源、该周**重新生成**。想避免的话，把批注版放到名字里不含 "week"/"exam" 的文件夹（如 `My Notes/`）。 |
| **把文件移到另一个 `Week N/`** | 不会重新下载；老师之后若更新该文件，新版会写回**原来的位置**（可能出现两份）。 | 涉及的两周都会重新生成。 |
| **给周文件夹改名**，如 `Week 3` → `Week 03` | 之后的新文件会再按 Spectrum 上的章节名存放。 | 没问题，周数相同就是同一周。改的是*数字*则整周文件会被当成另一周。 |
| **给课程文件夹改名**（`129_WIA2001`） | 会和 `downloaded.json` 里的记录对不上。 | 笔记本名取自 `129_` 后面的部分，改名会**新建一个笔记本**，旧的留在云端不动。**请不要改。** |
| **移走整个课程文件夹**（如上学期的课） | 除非你再次选这门课且 `downloaded.json` 里没有记录，否则不会重新下载。 | 该课程不再被扫描，云端笔记本原样保留。 |
| **删除 `downloaded.json`** | 所有文件都会重新下载一遍。 | 内容相同的文件不会重复上传。 |
| **删除整个 `UM_Courses/`** | 全部重新下载，并且忘记你选过的课程。 | 本地没了，同步前一定先 `--dry-run`！ |

**黄金法则**
1. 🗂️ 所有命令都在**项目文件夹**里运行。
2. ✅ 先下载（工具 4），再同步（工具 5）。
3. 🧹 先整理本地文件，**再**同步，同步前先 `--dry-run` 预览。
4. 🔒 个人笔记放在名字里**不含** "Week" / "EXAM" 的文件夹。
5. 🚫 不要手动改 `downloaded.json`，也不要在 NotebookLM 网页上给来源改名。

---

## 安全提醒（上传 GitHub 之前）

**第一次提交之前**，先在脚本旁边新建 `.gitignore`：

```gitignore
token.txt
token.text
.att.json
hidden_tasks.json
UM_Courses/
prompts/
__pycache__/
```

- `token.txt` 是你 Spectrum 账号的钥匙。万一泄露了，到 Spectrum 的安全密钥页面重新生成一个。
- NotebookLM / Google 的登录信息由 `notebooklm-py` 保存在你的用户目录里（不在本项目内），不会被提交，但同样不要分享。
- 课件的版权属于老师，请不要公开 `UM_Courses/`。

---

## 常见问题

| 问题 | 解决办法 |
|---|---|
| `'python' 不是内部或外部命令` | 重装 Python 并勾选 **Add python.exe to PATH**，然后*新开*一个 cmd 窗口。 |
| `'pip' 不是内部或外部命令` | 改用 `python -m pip install ...`。 |
| `No module named 'requests'` | `pip install requests` |
| 双击 `start.bat` 一闪而过 | Python 没加到 PATH（见上），或者 `.bat` 不在脚本所在文件夹。在 cmd 里运行 `python "哦~土豆~~.py"` 查看具体报错。 |
| 找不到 token | `token.txt` 必须在项目文件夹里，并且要在该文件夹里运行脚本。 |
| `invalidtoken` /"服务器返回的不是文件" | token 错了或过期了。重新获取，替换 `token.txt` 的内容。 |
| 中文乱码 | 先运行 `chcp 65001`，或改用 Windows Terminal。菜单启动时已经为子脚本设置了 UTF-8。 |
| `'notebooklm' 不是内部或外部命令` | 库没装好，或 Python 的 `Scripts` 文件夹不在 PATH 里。用 `python -m pip install "notebooklm-py[browser]"` 重装，然后重开 cmd。 |
| `Authentication expired` | 重新运行工具 5（每次都会登录）。仍然不行就手动运行 `notebooklm login`。 |
| NotebookLM 提示限速 / 中途停止 | 额度用完了，等恢复后再运行，会自动接着做。 |
| 某个文件一直传不上去 | 试 3 次后会被跳过（可能太大、损坏或格式不支持）。确认它在本地能打开，稍后再运行。 |
| 报错 `unsupported operand type(s) for \|` | Python 版本低于 3.10，请升级。 |

---

<div align="center">

为了在大学里活下去而做的 🥔。欢迎 PR 和 Issue。

[↑ 回到顶部](#-spectrum-toolbox--哦土豆-妙妙工具箱) · [English](#english)

</div>
