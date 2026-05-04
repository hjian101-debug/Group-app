from flask import Flask, request, redirect, render_template_string, send_file
import json
import os
import random
import qrcode
from io import BytesIO

app = Flask(__name__)

JOIN_URL = "https://group-app-55j5.onrender.com/join"
NEW_FRIENDS_FILE = "new_friends.json"
MEMBERS_FILE = "members.json"

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


def load_members():
    members = load_json(MEMBERS_FILE, DEFAULT_MEMBERS)
    save_json(MEMBERS_FILE, members)
    return members


def load_new_friends():
    return load_json(NEW_FRIENDS_FILE, [])


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
        if name:
            new_friends = load_new_friends()
            members = load_members()

            if name not in new_friends and name not in members:
                new_friends.append(name)
                save_json(NEW_FRIENDS_FILE, new_friends)

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
            <br>
            <button type="submit">提交</button>
        </form>
    </div>
</body>
</html>
"""


@app.route("/admin", methods=["GET", "POST"])
def admin():
    members = load_members()
    new_friends = load_new_friends()
    groups = None
    selected_members = []

    if request.method == "POST":
        selected_members = request.form.getlist("members")
        group_count = int(request.form.get("group_count", 1))

        all_people = selected_members + new_friends
        random.shuffle(all_people)

        groups = [[] for _ in range(group_count)]
        for i, name in enumerate(all_people):
            groups[i % group_count].append(name)

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

        .member-actions {
            margin-bottom: 18px;
        }

        .member-actions button {
            margin-right: 10px;
        }

        .member-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 12px;
        }

        .member-card {
            background: white;
            padding: 10px 12px;
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

        .small-btn {
            font-size: 13px;
            padding: 6px 10px;
        }

        .delete-btn {
            background: #e53e3e;
        }

        .delete-btn:hover {
            background: #c53030;
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
        }
    </style>

    <script>
        function selectAllMembers() {
            const boxes = document.querySelectorAll('input[name="members"]');
            boxes.forEach(box => box.checked = true);
        }

        function unselectAllMembers() {
            const boxes = document.querySelectorAll('input[name="members"]');
            boxes.forEach(box => box.checked = false);
        }
    </script>
</head>

<body>
<div class="container">
    <h1>管理员页面</h1>

    <form method="post">
        <div class="section">
            <h2>常来成员：勾选今天来了的人</h2>

            <div class="member-actions">
                <button type="button" onclick="selectAllMembers()">全选</button>
                <button type="button" onclick="unselectAllMembers()">取消全选</button>
            </div>

            <div class="member-grid">
            {% for member in members %}
                <div class="member-card">
                    <div class="member-left">
                        <input type="checkbox" name="members" value="{{ member }}"
                        {% if member in selected_members %}checked{% endif %}>
                        <span>{{ member }}</span>
                    </div>

                    <a class="small-btn delete-btn"
                       href="/delete_member/{{ member }}"
                       onclick="return confirm('确定要删除 {{ member }} 吗？')">
                       删除
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
                        <a class="small-btn" href="/add_member/{{ friend }}">加入常来名单</a>
                    </div>
                {% endfor %}
            {% else %}
                <p>目前还没有新朋友报名。</p>
            {% endif %}
        </div>

        <div class="section">
            <h2>开始分组</h2>
            <input type="number" name="group_count" min="1" placeholder="请输入分几组" required>
            <button type="submit">随机分组</button>
        </div>
    </form>

    {% if groups %}
        <div class="section">
            <h2>分组结果</h2>

            <div class="group-grid">
            {% for group in groups %}
                <div class="group">
                    <h3>第 {{ loop.index }} 组：{{ group|length }} 人</h3>
                    <ul>
                    {% for name in group %}
                        <li>{{ name }}</li>
                    {% endfor %}
                    </ul>
                </div>
            {% endfor %}
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
""", members=members, new_friends=new_friends, groups=groups, selected_members=selected_members)


@app.route("/add_member/<name>")
def add_member(name):
    members = load_members()
    new_friends = load_new_friends()

    if name not in members:
        members.append(name)
        save_json(MEMBERS_FILE, members)

    if name in new_friends:
        new_friends.remove(name)
        save_json(NEW_FRIENDS_FILE, new_friends)

    return redirect("/admin")


@app.route("/delete_member/<name>")
def delete_member(name):
    members = load_members()

    if name in members:
        members.remove(name)
        save_json(MEMBERS_FILE, members)

    return redirect("/admin")


@app.route("/clear_new_friends", methods=["POST"])
def clear_new_friends():
    save_json(NEW_FRIENDS_FILE, [])
    return redirect("/admin")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
