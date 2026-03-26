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
    print(f"--- 正在检查推特 (@{TWITTER_USER}) ---")
    # 尝试使用不同的 RSSHub 镜像，官方 app 实例经常被推特封 IP
    rss_urls = [
        f"https://rsshub.app/twitter/user/{TWITTER_USER}",
        f"https://rsshub.rssforever.com/twitter/user/{TWITTER_USER}"
    ]
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    for url in rss_urls:
        try:
            print(f"尝试从 {url} 获取数据...")
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
            else:
                print(f"❌ 状态码异常: {response.status_code}")
        except Exception as e:
            print(f"❌ 该镜像请求失败: {e}")
    return None

def get_binance_update():
    print("--- 正在检查币安公告 ---")
    api_url = "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query"
    payload = {"type": 1, "catalogId": BINANCE_CATALOG_ID, "pageNo": 1, "pageSize": 5}
    try:
        res = requests.post(api_url, json=payload, timeout=15)
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
        print(f"❌ 币安 API 异常: {res.status_code}")
    except Exception as e:
        print(f"❌ 币安获取异常: {e}")
    return None

def send_wechat(msg):
    if not SERVERCHAN_SENDKEY:
        print("⚠️ 错误: 环境变量中未找到 SCKEY，请检查 GitHub Secrets 配置！")
        return
    
    print(f"🚀 正在发送微信通知: {msg['title']}")
    url = f"https://sctapi.ftqq.com/{SERVERCHAN_SENDKEY}.send"
    payload = {
        "title": f"【{msg['source']}】新消息",
        "desp": f"### {msg['title']}\n\n[点击链接查看详情]({msg['link']})"
    }
    try:
        r = requests.post(url, data=payload, timeout=10)
        print(f"微信接口返回: {r.text}")
    except Exception as e:
        print(f"❌ 发送微信失败: {e}")

def main():
    print("=== 监控任务启动 ===")
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
        print(f"读取到历史状态: Twitter={state.get('twitter_last_id')}, Binance={state.get('binance_last_id')}")
    else:
        state = {"twitter_last_id": "", "binance_last_id": ""}
        print("未发现历史状态，将进行首次推送")

    # 检查推特
    t_msg = get_twitter_update()
    if t_msg:
        if t_msg['id'] != state.get("twitter_last_id"):
            send_wechat(t_msg)
            state["twitter_last_id"] = t_msg['id']
        else:
            print("推特无新动态")

    # 检查币安
    b_msg = get_binance_update()
    if b_msg:
        if b_msg['id'] != state.get("binance_last_id"):
            send_wechat(b_msg)
            state["binance_last_id"] = b_msg['id']
        else:
            print("币安无新动态")

    # 保存状态
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)
    print("=== 任务结束 ===")

if __name__ == "__main__":
    main()
