from flask import Flask, request, redirect, render_template_string, send_file
import json
import os
import random
import qrcode
from io import BytesIO

try:
    import psycopg
except ImportError:
    psycopg = None

app = Flask(__name__)

JOIN_URL = os.environ.get(
    "JOIN_URL", "https://good-friends-group-app.onrender.com/join"
)
NEW_FRIENDS_FILE = "new_friends.json"
NEW_FRIEND_STATUSES_FILE = "new_friend_statuses.json"
MEMBERS_FILE = "members.json"
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()

DEFAULT_MEMBERS = [
    "孙牧师", "师母", "胡老师", "京台姐", "Henry", "春霞", "Monica", "新业",
    "璐瑶", "Luisa", "Harry", "边边", "一王", "贠芳", "Larry", "骆雨",
    "浩文", "Amy", "天艺", "沁沁", "迦南", "雅歌"
]


def load_json(filename, default):
    if not os.path.exists(filename):
        return default
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def use_database():
    return bool(DATABASE_URL)


def get_db():
    if psycopg is None:
        raise RuntimeError("DATABASE_URL is set, but psycopg is not installed")
    return psycopg.connect(DATABASE_URL)


def ensure_database():
    if not use_database():
        return

    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS people (
                name TEXT PRIMARY KEY,
                kind TEXT NOT NULL CHECK (kind IN ('member', 'new_friend')),
                faith_status TEXT NOT NULL DEFAULT 'christian'
                    CHECK (faith_status IN ('christian', 'seeker')),
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
        conn.execute(
            "ALTER TABLE people ADD COLUMN IF NOT EXISTS faith_status TEXT NOT NULL DEFAULT 'christian'"
        )
        conn.execute("""
            CREATE TABLE IF NOT EXISTS app_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        initialized = conn.execute(
            "SELECT 1 FROM app_metadata WHERE key = 'people_initialized'"
        ).fetchone()
        if not initialized:
            with conn.cursor() as cursor:
                cursor.executemany(
                    "INSERT INTO people (name, kind) VALUES (%s, 'member') ON CONFLICT DO NOTHING",
                    [(name,) for name in DEFAULT_MEMBERS],
                )
            conn.execute(
                "INSERT INTO app_metadata (key, value) VALUES ('people_initialized', 'true')"
            )


def load_people(kind):
    ensure_database()
    with get_db() as conn:
        rows = conn.execute(
            "SELECT name FROM people WHERE kind = %s ORDER BY created_at, name",
            (kind,),
        ).fetchall()
    return [row[0] for row in rows]


def load_faith_statuses():
    if use_database():
        ensure_database()
        with get_db() as conn:
            rows = conn.execute("SELECT name, faith_status FROM people").fetchall()
        return {name: status for name, status in rows}

    statuses = {name: "christian" for name in load_members()}
    saved = load_json(NEW_FRIEND_STATUSES_FILE, {})
    statuses.update({name: saved.get(name, "christian") for name in load_new_friends()})
    return statuses


def load_members():
    if use_database():
        return load_people("member")
    members = load_json(MEMBERS_FILE, DEFAULT_MEMBERS)
    save_json(MEMBERS_FILE, members)
    return members


def load_new_friends():
    if use_database():
        return load_people("new_friend")
    return load_json(NEW_FRIENDS_FILE, [])


def add_new_friend(name, faith_status="christian"):
    if faith_status not in ("christian", "seeker"):
        faith_status = "christian"
    if use_database():
        ensure_database()
        with get_db() as conn:
            conn.execute(
                """
                INSERT INTO people (name, kind, faith_status)
                VALUES (%s, 'new_friend', %s)
                ON CONFLICT (name) DO UPDATE
                SET faith_status = EXCLUDED.faith_status
                WHERE people.kind = 'new_friend'
                """,
                (name, faith_status),
            )
        return

    new_friends = load_new_friends()
    members = load_members()
    if name not in new_friends and name not in members:
        new_friends.append(name)
        save_json(NEW_FRIENDS_FILE, new_friends)
    statuses = load_json(NEW_FRIEND_STATUSES_FILE, {})
    if name not in members:
        statuses[name] = faith_status
        save_json(NEW_FRIEND_STATUSES_FILE, statuses)


def promote_to_member(name):
    if use_database():
        ensure_database()
        with get_db() as conn:
            conn.execute(
                """
                INSERT INTO people (name, kind)
                VALUES (%s, 'member')
                ON CONFLICT (name) DO UPDATE SET kind = 'member'
                """,
                (name,),
            )
        return

    members = load_members()
    new_friends = load_new_friends()
    if name not in members:
        members.append(name)
        save_json(MEMBERS_FILE, members)
    if name in new_friends:
        new_friends.remove(name)
        save_json(NEW_FRIENDS_FILE, new_friends)


def remove_member(name):
    if use_database():
        ensure_database()
        with get_db() as conn:
            conn.execute("DELETE FROM people WHERE name = %s AND kind = 'member'", (name,))
        return

    members = load_members()
    if name in members:
        members.remove(name)
        save_json(MEMBERS_FILE, members)


def remove_all_new_friends():
    if use_database():
        ensure_database()
        with get_db() as conn:
            conn.execute("DELETE FROM people WHERE kind = 'new_friend'")
        return
    save_json(NEW_FRIENDS_FILE, [])
    save_json(NEW_FRIEND_STATUSES_FILE, {})


@app.route("/")
def home():
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>Good Friends Fellowship</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea, #764ba2);
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }

        .card {
            background: white;
            padding: 45px 60px;
            border-radius: 24px;
            text-align: center;
            width: 760px;
            box-shadow: 0 20px 55px rgba(0,0,0,0.25);
            position: relative;
        }

        h1 {
            font-size: 34px;
            margin: 0 0 15px 0;
            color: #222;
            white-space: nowrap;
        }

        h2 {
            color: #555;
            font-size: 20px;
            margin-bottom: 25px;
        }

        .qr {
            width: 260px;
            margin: 15px 0 30px 0;
        }

        .photo {
            position: absolute;
            width: 460px;
            height: 320px;
            object-fit: cover;
            border: 8px solid white;
            border-radius: 14px;
            box-shadow: 0 14px 35px rgba(0,0,0,0.32);
            z-index: 2;
        }

        .left-photo {
            left: -220px;
            top: 140px;
            transform: rotate(-8deg);
        }

        .right-photo {
            right: -220px;
            top: 140px;
            transform: rotate(8deg);
        }

        .link-box {
            background: #f2f2f2;
            padding: 13px;
            border-radius: 11px;
            font-size: 15px;
            word-break: break-all;
            margin: 0 auto 25px auto;
            max-width: 520px;
        }

        .admin-btn {
            display: inline-block;
            padding: 14px 32px;
            background: #667eea;
            color: white;
            border-radius: 11px;
            text-decoration: none;
            font-size: 17px;
            font-weight: bold;
        }

        @media (max-width: 900px) {
            .card {
                width: 82%;
                padding: 35px 24px;
            }

            h1 {
                font-size: 24px;
                white-space: normal;
            }

            .qr {
                width: 230px;
            }

            .photo {
                display: none;
            }
        }
    </style>
</head>

<body>
    <div class="card">
        <img src="/static/photo1.jpg" class="photo left-photo">
        <img src="/static/photo2.jpg" class="photo right-photo">

        <h1>🎯 Good Friends Fellowship</h1>
        <h2>新朋友扫码填写姓名</h2>

        <img src="/qr" class="qr">

        <div>打不开二维码？复制链接：</div>
        <div class="link-box">{{ join_url }}</div>

        <a href="/admin" class="admin-btn">进入管理员页面</a>
    </div>
</body>
</html>
""", join_url=JOIN_URL)


@app.route("/qr")
def qr():
    img = qrcode.make(JOIN_URL)
    buf = BytesIO()
    img.save(buf)
    buf.seek(0)
    return send_file(buf, mimetype="image/png")


@app.route("/join", methods=["GET", "POST"])
def join():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        faith_status = request.form.get("faith_status", "christian")
        if name:
            add_new_friend(name, faith_status)

        return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>提交成功</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea, #764ba2);
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }

        .card {
            background: white;
            padding: 40px;
            border-radius: 20px;
            text-align: center;
            width: 360px;
            box-shadow: 0 12px 35px rgba(0,0,0,0.22);
        }
    </style>
</head>
<body>
    <div class="card">
        <h1>提交成功 ✅</h1>
        <p>你的名字是：<strong>{{ name }}</strong></p>
        <p>请等待分组。</p>
    </div>
</body>
</html>
""", name=name)

    return """
<!DOCTYPE html>
<html>
<head>
    <title>填写姓名</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea, #764ba2);
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }

        .card {
            background: white;
            padding: 40px;
            border-radius: 20px;
            text-align: center;
            width: 360px;
            box-shadow: 0 12px 35px rgba(0,0,0,0.22);
        }

        input {
            width: 90%;
            padding: 14px;
            font-size: 18px;
            border-radius: 10px;
            border: 1px solid #ccc;
            margin-bottom: 20px;
        }

        .faith-options {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            margin-bottom: 22px;
            text-align: left;
        }

        .faith-option {
            background: #f2f3ff;
            padding: 14px;
            border-radius: 10px;
            font-size: 17px;
        }

        .faith-option input {
            width: auto;
            margin: 0 7px 0 0;
        }

        button {
            padding: 13px 30px;
            font-size: 18px;
            border: none;
            border-radius: 10px;
            background: #667eea;
            color: white;
            cursor: pointer;
        }
    </style>
</head>

<body>
    <div class="card">
        <h1>填写姓名</h1>
        <form method="post">
            <input name="name" placeholder="请输入你的姓名" required>
            <div class="faith-options">
                <label class="faith-option"><input type="radio" name="faith_status" value="christian" required>基督徒</label>
                <label class="faith-option"><input type="radio" name="faith_status" value="seeker" required>慕道友</label>
            </div>
            <button type="submit">提交</button>
        </form>
    </div>
</body>
</html>
"""


def build_balanced_groups(attendees, leaders, faith_statuses, group_count):
    groups = [[leader] for leader in leaders]
    christian_counts = [
        1 if faith_statuses.get(leader, "christian") == "christian" else 0
        for leader in leaders
    ]
    remaining = [name for name in attendees if name not in leaders]
    christians = [name for name in remaining if faith_statuses.get(name, "christian") == "christian"]
    seekers = [name for name in remaining if faith_statuses.get(name, "christian") != "christian"]
    random.shuffle(christians)
    random.shuffle(seekers)

    for name in christians:
        target = min(range(group_count), key=lambda i: (christian_counts[i], len(groups[i])))
        groups[target].append(name)
        christian_counts[target] += 1

    for name in seekers:
        target = min(range(group_count), key=lambda i: (len(groups[i]), christian_counts[i]))
        groups[target].append(name)

    return groups


@app.route("/admin", methods=["GET", "POST"])
def admin():
    members = load_members()
    new_friends = load_new_friends()
    faith_statuses = load_faith_statuses()
    groups = None
    group_count = None
    group_christian_counts = []
    selected_members = []
    leaders = []
    error = None

    if request.method == "POST":
        selected_members = request.form.getlist("members")
        group_count = int(request.form.get("group_count", 1))
        leaders = request.form.getlist("leaders")
        all_people = list(dict.fromkeys(selected_members + new_friends))

        if len(leaders) != group_count or len(set(leaders)) != group_count:
            error = "请为每一组选择一位不同的组长。"
        elif any(leader not in selected_members for leader in leaders):
            error = "组长必须是今天已勾选的常来成员。"
        else:
            groups = build_balanced_groups(
                all_people, leaders, faith_statuses, group_count
            )
            group_christian_counts = [
                sum(faith_statuses.get(name, "christian") == "christian" for name in group)
                for group in groups
            ]

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>管理员页面</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #f4f5fb;
            padding: 30px;
        }

        .container {
            max-width: 1200px;
            margin: auto;
            background: white;
            padding: 35px;
            border-radius: 18px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.12);
        }

        h1, h2 {
            color: #222;
        }

        .section {
            background: #f7f7f7;
            padding: 22px;
            border-radius: 14px;
            margin-bottom: 30px;
        }

        .add-friend-form {
            display: flex;
            gap: 12px;
        }

        .add-friend-form input {
            flex: 1;
            min-width: 0;
            padding: 12px 14px;
            font-size: 16px;
            border: 1px solid #ccc;
            border-radius: 8px;
        }

        .faith-select {
            display: flex;
            align-items: center;
            gap: 14px;
            background: white;
            padding: 10px 14px;
            border-radius: 8px;
        }

        .faith-select label {
            white-space: nowrap;
        }

        .leader-selects {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
            gap: 12px;
            margin: 18px 0;
        }

        .leader-selects label {
            display: flex;
            flex-direction: column;
            gap: 7px;
            font-weight: bold;
        }

        .leader-selects select {
            padding: 11px;
            font-size: 16px;
            border: 1px solid #ccc;
            border-radius: 8px;
            background: white;
        }

        .error-message {
            background: #fff0f0;
            color: #b42318;
            padding: 12px 15px;
            border-radius: 8px;
            margin-bottom: 16px;
        }

        .status-badge, .leader-badge {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 999px;
            font-size: 13px;
            margin-left: 7px;
        }

        .status-badge {
            background: #edf0ff;
            color: #4c5fc7;
        }

        .leader-badge {
            background: #fff1bd;
            color: #7a5b00;
            font-weight: bold;
        }

        .member-actions {
            margin-bottom: 18px;
        }

        .member-actions button {
            margin-right: 10px;
        }

        .member-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(155px, 1fr));
            gap: 12px;
        }

        .member-card {
            background: white;
            padding: 12px 14px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
        }

        .member-left {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        input[type="checkbox"] {
            transform: scale(1.2);
        }

        input[type="number"] {
            padding: 11px;
            font-size: 16px;
            border-radius: 8px;
            border: 1px solid #ccc;
        }

        button, .small-btn {
            padding: 10px 18px;
            font-size: 16px;
            border: none;
            border-radius: 8px;
            background: #667eea;
            color: white;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
        }

        .delete-toggle-btn {
            background: #e53e3e;
        }

        .delete-toggle-btn:hover {
            background: #c53030;
        }

        .delete-x {
            display: none;
            color: white;
            background: #e53e3e;
            text-decoration: none;
            font-size: 18px;
            font-weight: bold;
            width: 28px;
            height: 28px;
            line-height: 28px;
            text-align: center;
            border-radius: 50%;
        }

        .delete-mode .delete-x {
            display: inline-block;
        }

        .clear-btn {
            background: #e53e3e;
        }

        .group-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 22px;
        }

        .group {
            background: #f2f3ff;
            padding: 20px;
            border-radius: 14px;
            min-height: 160px;
            transition: background 0.2s, outline 0.2s;
        }

        .group.drag-over {
            background: #e3e6ff;
            outline: 3px dashed #667eea;
        }

        .group h3 {
            margin-top: 0;
        }

        .group-list {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .group-member {
            background: white;
            padding: 11px 12px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            cursor: grab;
        }

        .move-btn {
            padding: 8px 13px;
            font-size: 14px;
            white-space: nowrap;
        }

        .move-sheet-backdrop {
            display: none;
            position: fixed;
            inset: 0;
            background: rgba(0, 0, 0, 0.42);
            z-index: 20;
            align-items: flex-end;
            justify-content: center;
        }

        .move-sheet-backdrop.open {
            display: flex;
        }

        .move-sheet {
            background: white;
            width: min(520px, 100%);
            padding: 24px;
            border-radius: 22px 22px 0 0;
            box-shadow: 0 -8px 30px rgba(0,0,0,0.2);
        }

        .move-sheet h3 {
            margin-top: 0;
        }

        .move-options {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
        }

        .move-options button {
            min-height: 52px;
        }

        .cancel-move {
            width: 100%;
            margin-top: 14px;
            background: #777;
        }

        .adjust-help {
            color: #555;
            margin-top: -8px;
            margin-bottom: 18px;
        }

        .new-friend {
            background: white;
            padding: 12px;
            border-radius: 10px;
            margin: 8px 0;
        }

        @media (max-width: 700px) {
            .group-grid {
                grid-template-columns: 1fr;
            }

            .container {
                padding: 20px;
            }

            .add-friend-form {
                flex-direction: column;
            }

            .add-friend-form button {
                min-height: 48px;
            }

            .faith-select {
                justify-content: space-around;
            }
        }
    </style>

    <script>
        function selectAllMembers() {
            const boxes = document.querySelectorAll('input[name="members"]');
            boxes.forEach(box => box.checked = true);
            updateLeaderSelects();
        }

        function unselectAllMembers() {
            const boxes = document.querySelectorAll('input[name="members"]');
            boxes.forEach(box => box.checked = false);
            updateLeaderSelects();
        }

        function toggleDeleteMode() {
            const memberSection = document.getElementById("member-section");
            memberSection.classList.toggle("delete-mode");
        }

        function updateGroupCounts() {
            document.querySelectorAll(".group").forEach(group => {
                const count = group.querySelectorAll(".group-member").length;
                group.querySelector(".group-count").textContent = count;
                const christianCount = group.querySelectorAll('.group-member[data-faith="christian"]').length;
                group.querySelector(".christian-count").textContent = christianCount;
            });
        }

        let selectedMember = null;

        function moveMemberTo(member, targetGroup) {
            const targetList = document.querySelector(
                `.group[data-group="${targetGroup}"] .group-list`
            );

            if (!targetList) return;
            targetList.appendChild(member);
            member.dataset.group = targetGroup;
            updateGroupCounts();
        }

        function openMoveSheet(button) {
            selectedMember = button.closest(".group-member");
            document.getElementById("move-member-name").textContent = selectedMember.dataset.name;
            document.getElementById("move-sheet-backdrop").classList.add("open");
        }

        function closeMoveSheet() {
            document.getElementById("move-sheet-backdrop").classList.remove("open");
            selectedMember = null;
        }

        function chooseTargetGroup(groupNumber) {
            if (selectedMember) moveMemberTo(selectedMember, groupNumber);
            closeMoveSheet();
        }

        function startMemberDrag(event) {
            selectedMember = event.currentTarget;
            event.dataTransfer.effectAllowed = "move";
        }

        function allowGroupDrop(event) {
            event.preventDefault();
            event.currentTarget.classList.add("drag-over");
        }

        function leaveGroupDrop(event) {
            event.currentTarget.classList.remove("drag-over");
        }

        function dropMember(event) {
            event.preventDefault();
            event.currentTarget.classList.remove("drag-over");
            if (selectedMember) moveMemberTo(selectedMember, event.currentTarget.dataset.group);
            selectedMember = null;
        }

        function updateLeaderSelects() {
            const countInput = document.querySelector('input[name="group_count"]');
            const container = document.getElementById("leader-selects");
            const groupCount = Math.max(0, parseInt(countInput.value || "0", 10));
            const currentSelections = Array.from(container.querySelectorAll("select")).map(select => select.value);
            const previous = currentSelections.length ? currentSelections : {{ leaders|tojson }};
            const attendees = Array.from(document.querySelectorAll('input[name="members"]:checked'))
                .map(box => box.value);

            container.innerHTML = "";
            for (let i = 0; i < groupCount; i++) {
                const label = document.createElement("label");
                label.textContent = `第 ${i + 1} 组组长`;
                const select = document.createElement("select");
                select.name = "leaders";
                select.required = true;

                const placeholder = document.createElement("option");
                placeholder.value = "";
                placeholder.textContent = "请选择组长";
                select.appendChild(placeholder);

                attendees.forEach(name => {
                    const option = document.createElement("option");
                    option.value = name;
                    option.textContent = name;
                    if (previous[i] === name) option.selected = true;
                    select.appendChild(option);
                });
                label.appendChild(select);
                container.appendChild(label);
            }
        }

        document.addEventListener("DOMContentLoaded", () => {
            document.querySelector('input[name="group_count"]').addEventListener("input", updateLeaderSelects);
            document.querySelectorAll('input[name="members"]').forEach(box => {
                box.addEventListener("change", updateLeaderSelects);
            });
            updateLeaderSelects();
        });
    </script>
</head>

<body>
<div class="container">
    <h1>管理员页面</h1>

    <div class="section">
        <h2>添加新朋友</h2>
        <form class="add-friend-form" action="/admin/add_new_friend" method="post">
            <input type="text" name="name" placeholder="请输入新朋友姓名"
                   aria-label="新朋友姓名" autocomplete="off" required>
            <div class="faith-select">
                <label><input type="radio" name="faith_status" value="christian" required> 基督徒</label>
                <label><input type="radio" name="faith_status" value="seeker" required> 慕道友</label>
            </div>
            <button type="submit">添加新朋友</button>
        </form>
    </div>

    <form method="post">
        <div class="section" id="member-section">
            <h2>常来成员：勾选今天来了的人</h2>

            <div class="member-actions">
                <button type="button" onclick="selectAllMembers()">全选</button>
                <button type="button" onclick="unselectAllMembers()">取消全选</button>
                <button type="button" class="delete-toggle-btn" onclick="toggleDeleteMode()">删除成员</button>
            </div>

            <div class="member-grid">
            {% for member in members %}
                <div class="member-card">
                    <div class="member-left">
                        <input type="checkbox" name="members" value="{{ member }}"
                        {% if member in selected_members %}checked{% endif %}>
                        <span>{{ member }}</span>
                    </div>

                    <a class="delete-x"
                       href="/delete_member/{{ member }}"
                       onclick="return confirm('确定要删除 {{ member }} 吗？')">
                       ×
                    </a>
                </div>
            {% endfor %}
            </div>
        </div>

        <div class="section">
            <h2>新朋友名单：{{ new_friends|length }} 人</h2>

            {% if new_friends %}
                {% for friend in new_friends %}
                    <div class="new-friend">
                        {{ friend }}
                        <span class="status-badge">{{ '基督徒' if faith_statuses.get(friend) == 'christian' else '慕道友' }}</span>
                        <a class="small-btn" href="/add_member/{{ friend }}">加入常来名单</a>
                    </div>
                {% endfor %}
            {% else %}
                <p>目前还没有新朋友报名。</p>
            {% endif %}
        </div>

        <div class="section">
            <h2>开始分组</h2>
            {% if error %}<div class="error-message">{{ error }}</div>{% endif %}
            <p>先输入组数，再为每一组选择一位今天已勾选的组长。</p>
            <input type="number" name="group_count" min="1" max="20"
                   value="{{ group_count or '' }}" placeholder="请输入分几组" required>
            <div class="leader-selects" id="leader-selects"></div>
            <button type="submit">随机分组</button>
        </div>
    </form>

    {% if groups %}
        <div class="section">
            <h2>分组结果</h2>
            <p class="adjust-help">手机点“换组”选择目标组；电脑也可以直接拖动成员。</p>

            <div class="group-grid">
            {% for group in groups %}
                {% set group_number = loop.index %}
                <div class="group" data-group="{{ group_number }}"
                     ondragover="allowGroupDrop(event)" ondragleave="leaveGroupDrop(event)"
                     ondrop="dropMember(event)">
                    <h3>第 {{ group_number }} 组：<span class="group-count">{{ group|length }}</span> 人
                        · 基督徒 <span class="christian-count">{{ group_christian_counts[group_number - 1] }}</span> 人</h3>
                    <div class="group-list">
                    {% for name in group %}
                        <div class="group-member" data-group="{{ group_number }}" data-name="{{ name }}"
                             data-faith="{{ faith_statuses.get(name, 'christian') }}"
                             draggable="{{ 'false' if name == leaders[group_number - 1] else 'true' }}"
                             {% if name != leaders[group_number - 1] %}ondragstart="startMemberDrag(event)"{% endif %}>
                            <span>{{ name }}{% if name == leaders[group_number - 1] %}<span class="leader-badge">组长</span>{% endif %}</span>
                            {% if name != leaders[group_number - 1] %}<button type="button" class="move-btn" onclick="openMoveSheet(this)">换组</button>{% endif %}
                        </div>
                    {% endfor %}
                    </div>
                </div>
            {% endfor %}
            </div>
        </div>

        <div class="move-sheet-backdrop" id="move-sheet-backdrop" onclick="if (event.target === this) closeMoveSheet()">
            <div class="move-sheet" role="dialog" aria-modal="true" aria-labelledby="move-sheet-title">
                <h3 id="move-sheet-title">移动 <span id="move-member-name"></span> 到：</h3>
                <div class="move-options">
                {% for target in range(1, (groups|length) + 1) %}
                    <button type="button" onclick="chooseTargetGroup('{{ target }}')">第 {{ target }} 组</button>
                {% endfor %}
                </div>
                <button type="button" class="cancel-move" onclick="closeMoveSheet()">取消</button>
            </div>
        </div>
    {% endif %}

    <div class="section">
        <form action="/clear_new_friends" method="post">
            <button class="clear-btn" type="submit" onclick="return confirm('确定要清空新朋友名单吗？')">
                清空新朋友名单
            </button>
        </form>
    </div>
</div>
</body>
</html>
""", members=members, new_friends=new_friends, groups=groups,
       selected_members=selected_members, faith_statuses=faith_statuses,
       leaders=leaders, error=error, group_count=group_count,
       group_christian_counts=group_christian_counts)


@app.route("/add_member/<name>")
def add_member(name):
    promote_to_member(name)
    return redirect("/admin")


@app.route("/admin/add_new_friend", methods=["POST"])
def admin_add_new_friend():
    name = request.form.get("name", "").strip()
    faith_status = request.form.get("faith_status", "christian")
    if name:
        add_new_friend(name, faith_status)
    return redirect("/admin")


@app.route("/delete_member/<name>")
def delete_member(name):
    remove_member(name)
    return redirect("/admin")


@app.route("/clear_new_friends", methods=["POST"])
def clear_new_friends():
    remove_all_new_friends()
    return redirect("/admin")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
