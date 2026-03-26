import requests
import os
import json
import time
import xml.etree.ElementTree as ET

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
        requests.post(url, data=data, timeout=10)
        print("✅ 微信推送成功")
    except Exception as e:
        print(f"❌ 微信推送失败: {e}")

def get_twitter_update():
    print(f"--- 检查推特 (@{TWITTER_USER}) ---")
    urls = ["https://nitter.net/alpha123cc/rss", "https://nitter.cz/alpha123cc/rss"]
    for url in urls:
        try:
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
        except: pass
    return None

def get_binance_update():
    print("--- 启动币安中文多节点防封锁轮询 ---")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0'}

    # 【第一层：币安官方镜像节点】（规避 .com 的主防火墙）
    mirrors = ["https://www.binance.info", "https://www.binance.me"]
    payload = {"type": 1, "catalogId": "93", "pageNo": 1, "pageSize": 5}
    for domain in mirrors:
        try:
            print(f"尝试官方镜像节点: {domain} ...")
            url = f"{domain}/bapi/composite/v1/public/cms/article/list/query"
            res = requests.post(url, json=payload, headers={"Lang": "zh-CN", **headers}, timeout=10)
            if res.status_code == 200:
                articles = res.json().get("data", {}).get("catalogs", [{}])[0].get("articles", [])
                if articles:
                    print("✅ 官方镜像节点抓取成功！")
                    return {"id": str(articles[0]["id"]), "title": articles[0]["title"], "link": f"{domain}/zh-CN/support/announcement/{articles[0]['code']}"}
        except: pass

    # 【第二层：稳定的社区高速 RSS 节点池】
    rss_nodes = [
        "https://rsshub.rssforever.com",
        "https://rsshub.liubing.me",
        "https://rss.shab.fun",
        "https://rss.peo.pw"
    ]
    for node in rss_nodes:
        try:
            print(f"尝试社区节点: {node} ...")
            res = requests.get(f"{node}/binance/announcement/93", headers=headers, timeout=10)
            if res.status_code == 200:
                root = ET.fromstring(res.content)
                item = root.find(".//item")
                if item is not None:
                    print("✅ 社区节点抓取成功！")
                    return {
                        "id": item.find("guid").text if item.find("guid") is not None else item.find("link").text,
                        "title": item.find("title").text,
                        "link": item.find("link").text
                    }
        except: pass

    # 【第三层：无敌兜底 - 星球日报官方 API】(100%无防爬虫拦截)
    try:
        print("尝试终极兜底节点 (全网快讯) ...")
        res = requests.get("https://www.odaily.news/api/pp/api/info-flow/newsflash_columns/newsflashes?per_page=20", headers=headers, timeout=10)
        if res.status_code == 200:
            for item in res.json().get("data", {}).get("items", []):
                title = item.get("title", "")
                # 只要快讯里包含“币安”和“活动/上线/锦标赛”等字眼，立刻抓取！
                if "币安" in title and any(kw in title for kw in ["上线", "活动", "锦标赛", "Launchpool"]):
                    print("✅ 兜底快讯节点抓取成功！")
                    return {"id": str(item["id"]), "title": title, "link": item.get("news_url") or item.get("url")}
    except: pass

    print("❌ 所有节点均被拦截或超时")
    return None

def main():
    print(f"=== 监控启动 {time.strftime('%Y-%m-%d %H:%M:%S')} ===")
    
    # 强制发送一条测试消息，确保微信通畅
    send_wechat("集群测试", "如果收到这条，说明底层通信正常。马上开始多节点轮询...")
    
    state = {"twitter_last_id": "", "binance_last_id": ""}
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            try: state = json.load(f)
            except: pass

    # 1. 推特逻辑
    t = get_twitter_update()
    if t and t['id'] != state.get("twitter_last_id"):
        send_wechat(t['title'], f"链接: {t['link']}", "推特")
        state["twitter_last_id"] = t['id']

    # 2. 币安逻辑
    b = get_binance_update()
    if b and b['id'] != state.get("binance_last_id"):
        send_wechat(b['title'], f"链接: {b['link']}", "币安最新活动")
        state["binance_last_id"] = b['id']

    with open(STATE_FILE, "w") as f:
        json.dump(state, f)
    print("=== 运行结束 ===")

if __name__ == "__main__":
    main()
