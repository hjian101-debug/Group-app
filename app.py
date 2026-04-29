from flask import Flask, request, redirect, render_template_string, send_file
import qrcode
import socket
import random
import json
import os
from io import BytesIO

app = Flask(__name__)
DATA_FILE = "names.json"


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip


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
    join_url = "https://group-app-5555.onrender.com/join"
   

    return render_template_string("""
    <h1>随机分组报名系统</h1>

    <h2>请大家扫码填写姓名</h2>
    <img src="/qr" width="260">

    <p>手机打不开二维码时，手动输入这个网址：</p>
    <h3>{{ join_url }}</h3>

    <hr>

    <p><a href="/admin">进入管理员页面</a></p>
    """, join_url=join_url)


@app.route("/qr")
def qr():
    join_url = "https://group-app-5555.onrender.com/join"

    img = qrcode.make(join_url)
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return send_file(buffer, mimetype="image/png")


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
            <h1>提交成功</h1>
            <p>你的名字是：<strong>{{ name }}</strong></p>
            <p>请等待老师/管理员分组。</p>
            """, name=name)

    return render_template_string("""
    <h1>填写姓名</h1>

    <form method="post">
        <input name="name" placeholder="请输入你的姓名" required style="font-size:24px;">
        <button type="submit" style="font-size:24px;">提交</button>
    </form>
    """)


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
    <h1>管理员页面</h1>

    <h2>当前已报名人数：{{ names|length }}</h2>

    <ol>
    {% for name in names %}
        <li>{{ name }}</li>
    {% endfor %}
    </ol>

    <hr>

    <h2>随机分组</h2>

    <form method="post">
        <label>请输入分几组：</label>
        <input type="number" name="group_count" min="1" required>
        <button type="submit">开始分组</button>
    </form>

    {% if groups %}
        <hr>
        <h2>分组结果</h2>

        {% for group in groups %}
            <h3>第 {{ loop.index }} 组：{{ group|length }} 人</h3>
            <ul>
            {% for name in group %}
                <li>{{ name }}</li>
            {% endfor %}
            </ul>
        {% endfor %}
    {% endif %}

    <hr>

    <form action="/clear" method="post">
        <button type="submit" onclick="return confirm('确定要清空名单吗？')">
            清空名单
        </button>
    </form>
    """, names=names, groups=groups)


@app.route("/clear", methods=["POST"])
def clear():
    save_names([])
    return redirect("/admin")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
