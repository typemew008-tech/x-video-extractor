import os
import re
import tempfile
import shutil
from pathlib import urlparse
from flask import Flask, request, jsonify, render_template, send_file, after_this_request
import yt_dlp

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024

ALLOWED_HOSTS = {"x.com", "www.x.com", "twitter.com", "www.twitter.com", "mobile.twitter.com"}

def valid_x_url(value):
    try:
        parsed = urlparse(value.strip())
        host = (parsed.hostname or "").lower()
        return parsed.scheme in ("http", "https") and host in ALLOWED_HOSTS and bool(re.search(r"/(status|statuses)/\d+", parsed.path))
    except Exception:
        return False

def extract_info(url):
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": True,
        "socket_timeout": 20,
        "retries": 2,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=False)

@app.get("/")
def home():
    return render_template("index.html")

@app.post("/api/extract")
def api_extract():
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()
    if not valid_x_url(url):
        return jsonify(error="请粘贴有效的 X/Twitter 视频推文链接。"), 400
    try:
        info = extract_info(url)
        formats = []
        seen = set()
        for f in info.get("formats", []):
            if not f.get("url") or not f.get("height"):
                continue
            ext = f.get("ext", "")
            if ext not in ("mp4", "m4v"):
                continue
            # X often supplies separate video/audio streams. Keep video formats;
            # yt-dlp will merge audio when downloading the selected format.
            key = (f.get("format_id"), f.get("height"), f.get("tbr"))
            if key in seen:
                continue
            seen.add(key)
            formats.append({
                "id": str(f.get("format_id")),
                "label": f'{f.get("height")}p' + (f' · {round(f.get("tbr"))} kbps' if f.get("tbr") else ""),
                "height": f.get("height") or 0,
                "url": f.get("url"),
                "has_audio": bool(f.get("acodec") and f.get("acodec") != "none"),
            })
        formats.sort(key=lambda x: x["height"], reverse=True)
        if not formats:
            return jsonify(error="没有找到可用的 MP4 视频格式。该推文可能没有视频、受到访问限制，或需要登录。"), 404
        return jsonify({
            "title": info.get("title") or "X 视频",
            "thumbnail": info.get("thumbnail"),
            "duration": info.get("duration"),
            "formats": formats,
        })
    except Exception as exc:
        message = str(exc)
        if "login" in message.lower() or "protected" in message.lower():
            message = "该视频可能需要登录、来自受保护账号，或当前无法公开访问。"
        else:
            message = "提取失败。请确认推文是公开视频，并稍后重试。"
        app.logger.exception("X extraction failed")
        return jsonify(error=message), 502

@app.post("/api/download")
def api_download():
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()
    format_id = str(data.get("format_id") or "")
    if not valid_x_url(url) or not format_id:
        return jsonify(error="请求参数无效。"), 400

    temp_dir = tempfile.mkdtemp(prefix="xvideo_")
    output = os.path.join(temp_dir, "video.%(ext)s")
    opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "format": format_id + "+bestaudio/best",
        "merge_output_format": "mp4",
        "outtmpl": output,
        "socket_timeout": 30,
        "retries": 2,
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        candidates = [os.path.join(temp_dir, f) for f in os.listdir(temp_dir) if f.lower().endswith((".mp4", ".mkv", ".webm"))]
        if not candidates:
            raise RuntimeError("视频文件生成失败")
        path = candidates[0]

        @after_this_request
        def cleanup(response):
            # Delay cleanup briefly so the response can finish streaming.
            import threading, time
            def remove():
                time.sleep(60)
                shutil.rmtree(temp_dir, ignore_errors=True)
            threading.Thread(target=remove, daemon=True).start()
            return response

        return send_file(path, as_attachment=True, download_name="x-video.mp4")
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        app.logger.exception("X download failed")
        return jsonify(error="下载失败。请换一个清晰度重试；部分视频可能受到登录或地区限制。"), 502

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
