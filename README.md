# douyin-guest-dl

**免登录下载抖音视频** —— 不需要账号、不需要导出 cookie、不需要逆向签名。

> 2026 年起 yt-dlp 等工具下载抖音常遇到 `HTTP 403` / `Fresh cookies are needed`，即使带上登录 cookie 也一样。本工具换个思路：让真实浏览器（无头模式）打开视频页，抖音会自动给访客会话下发临时 cookie，脚本截获页面自己请求到的视频详情，挑最高码率地址在同一会话里下载。

## 特点

- 免登录，访客模式即可下载
- 直接粘贴抖音「复制链接」的整段分享文字即可识别
- 支持短链 `v.douyin.com/xxx`、`douyin.com/video/<id>`、`modal_id=`、纯视频 ID
- 自动选最高码率，可选保存视频详情 JSON（标题、作者、音乐、点赞数等）
- 一次可下载多个
- 优先复用系统已安装的 Edge / Chrome，无需额外下载浏览器

## 安装

```bash
pip install -r requirements.txt
# 如果系统没有 Edge 或 Chrome，再执行：
playwright install chromium
```

## 使用

```bash
python dydl.py "7.43 复制打开抖音，看看【xxx的作品】... https://v.douyin.com/xxxxxxx/"
python dydl.py https://www.douyin.com/video/7xxxxxxxxxxxxxxxxxx -o ./downloads
python dydl.py 7xxxxxxxxxxxxxxxxxx 7yyyyyyyyyyyyyyyyyy
```

参数：

| 参数 | 说明 |
| --- | --- |
| `-o, --out` | 输出目录，默认 `./videos` |
| `--browser` | `auto`（默认，Edge > Chrome > Chromium）/ `msedge` / `chrome` / `chromium` |
| `--cdp` | 可选，连接一个已打开的浏览器调试端口（如 `http://127.0.0.1:9222`），复用其中的会话 |
| `--no-json` | 不保存视频详情 JSON |

输出：`<视频ID>.mp4`，以及 `<视频ID>.json`（视频详情）。

## 注意

- 建议在中国大陆网络环境使用；海外 IP 访问抖音网页可能拿不到视频数据。
- 暂不支持图文（图集）作品。
- 抖音页面结构随时可能变化，失效请提 Issue。
- 仅供个人学习研究使用，请尊重创作者版权，勿用于二次分发或商业用途。

## English

Download Douyin (Chinese TikTok) videos **without logging in**. A headless Edge/Chrome opens the video page, Douyin hands the guest session temporary cookies by itself, and the script captures the page's own video-detail response and downloads the highest-bitrate stream in the same session. No account, no cookie export, no signature reverse-engineering.

```bash
pip install -r requirements.txt
python dydl.py "<share text | short link | video url | video id>" [-o out_dir]
```

Works best from a mainland-China network. For personal use only; respect creators' copyrights.

## License

MIT
