import os
import json
import time
import xml.etree.ElementTree as ET
# 引入浏览器指纹伪装库
from curl_cffi import requests

# --- 配置区 ---
TWITTER_USER = "alpha123cc"
SERVERCHAN_SENDKEY = os.environ.get("SCKEY")
STATE_FILE = "monitor_state.json"

def send_wechat(title, content, source="监控系统"):
    if not SERVERCHAN_SENDKEY: return
    print(f"🚀 准备推送微信: {title}")
    url = f"https://sctapi.ftqq.com/{SERVERCHAN_SENDKEY}.send"
    data = {"title": f"【{source}】{title}", "desp": content}
    try:
        requests.post(url, data=data, timeout=15)
        print("✅ 微信推送成功")
    except Exception as e:
        print(f"❌ 微信推送失败: {e}")

def get_twitter_update():
    print(f"--- 检查推特 (@{TWITTER_USER}) ---")
    urls = [
        f"https://nitter.net/{TWITTER_USER}/rss",
        f"https://nitter.cz/{TWITTER_USER}/rss"
    ]
    for url in urls:
        try:
            # 伪装成 Chrome 120 浏览器请求
            res = requests.get(url, impersonate="chrome120", timeout=20)
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
    print("--- 检查币安中文官网 (启动浏览器指纹伪装) ---")
    # 直接请求币安官方 API
    api_url = "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query"
    # catalogId: 93 代表 "最新活动" (跟你截图里的一致)
    payload = {"type": 1, "catalogId": "93", "pageNo": 1, "pageSize": 5}
    headers = {
        "clienttype": "web",
        "Lang": "zh-CN"  # 强制要求返回纯正中文！
    }
    try:
        # impersonate="chrome120" 是突破 403 拦截的核心利器！
        res = requests.post(api_url, json=payload, headers=headers, impersonate="chrome120", timeout=20)
        if res.status_code == 200:
            articles = res.json().get("data", {}).get("catalogs", [{}])[0].get("articles", [])
            if articles:
                latest = articles[0]
                print(f"✅ 成功穿透防火墙！抓取到中文标题: {latest['title']}")
                return {
                    "id": str(latest['id']),
                    "title": latest['title'],
                    "link": f"https://www.binance.com/zh-CN/support/announcement/{latest['code']}"
                }
        else:
            print(f"⚠️ 状态码异常: {res.status_code}")
    except Exception as e:
        print(f"❌ 币安请求失败: {e}")
    return None

def main():
    print(f"=== 监控启动 {time.strftime('%H:%M:%S')} ===")
    state = {"twitter_last_id": "", "binance_last_id": ""}
    
    # 强制每次运行都提示连接成功，用于你测试
    print("读取状态中...")
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            try: state = json.load(f)
            except: pass
    else:
        # 第一次运行，发送测试微信
        send_wechat("币安中文监控已就绪", "如果收到这条，说明中文抓取功能即将开始工作！")

    # 1. 推特逻辑
    t = get_twitter_update()
    if t:
        if t['id'] != state.get("twitter_last_id"):
            send_wechat(t['title'], f"链接: {t['link']}", "推特")
            state["twitter_last_id"] = t['id']
        else:
            print("ℹ️ 推特无新内容，跳过")

    # 2. 币安逻辑
    b = get_binance_update()
    if b:
        if b['id'] != state.get("binance_last_id"):
            send_wechat(b['title'], f"链接: {b['link']}", "币安活动")
            state["binance_last_id"] = b['id']
        else:
            print("ℹ️ 币安无新内容，跳过")

    with open(STATE_FILE, "w") as f:
        json.dump(state, f)
    print("=== 运行结束 ===")

if __name__ == "__main__":
    main()
