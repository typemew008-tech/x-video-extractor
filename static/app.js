const form = document.querySelector("#form");
const input = document.querySelector("#url");
const statusBox = document.querySelector("#status");
const result = document.querySelector("#result");
const quality = document.querySelector("#quality");
const preview = document.querySelector("#preview");
let formats = [];

document.querySelector("#paste").addEventListener("click", async () => {
  try {
    input.value = await navigator.clipboard.readText();
    statusBox.textContent = input.value ? "已粘贴链接，点击提取视频即可。" : "剪贴板为空。";
    statusBox.className = "status";
  } catch {
    input.focus();
    statusBox.textContent = "浏览器未允许读取剪贴板，请长按输入框并选择“粘贴”。";
    statusBox.className = "status";
  }
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const url = input.value.trim();
  result.hidden = true;
  preview.removeAttribute("src");
  statusBox.textContent = "正在解析视频，请稍候……";
  statusBox.className = "status";
  const button = document.querySelector("#extract");
  button.disabled = true;
  try {
    const response = await fetch("/api/extract", {
      method: "POST", headers: {"Content-Type":"application/json"},
      body: JSON.stringify({url})
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "提取失败");
    formats = data.formats;
    quality.innerHTML = "";
    formats.forEach((f, i) => {
      const option = document.createElement("option");
      option.value = f.id;
      option.textContent = f.label + (f.has_audio ? "" : "（下载时合并音频）");
      quality.appendChild(option);
    });
    document.querySelector("#videoTitle").textContent = data.title || "X 视频";
    preview.src = formats[0].url;
    result.hidden = false;
    statusBox.textContent = "解析成功。请选择清晰度后下载。";
  } catch (error) {
    statusBox.textContent = error.message;
    statusBox.className = "status error";
  } finally {
    button.disabled = false;
  }
});

quality.addEventListener("change", () => {
  const selected = formats.find(f => f.id === quality.value);
  if (selected) preview.src = selected.url;
});

document.querySelector("#download").addEventListener("click", async () => {
  const button = document.querySelector("#download");
  button.disabled = true;
  button.textContent = "正在准备下载……";
  try {
    const response = await fetch("/api/download", {
      method: "POST", headers: {"Content-Type":"application/json"},
      body: JSON.stringify({url: input.value.trim(), format_id: quality.value})
    });
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.error || "下载失败");
    }
    const blob = await response.blob();
    const objectUrl = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = objectUrl;
    a.download = "x-video.mp4";
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(objectUrl), 60000);
    button.textContent = "已开始下载 ✓";
  } catch (error) {
    statusBox.textContent = error.message;
    statusBox.className = "status error";
    button.textContent = "下载 MP4 ↓";
  } finally {
    button.disabled = false;
  }
});
