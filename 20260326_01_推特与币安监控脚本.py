import requests
import os
import json
import xml.etree.ElementTree as ET
import time
import re

# --- 配置区 ---
TWITTER_USER = "alpha123cc"
SERVERCHAN_SENDKEY = os.environ.get("SCKEY")
STATE_FILE = "monitor_state.json"

def send_wechat(title, content, source="监控系统"):
    if not SERVERCHAN_SENDKEY: return
    print(f"🚀 尝试推送微信: {title}")
    url = f"https://sctapi.ftqq.com/{SERVERCHAN_SENDKEY}.send"
    data = {"title": f"【{source}】{title}", "desp": content}
    try:
        r = requests.post(url, data=data, timeout=15)
        print(f"微信返回: {r.text}")
    except:
        print("❌ 微信推送失败")

def get_twitter_update():
    print(f"--- 正在检查推特 (@{TWITTER_USER}) ---")
    urls = [
        f"https://nitter.net/{TWITTER_USER}/rss",
        f"https://nitter.cz/{TWITTER_USER}/rss"
    ]
    for url in urls:
        try:
            res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=20)
            if res.status_code == 200:
                root = ET.fromstring(res.content)
                item = root.find(".//item")
                if item is not None:
                    print("✅ 推特获取成功")
                    return {
                        "id": item.find("guid").text if item.find("guid") is not None else item.find("link").text,
                        "title": item.find("title").text,
                        "link": item.find("link").text
                    }
        except: pass
    return None

def get_binance_update():
    print("--- 正在检查币安公告 (降维打击：从官方电报/推特抓取) ---")
    
    # 【方案1：抓取币安官方公告电报频道（零拦截，实时更新）】
    try:
        print("尝试通道1: 币安官方电报网页版...")
        res = requests.get("https://t.me/s/binance_announcements", headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        if res.status_code == 200:
            # 正则提取电报网页版里的最新消息
            msgs = re.findall(r'<div class="tgme_widget_message_text[^>]*>(.*?)</div>', res.text, re.IGNORECASE | re.DOTALL)
            ids = re.findall(r'data-post="binance_announcements/(\d+)"', res.text)
            if msgs and ids:
                latest_html = msgs[-1]
                msg_id = ids[-1]
                # 尝试提取公告链接
                link_match = re.search(r'href="(https://www.binance.com/[^"]+)"', latest_html)
                link = link_match.group(1) if link_match else "https://www.binance.com/zh-CN/support/announcement"
                
                # 清理 HTML 标签获取纯文本标题
                title = re.sub(r'<[^>]+>', ' ', latest_html).strip().replace('\n', ' ')
                if len(title) > 80: title = title[:80] + "..."
                
                print("✅ 币安电报频道抓取成功！完全绕过防火墙！")
                return {"id": f"tg_{msg_id}", "title": title, "link": link}
    except Exception as e:
        print(f"电报通道失败: {e}")

    # 【方案2：抓取币安官方推特 Nitter (备用)】
    try:
        print("尝试通道2: 币安官推 Nitter...")
        # 因为我们已经验证 Nitter 在你的 GitHub 上是 100% 成功的
        res = requests.get("https://nitter.net/binance/rss", headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        if res.status_code == 200:
            root = ET.fromstring(res.content)
            item = root.find(".//item")
            if item is not None:
                title = item.find("title").text
                print("✅ 币安官推抓取成功！")
                return {
                    "id": item.find("guid").text if item.find("guid") is not None else item.find("link").text,
                    "title": f"币安官推: {title}",
                    "link": item.find("link").text
                }
    except Exception as e:
        print(f"推特通道失败: {e}")
        
    print("❌ 所有币安获取通道均失效")
    return None

def main():
    print(f"=== 监控启动 {time.strftime('%Y-%m-%d %H:%M:%S')} ===")
    state = {"twitter_last_id": "", "binance_last_id": ""}
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            try: state = json.load(f)
            except: pass

    # 1. 检查推特
    t = get_twitter_update()
    if t:
        if t['id'] != state.get("twitter_last_id"):
            send_wechat(t['title'], f"[点击查看]({t['link']})", "推特")
            state["twitter_last_id"] = t['id']
        else:
            print("ℹ️ 推特无新内容，跳过")

    # 2. 检查币安
    b = get_binance_update()
    if b:
        if b['id'] != state.get("binance_last_id"):
            send_wechat(b['title'], f"[点击查看]({b['link']})", "币安")
            state["binance_last_id"] = b['id']
        else:
            print("ℹ️ 币安无新内容，跳过")

    with open(STATE_FILE, "w") as f:
        json.dump(state, f)
    print("=== 运行结束 ===")

if __name__ == "__main__":
    main()
