import requests
import os
import json
import xml.etree.ElementTree as ET

# --- 配置区 ---
TWITTER_USER = "alpha123cc"
BINANCE_CATALOG_ID = "93"
SERVERCHAN_SENDKEY = os.environ.get("SCKEY")
STATE_FILE = "monitor_state.json"

def get_twitter_update():
    rss_url = f"https://rsshub.app/twitter/user/{TWITTER_USER}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        response = requests.get(rss_url, headers=headers, timeout=20)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            item = root.find(".//item")
            if item is not None:
                return {
                    "id": item.find("guid").text if item.find("guid") is not None else item.find("link").text,
                    "title": item.find("title").text,
                    "link": item.find("link").text,
                    "source": "Twitter"
                }
    except Exception as e:
        print(f"Twitter 获取失败: {e}")
    return None

def get_binance_update():
    api_url = "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query"
    payload = {"type": 1, "catalogId": BINANCE_CATALOG_ID, "pageNo": 1, "pageSize": 5}
    try:
        res = requests.post(api_url, json=payload, timeout=20)
        if res.status_code == 200:
            articles = res.json().get("data", {}).get("catalogs", [{}])[0].get("articles", [])
            if articles:
                latest = articles[0]
                return {
                    "id": str(latest['id']),
                    "title": latest['title'],
                    "link": f"https://www.binance.com/zh-CN/support/announcement/{latest['code']}",
                    "source": "币安公告"
                }
    except Exception as e:
        print(f"币安公告获取失败: {e}")
    return None

def send_wechat(msg):
    if not SERVERCHAN_SENDKEY:
        print("未检测到 SCKEY")
        return
    url = f"https://sctapi.ftqq.com/{SERVERCHAN_SENDKEY}.send"
    payload = {
        "title": f"【{msg['source']}】新动态",
        "desp": f"### {msg['title']}\n\n[点击查看详情]({msg['link']})"
    }
    requests.post(url, data=payload, timeout=10)

def main():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
    else:
        state = {"twitter_last_id": "", "binance_last_id": ""}

    t_msg = get_twitter_update()
    if t_msg and t_msg['id'] != state.get("twitter_last_id"):
        send_wechat(t_msg)
        state["twitter_last_id"] = t_msg['id']

    b_msg = get_binance_update()
    if b_msg and b_msg['id'] != state.get("binance_last_id"):
        send_wechat(b_msg)
        state["binance_last_id"] = b_msg['id']

    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

if __name__ == "__main__":
    main()
