import requests
import os
import json
import xml.etree.ElementTree as ET
import time

# --- 配置区 ---
TWITTER_USER = "alpha123cc"
SERVERCHAN_SENDKEY = os.environ.get("SCKEY")
STATE_FILE = "monitor_state.json"

def get_twitter_update():
    print(f"--- 正在检查推特 (@{TWITTER_USER}) ---")
    # Nitter 是目前抓取推特最稳的源
    url = f"https://nitter.net/{TWITTER_USER}/rss"
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=20)
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
        print(f"❌ 推特获取异常: {e}")
    return None

def get_binance_update():
    print("--- 正在检查币安公告 ---")
    # 尝试多个不同的镜像站，绕过币安对 GitHub IP 的封锁
    mirrors = [
        "https://rsshub.app/binance/announcement/93",
        "https://hub.001001.xyz/binance/announcement/93",
        "https://rss.lilyre.com/binance/announcement/93",
        "https://rsshub.rssforever.com/binance/announcement/93"
    ]
    
    for url in mirrors:
        try:
            print(f"尝试镜像: {url}")
            res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
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
            else:
                print(f"⚠️ 状态码: {res.status_code}")
        except Exception as e:
            print(f"❌ 该镜像超时或异常: {e}")
    return None

def send_wechat(msg):
    if not SERVERCHAN_SENDKEY: return
    print(f"🚀 准备推送微信: {msg['title']}")
    url = f"https://sctapi.ftqq.com/{SERVERCHAN_SENDKEY}.send"
    data = {
        "title": f"【{msg['source']}】新提醒", 
        "desp": f"内容：{msg['title']}\n\n[查看详情]({msg['link']})"
    }
    # 尝试推送，最多试2次
    for i in range(2):
        try:
            r = requests.post(url, data=data, timeout=15)
            print(f"微信返回结果: {r.text}")
            if r.status_code == 200: break
        except:
            print(f"推送第 {i+1} 次失败，正在重试...")
            time.sleep(2)

def main():
    print(f"=== 监控启动 {time.strftime('%Y-%m-%d %H:%M:%S')} ===")
    
    # 读取旧状态
    state = {"twitter_last_id": "", "binance_last_id": ""}
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            try:
                state = json.load(f)
            except: pass

    # 1. 处理推特
    t_msg = get_twitter_update()
    if t_msg:
        if t_msg['id'] != state.get("twitter_last_id"):
            send_wechat(t_msg)
            state["twitter_last_id"] = t_msg['id']
        else:
            print("ℹ️ 推特内容未更新，跳过推送")

    # 2. 处理币安
    b_msg = get_binance_update()
    if b_msg:
        if b_msg['id'] != state.get("binance_last_id"):
            send_wechat(b_msg)
            state["binance_last_id"] = b_msg['id']
        else:
            print("ℹ️ 币安公告未更新，跳过推送")

    # 保存新状态
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)
    print("=== 监控任务结束 ===")

if __name__ == "__main__":
    main()
