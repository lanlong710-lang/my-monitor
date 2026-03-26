import requests
import os
import json
import xml.etree.ElementTree as ET
import random

# --- 配置区 ---
TWITTER_USER = "alpha123cc"
BINANCE_CATALOG_ID = "93"
SERVERCHAN_SENDKEY = os.environ.get("SCKEY")
STATE_FILE = "monitor_state.json"

def get_twitter_update():
    print(f"--- 正在检查推特 (@{TWITTER_USER}) ---")
    # 增加更多 RSS 源，包括 Nitter 镜像（Nitter 对推特抓取更友好）
    rss_urls = [
        f"https://nitter.net/{TWITTER_USER}/rss",
        f"https://rsshub.rssforever.com/twitter/user/{TWITTER_USER}",
        f"https://nitter.cz/{TWITTER_USER}/rss"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    for url in rss_urls:
        try:
            print(f"尝试从 {url} 获取...")
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                item = root.find(".//item")
                if item is not None:
                    print("✅ 推特数据获取成功")
                    return {
                        "id": item.find("guid").text if item.find("guid") is not None else item.find("link").text,
                        "title": item.find("title").text,
                        "link": item.find("link").text,
                        "source": "Twitter"
                    }
            print(f"⚠️ 该源返回状态码: {response.status_code}")
        except Exception as e:
            print(f"❌ 该源连接失败: {e}")
    return None

def get_binance_update():
    print("--- 正在检查币安公告 ---")
    # 使用币安的移动端接口或增加更多指纹参数，尝试绕过 403
    api_url = "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query"
    payload = {
        "type": 1, 
        "catalogId": BINANCE_CATALOG_ID, 
        "pageNo": 1, 
        "pageSize": 5
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
        'Referer': 'https://www.binance.com/zh-CN/support/announcement/',
        'Lang': 'zh-CN'
    }
    try:
        # 使用 Session 保持
        session = requests.Session()
        res = session.post(api_url, json=payload, headers=headers, timeout=15)
        if res.status_code == 200:
            articles = res.json().get("data", {}).get("catalogs", [{}])[0].get("articles", [])
            if articles:
                print("✅ 币安公告获取成功")
                latest = articles[0]
                return {
                    "id": str(latest['id']),
                    "title": latest['title'],
                    "link": f"https://www.binance.com/zh-CN/support/announcement/{latest['code']}",
                    "source": "币安公告"
                }
        print(f"❌ 币安 API 仍返回 403 或其他错误: {res.status_code}")
    except Exception as e:
        print(f"❌ 币安获取异常: {e}")
    return None

def send_wechat(msg):
    if not SERVERCHAN_SENDKEY:
        print("⚠️ 未找到 SCKEY")
        return
    print(f"🚀 发送通知: {msg['title']}")
    url = f"https://sctapi.ftqq.com/{SERVERCHAN_SENDKEY}.send"
    data = {"title": f"【{msg['source']}】新提醒", "desp": f"{msg['title']}\n\n[链接]({msg['link']})"}
    requests.post(url, data=data, timeout=10)

def main():
    print("=== 监控启动 ===")
    state = {}
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            state = json.load(f)

    # 检查推特
    t_msg = get_twitter_update()
    if t_msg and t_msg['id'] != state.get("twitter_last_id"):
        send_wechat(t_msg)
        state["twitter_last_id"] = t_msg['id']

    # 检查币安
    b_msg = get_binance_update()
    if b_msg and b_msg['id'] != state.get("binance_last_id"):
        send_wechat(b_msg)
        state["binance_last_id"] = b_msg['id']

    with open(STATE_FILE, "w") as f:
        json.dump(state, f)
    print("=== 任务结束 ===")

if __name__ == "__main__":
    main()
