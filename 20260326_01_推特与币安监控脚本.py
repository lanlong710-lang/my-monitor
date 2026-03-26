import requests
import os
import json
import xml.etree.ElementTree as ET
import time
import urllib.parse

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
        print(f"微信服务器返回: {r.text}")
    except Exception as e:
        print(f"❌ 微信推送失败: {e}")

def get_twitter_update():
    print(f"--- 正在检查推特 (@{TWITTER_USER}) ---")
    url = f"https://nitter.net/{TWITTER_USER}/rss"
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
    except Exception as e:
        print(f"❌ 推特获取异常: {e}")
    return None

def get_binance_update():
    print("--- 正在检查币安公告 (使用代理穿透) ---")
    # 目标币安 RSS 地址
    target_url = "https://www.binance.com/zh-CN/support/announcement/c-48?format=rss"
    # 将目标地址进行编码
    encoded_url = urllib.parse.quote(target_url, safe='')
    # 使用 AllOrigins 免费代理服务，隐藏 GitHub Actions 的真实 IP
    proxy_url = f"https://api.allorigins.win/raw?url={encoded_url}"
    
    try:
        print("尝试通过 AllOrigins 代理获取数据...")
        res = requests.get(proxy_url, timeout=25)
        if res.status_code == 200:
            root = ET.fromstring(res.text)
            item = root.find(".//item")
            if item is not None:
                print("✅ 币安数据获取成功！代理穿透有效！")
                return {
                    "id": item.find("guid").text if item.find("guid") is not None else item.find("link").text,
                    "title": item.find("title").text,
                    "link": item.find("link").text
                }
        else:
            print(f"⚠️ 代理返回状态码: {res.status_code}")
    except Exception as e:
        print(f"❌ 代理请求失败: {e}")
    return None

def main():
    print(f"=== 监控启动 {time.strftime('%Y-%m-%d %H:%M:%S')} ===")
    
    state = {"twitter_last_id": "", "binance_last_id": ""}
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            try: state = json.load(f)
            except: pass

    # 1. 推特逻辑
    t = get_twitter_update()
    if t:
        if t['id'] != state.get("twitter_last_id"):
            send_wechat(t['title'], f"链接: {t['link']}", "推特")
            state["twitter_last_id"] = t['id']
        else:
            print("ℹ️ 推特无新内容，跳过推送")

    # 2. 币安逻辑
    b = get_binance_update()
    if b:
        if b['id'] != state.get("binance_last_id"):
            send_wechat(b['title'], f"链接: {b['link']}", "币安")
            state["binance_last_id"] = b['id']
        else:
            print("ℹ️ 币安无新内容，跳过推送")

    with open(STATE_FILE, "w") as f:
        json.dump(state, f)
    print("=== 运行结束 ===")

if __name__ == "__main__":
    main()
