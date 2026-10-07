#!/usr/bin/env python3
"""douyin-guest-dl: 免登录下载抖音视频 / Download Douyin videos without logging in.

用法 Usage:
    python dydl.py "<分享文字 / 短链 / 视频链接 / 视频ID>" [更多...] [-o 输出目录]

原理: 用 Playwright 打开一个无头浏览器访问视频页，抖音会自动给访客会话发临时 cookie；
脚本截获页面自己请求到的视频详情 JSON，挑最高码率的地址，在同一会话里下载。
不需要账号、不需要导出 cookie、也不需要逆向签名算法。
"""
import argparse, asyncio, json, os, re, sys, urllib.request
from playwright.async_api import async_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36")
ID_RE = r"(?:video/|note/|modal_id=)(\d{15,})"


def to_id(s: str) -> str:
    m = re.search(ID_RE, s) or re.fullmatch(r"\s*(\d{15,})\s*", s)
    if m:
        return m.group(1)
    m = re.search(r"https?://v\.douyin\.com/[\w\-]+/?", s)
    if not m:
        raise SystemExit(f"无法识别的链接 / unrecognized input: {s}")
    req = urllib.request.Request(m.group(0), headers={"User-Agent": UA})
    final = urllib.request.urlopen(req, timeout=20).geturl()
    m = re.search(ID_RE, final)
    if not m:
        raise SystemExit(f"短链解析失败 / failed to resolve short link: {final}")
    return m.group(1)


async def grab(ctx, aid: str, out: str, save_json: bool) -> bool:
    found, media = {}, []
    page = await ctx.new_page()

    async def on_resp(r):
        u = r.url
        try:
            if "aweme/v1/web/aweme/detail" in u:
                j = await r.json()
                if j.get("aweme_detail"):
                    found["d"] = j["aweme_detail"]
            elif "douyinvod" in u and u not in media:
                media.append(u)
        except Exception:
            pass

    page.on("response", on_resp)
    await page.goto(f"https://www.douyin.com/video/{aid}", wait_until="domcontentloaded", timeout=60000)
    for _ in range(25):
        if found.get("d"):
            break
        await page.wait_for_timeout(1000)

    d, url = found.get("d"), None
    if d:
        v = d["video"]
        if save_json:
            with open(os.path.join(out, f"{aid}.json"), "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, indent=1)
        cands = sorted(((br.get("bit_rate", 0), br["play_addr"]["url_list"]) for br in v.get("bit_rate") or []),
                       key=lambda x: -x[0])
        urls = [u for _, lst in cands for u in lst] + v["play_addr"]["url_list"]
        url = urls[0] if urls else None
        print(f"[{aid}] {d['author'].get('nickname')} | {d.get('desc')} | {v.get('duration')}ms")
    url = url or (media[0] if media else None)
    if not url:
        print(f"[{aid}] 未获取到视频地址 / no video url found (图文作品暂不支持)")
        await page.close()
        return False
    r = await ctx.request.get(url, headers={"Referer": "https://www.douyin.com/"}, timeout=120000)
    body = await r.body()
    path = os.path.join(out, f"{aid}.mp4")
    with open(path, "wb") as f:
        f.write(body)
    print(f"[{aid}] OK {len(body)} bytes -> {path}")
    await page.close()
    return True


async def launch(p, browser: str):
    order = [browser] if browser != "auto" else ["msedge", "chrome", "chromium"]
    last = None
    for ch in order:
        try:
            kw = {"headless": True, "args": ["--mute-audio"]}
            if ch != "chromium":
                kw["channel"] = ch
            return await p.chromium.launch(**kw)
        except Exception as e:
            last = e
    raise SystemExit(f"找不到可用浏览器，请安装 Edge/Chrome 或运行 `playwright install chromium`\n{last}")


async def main():
    ap = argparse.ArgumentParser(description="免登录下载抖音视频 / Download Douyin videos without login")
    ap.add_argument("items", nargs="+", help="分享文字、短链、视频链接或视频ID")
    ap.add_argument("-o", "--out", default="videos", help="输出目录 (默认 ./videos)")
    ap.add_argument("--browser", default="auto", choices=["auto", "msedge", "chrome", "chromium"],
                    help="使用的浏览器 (默认自动: Edge > Chrome > Playwright Chromium)")
    ap.add_argument("--cdp", default=None,
                    help="可选: 连接已打开的浏览器调试端口, 如 http://127.0.0.1:9222")
    ap.add_argument("--no-json", action="store_true", help="不保存视频详情 JSON")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    ids = [to_id(s) for s in a.items]
    ok = 0
    async with async_playwright() as p:
        if a.cdp:
            b = await p.chromium.connect_over_cdp(a.cdp)
            ctx = b.contexts[0] if b.contexts else await b.new_context()
        else:
            b = await launch(p, a.browser)
            ctx = await b.new_context(locale="zh-CN", user_agent=UA)
        for aid in ids:
            try:
                ok += await grab(ctx, aid, a.out, not a.no_json)
            except Exception as e:
                print(f"[{aid}] 失败 / failed: {e}")
        if not a.cdp:
            await b.close()
    print(f"完成 {ok}/{len(ids)}")
    sys.exit(0 if ok == len(ids) else 1)


if __name__ == "__main__":
    asyncio.run(main())
