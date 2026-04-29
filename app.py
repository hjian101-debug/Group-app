from flask import Flask, request, redirect, render_template_string, send_file
import json
import os
import random
import qrcode
from io import BytesIO

app = Flask(__name__)

DATA_FILE = "names.json"
JOIN_URL = "https://group-app-55j5.onrender.com/join"


def load_names():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_names(names):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(names, f, ensure_ascii=False, indent=2)


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
            width: 320px;
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
             left: -400px;
             top: 140px;
            transform: rotate(-8deg);
        }

        .right-photo {
            right: -400px;
            top: 140px;
            transform: rotate(8deg);
        }

        .link-title {
            font-size: 16px;
            margin-bottom: 10px;
            color: #333;
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

        .admin-btn:hover {
            background: #5a67d8;
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
        <h2>扫码填写你的姓名</h2>

        <img src="/qr" class="qr">

        <div class="link-title">打不开二维码？复制链接：</div>
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
            names = load_names()
            if name not in names:
                names.append(name)
                save_names(names)

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

        h1 {
            color: #222;
        }

        p {
            color: #555;
            font-size: 18px;
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

        h1 {
            color: #222;
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

        button:hover {
            background: #5a67d8;
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
    names = load_names()
    groups = None

    if request.method == "POST":
        group_count = int(request.form.get("group_count", 1))

        shuffled_names = names[:]
        random.shuffle(shuffled_names)

        groups = [[] for _ in range(group_count)]

        for i, name in enumerate(shuffled_names):
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
            max-width: 900px;
            margin: auto;
            background: white;
            padding: 30px;
            border-radius: 18px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.12);
        }

        h1 {
            color: #222;
        }

        .name-list {
            background: #f7f7f7;
            padding: 15px;
            border-radius: 12px;
        }

        input {
            padding: 10px;
            font-size: 16px;
            border-radius: 8px;
            border: 1px solid #ccc;
        }

        button {
            padding: 10px 18px;
            font-size: 16px;
            border: none;
            border-radius: 8px;
            background: #667eea;
            color: white;
            cursor: pointer;
        }

        button:hover {
            background: #5a67d8;
        }

        .group {
            background: #f2f3ff;
            padding: 15px;
            border-radius: 12px;
            margin: 15px 0;
        }

        .clear-btn {
            background: #e53e3e;
        }

        .clear-btn:hover {
            background: #c53030;
        }
    </style>
</head>

<body>
    <div class="container">
        <h1>管理员页面</h1>

        <h2>当前已报名人数：{{ names|length }}</h2>

        <div class="name-list">
            <ol>
            {% for name in names %}
                <li>{{ name }}</li>
            {% endfor %}
            </ol>
        </div>

        <hr>

        <h2>随机分组</h2>

        <form method="post">
            <input type="number" name="group_count" min="1" placeholder="请输入分几组" required>
            <button type="submit">开始分组</button>
        </form>

        {% if groups %}
            <hr>
            <h2>分组结果</h2>

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
        {% endif %}

        <hr>

        <form action="/clear" method="post">
            <button class="clear-btn" type="submit" onclick="return confirm('确定要清空名单吗？')">
                清空名单
            </button>
        </form>
    </div>
</body>
</html>
""", names=names, groups=groups)


@app.route("/clear", methods=["POST"])
def clear():
    save_names([])
    return redirect("/admin")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
