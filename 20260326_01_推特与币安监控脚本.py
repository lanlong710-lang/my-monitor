import requests
import os
import json
import xml.etree.ElementTree as ET
import time

# --- 配置区 ---
TWITTER_USER = "alpha123cc"
SERVERCHAN_SENDKEY = os.environ.get("SCKEY")
STATE_FILE = "monitor_state.json"

def send_wechat(title, content, source="系统通知"):
    if not SERVERCHAN_SENDKEY:
        print("⚠️ 没找到 SCKEY，请检查 GitHub Secrets")
        return
    print(f"🚀 尝试发送微信: {title}")
    url = f"https://sctapi.ftqq.com/{SERVERCHAN_SENDKEY}.send"
    data = {"title": f"【{source}】{title}", "desp": content}
    try:
        r = requests.post(url, data=data, timeout=15)
        print(f"微信服务器返回: {r.text}")
    except Exception as e:
        print(f"❌ 微信推送崩溃: {e}")

def get_twitter_update():
    print(f"--- 检查推特 (@{TWITTER_USER}) ---")
    url = f"https://nitter.net/{TWITTER_USER}/rss"
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=20)
        if res.status_code == 200:
            root = ET.fromstring(res.content)
            item = root.find(".//item")
            if item is not None:
                return {
                    "id": item.find("guid").text if item.find("guid") is not None else item.find("link").text,
                    "title": item.find("title").text,
                    "link": item.find("link").text
                }
    except: pass
    return None

def get_binance_update():
    print("--- 检查币安公告 ---")
    # 尝试直接请求 API，但换一组超级模拟头
    api_url = "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query"
    payload = {"type": 1, "catalogId": "93", "pageNo": 1, "pageSize": 5}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "clienttype": "web"
    }
    try:
        res = requests.post(api_url, json=payload, headers=headers, timeout=15)
        if res.status_code == 200:
            data = res.json()
            articles = data.get("data", {}).get("catalogs", [{}])[0].get("articles", [])
            if articles:
                print("✅ 币安数据获取成功")
                latest = articles[0]
                return {
                    "id": str(latest['id']),
                    "title": latest['title'],
                    "link": f"https://www.binance.com/zh-CN/support/announcement/{latest['code']}"
                }
        print(f"⚠️ 币安 API 仍然报错: {res.status_code}")
    except: pass
    return None

def main():
    print(f"=== 监控运行 {time.strftime('%H:%M:%S')} ===")
    
    # 第一次运行？强制发一条测试，确认微信通路！
    if not os.path.exists(STATE_FILE):
        send_wechat("连接成功", "这是系统自动发送的第一次连接测试，如果你收到了，说明监控已就绪！", "初始化")
        state = {"twitter_last_id": "", "binance_last_id": ""}
    else:
        with open(STATE_FILE, "r") as f:
            state = json.load(f)

    # 1. 推特逻辑
    t = get_twitter_update()
    if t and t['id'] != state.get("twitter_last_id"):
        send_wechat(t['title'], f"[点击查看]({t['link']})", "推特")
        state["twitter_last_id"] = t['id']

    # 2. 币安逻辑
    b = get_binance_update()
    if b and b['id'] != state.get("binance_last_id"):
        send_wechat(b['title'], f"[点击查看]({b['link']})", "币安")
        state["binance_last_id"] = b['id']

    with open(STATE_FILE, "w") as f:
        json.dump(state, f)
    print("=== 运行结束 ===")

if __name__ == "__main__":
    main()
