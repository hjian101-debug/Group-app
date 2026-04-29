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
    join_url = "https://group-app-55j5.onrender.com/join"
   

  return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>随机分组报名系统</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(to right, #667eea, #764ba2);
            text-align: center;
            margin: 0;
            padding: 0;
        }

        .card {
            background: white;
            width: 400px;
            margin: 80px auto;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        }

        h1 {
            color: #333;
        }

        h2 {
            color: #666;
        }

        img {
            margin: 20px 0;
            border-radius: 10px;
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
