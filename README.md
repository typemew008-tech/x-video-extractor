# X 视频提取器

一个适配手机 Safari 的网页：粘贴公开 X/Twitter 视频推文链接，解析预览、选择清晰度并下载 MP4。

## 部署（推荐 Render + GitHub）

1. 将本项目所有文件上传到一个新的 GitHub 仓库，仓库保持 Public 或 Private 均可。
2. 登录 Render，选择 **New → Web Service**，连接刚才的 GitHub 仓库。
3. Render 会识别根目录的 `Dockerfile`。无需填写 Build Command 或 Start Command。
4. 点击部署。部署成功后，打开 Render 提供的 `https://你的服务名.onrender.com`。
5. 在 iPhone Safari 打开该网址，即可粘贴 X 视频链接使用；可以通过 Safari“分享 → 添加到主屏幕”。

## 本地运行（可选）

需要 Python 3.12 和 FFmpeg：

```bash
pip install -r requirements.txt
python app.py
```

## 使用限制

- 仅针对可公开访问的 X/Twitter 推文视频。
- 私密账号、受保护推文、需要登录或地区受限的视频可能无法提取。
- X 平台规则、视频可访问性及 yt-dlp 更新都会影响可用性；如突然无法解析，先更新依赖中的 yt-dlp 版本并重新部署。
- 请遵守版权及平台条款，仅下载你有权保存或使用的内容。
- 免费托管服务可能休眠，首次打开或首次解析需要等待唤醒；大文件下载也可能受服务商时长/内存限制。
