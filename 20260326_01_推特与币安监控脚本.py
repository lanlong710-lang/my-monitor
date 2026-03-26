import requests
import os
import json
import xml.etree.ElementTree as ET
import time

# --- 配置区 ---
TWITTER_USER = "alpha123cc"
SERVERCHAN_SENDKEY = os.environ.get("SCKEY")
STATE_FILE = "monitor_state.json"

def send_wechat(title, content, source="监控系统"):
    if not SERVERCHAN_SENDKEY:
        print("⚠️ 没找到 SCKEY，请检查 GitHub Secrets")
        return
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
    # 多个推特 RSS 镜像源
    urls = [
        f"https://nitter.net/{TWITTER_USER}/rss",
        f"https://nitter.cz/{TWITTER_USER}/rss",
        f"https://rsshub.app/twitter/user/{TWITTER_USER}"
    ]
    for url in urls:
        try:
            print(f"尝试源: {url}")
            res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
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
            print(f"⚠️ 状态码: {res.status_code}")
        except Exception as e:
            print(f"❌ 该源失败: {e}")
    return None

def get_binance_update():
    print("--- 正在检查币安公告 ---")
    # 尝试币安官方的另一种 RSS 路径
    urls = [
        "https://www.binance.com/zh-CN/support/announcement/c-48?format=rss",
        "https://rsshub.rssforever.com/binance/announcement/93"
    ]
    for url in urls:
        try:
            print(f"尝试币安源: {url}")
            res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
            if res.status_code == 200:
                root = ET.fromstring(res.content)
                item = root.find(".//item")
                if item is not None:
                    print("✅ 币安数据获取成功")
                    return {
                        "id": item.find("guid").text if item.find("guid") is not None else item.find("link").text,
                        "title": item.find("title").text,
                        "link": item.find("link").text
                    }
            print(f"⚠️ 状态码: {res.status_code}")
        except: pass
    return None

def main():
    print(f"=== 监控启动 {time.strftime('%H:%M:%S')} ===")
    
    # 【测试代码】每次运行强制发一条，确认微信通不通！成功后可删除
    send_wechat("连接测试", f"时间: {time.strftime('%H:%M:%S')}，如果你看到这条，说明SCKEY完全没问题！", "系统检测")

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
            print("ℹ️ 推特无新内容")
    else:
        print("❌ 所有推特源均失效")

    # 2. 币安逻辑
    b = get_binance_update()
    if b:
        if b['id'] != state.get("binance_last_id"):
            send_wechat(b['title'], f"链接: {b['link']}", "币安")
            state["binance_last_id"] = b['id']
        else:
            print("ℹ️ 币安无新内容")
    else:
        print("❌ 所有币安源均失效")

    with open(STATE_FILE, "w") as f:
        json.dump(state, f)
    print("=== 运行结束 ===")

if __name__ == "__main__":
    main()
