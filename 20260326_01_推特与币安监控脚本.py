import requests
import os
import json
import xml.etree.ElementTree as ET

# --- 配置区 ---
TWITTER_USER = "alpha123cc"
SERVERCHAN_SENDKEY = os.environ.get("SCKEY")
STATE_FILE = "monitor_state.json"

def get_twitter_update():
    print(f"--- 正在检查推特 (@{TWITTER_USER}) ---")
    # Nitter 源（刚才日志里成功的那个）
    url = f"https://nitter.net/{TWITTER_USER}/rss"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            root = ET.fromstring(res.content)
            item = root.find(".//item")
            if item is not None:
                print("✅ 推特数据获取成功")
                return {
                    "id": item.find("guid").text if item.find("guid") is not None else item.find("link").text,
                    "title": item.find("title").text,
                    "link": item.find("link").text,
                    "source": "Twitter"
                }
    except Exception as e:
        print(f"❌ 推特获取失败: {e}")
    return None

def get_binance_update():
    print("--- 正在检查币安公告 ---")
    # 既然 API 403，我们换成 RSSHub 镜像来抓取币安公告，这通常能绕过 IP 屏蔽
    # 路径 93 是新币上市公告
    rss_urls = [
        "https://rsshub.app/binance/announcement/93",
        "https://rsshub.rssforever.com/binance/announcement/93"
    ]
    headers = {'User-Agent': 'Mozilla/5.0'}
    for url in rss_urls:
        try:
            print(f"尝试从 RSS 获取币安公告: {url}")
            res = requests.get(url, headers=headers, timeout=15)
            if res.status_code == 200:
                root = ET.fromstring(res.content)
                item = root.find(".//item")
                if item is not None:
                    print("✅ 币安公告获取成功")
                    return {
                        "id": item.find("guid").text if item.find("guid") is not None else item.find("link").text,
                        "title": item.find("title").text,
                        "link": item.find("link").text,
                        "source": "币安公告"
                    }
            print(f"⚠️ 状态码: {res.status_code}")
        except Exception as e:
            print(f"❌ 币安 RSS 异常: {e}")
    return None

def send_wechat(msg):
    if not SERVERCHAN_SENDKEY: return
    print(f"🚀 正在发送微信通知: {msg['title']}")
    url = f"https://sctapi.ftqq.com/{SERVERCHAN_SENDKEY}.send"
    data = {"title": f"【{msg['source']}】新动态", "desp": f"{msg['title']}\n\n[查看详情]({msg['link']})"}
    try:
        r = requests.post(url, data=data, timeout=10)
        print(f"微信返回: {r.text}")
    except:
        print("❌ 发送失败")

def main():
    print("=== 监控任务启动 ===")
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
