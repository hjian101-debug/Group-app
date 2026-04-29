from flask import Flask, request, redirect, render_template_string
import json
import os
import random
import qrcode
from io import BytesIO
from flask import send_file

app = Flask(__name__)

DATA_FILE = "names.json"

# ===== 数据处理 =====
def load_names():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_names(names):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(names, f, ensure_ascii=False, indent=2)

# ===== 首页（美化版）=====
@app.route("/")
def home():
    join_url = "https://group-app-55j5.onrender.com/join"

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>随机分组报名系统</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(to right, #667eea, #764ba2);
            margin: 0;
        }

        .card {
            background: white;
            max-width: 400px;
            margin: 60px auto;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
            text-align: center;
        }

        h1 {
            color: #333;
        }

        h2 {
            color: #666;
            font-size: 18px;
        }

        img {
            margin: 20px 0;
        }

        .link {
            background: #f4f4f4;
            padding: 10px;
            border-radius: 8px;
            word-break: break-all;
            font-size: 14px;
        }

        .admin-btn {
            margin-top: 20px;
            display: inline-block;
            padding: 10px 20px;
            background: #667eea;
            color: white;
            border-radius: 8px;
            text-decoration: none;
        }

        .admin-btn:hover {
            background: #5a67d8;
        }
    </style>
</head>

<body>

<div class="card">
    <h1>🎯 随机分组报名系统</h1>
    <h2>扫码填写你的姓名</h2>

    <img src="/qr" width="200">

    <p>打不开二维码？复制链接：</p>
    <div class="link">{{join_url}}</div>

    <a href="/admin" class="admin-btn">进入管理员页面</a>
</div>

</body>
</html>
""", join_url=join_url)

# ===== 二维码 =====
@app.route("/qr")
def qr():
    join_url = "https://group-app-55j5.onrender.com/join"
    img = qrcode.make(join_url)

    buf = BytesIO()
    img.save(buf)
    buf.seek(0)

    return send_file(buf, mimetype='image/png')

# ===== 报名页面 =====
@app.route("/join", methods=["GET", "POST"])
def join():
    if request.method == "POST":
        name = request.form.get("name")
        if name:
            names = load_names()
            names.append(name)
            save_names(names)
        return redirect("/join")

    return """
    <h2>请输入你的姓名</h2>
    <form method="post">
        <input name="name" placeholder="姓名">
        <button type="submit">提交</button>
    </form>
    """

# ===== 管理员页面 =====
@app.route("/admin", methods=["GET", "POST"])
def admin():
    names = load_names()

    result = ""

    if request.method == "POST":
        group_num = int(request.form.get("group"))

        random.shuffle(names)
        groups = [names[i::group_num] for i in range(group_num)]

        result += "<h3>分组结果：</h3>"
        for i, g in enumerate(groups):
            result += f"<p>第{i+1}组：{', '.join(g)}</p>"

    name_list = "<br>".join(names)

    return f"""
    <h2>管理员页面</h2>

    <h3>当前人数：{len(names)}</h3>
    <p>{name_list}</p>

    <hr>

    <form method="post">
        <input name="group" placeholder="分几组">
        <button type="submit">开始分组</button>
    </form>

    <br>
    <a href="/clear">清空数据</a>
    """

# ===== 清空数据 =====
@app.route("/clear")
def clear():
    save_names([])
    return redirect("/admin")

# ===== 启动 =====
if __name__ == "__main__":
    app.run()
