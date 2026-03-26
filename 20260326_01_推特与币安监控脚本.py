import requests
import os
import json
import time
import xml.etree.ElementTree as ET

# --- 配置区 ---
TWITTER_ALPHA = "alpha123cc"        # 账号1：无条件全量推送
TWITTER_BINANCE = "binancezh"       # 账号2：只推送命中关键词的
BINANCE_KEYWORDS = ["交易竞赛", "瓜分", "积分"] # 账号2的触发关键词

SERVERCHAN_SENDKEY = os.environ.get("SCKEY")
STATE_FILE = "monitor_state.json"

def send_wechat(title, content, source="监控系统"):
    if not SERVERCHAN_SENDKEY: return
    print(f"🚀 准备推送微信: 【{source}】{title[:15]}...")
    url = f"https://sctapi.ftqq.com/{SERVERCHAN_SENDKEY}.send"
    data = {"title": f"【{source}】预警", "desp": f"### {title}\n\n{content}"}
    try:
        requests.post(url, data=data, timeout=10)
        print("✅ 微信推送成功！")
    except Exception as e:
        print(f"❌ 微信推送失败: {e}")

def fetch_tweets(username):
    print(f"--- 正在获取推特 (@{username}) ---")
    # 使用多个 Nitter 镜像源确保稳定抓取
    urls = [
        f"https://nitter.net/{username}/rss",
        f"https://nitter.cz/{username}/rss",
        f"https://nitter.poast.org/{username}/rss"
    ]
    for url in urls:
        try:
            res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
            if res.status_code == 200:
                root = ET.fromstring(res.content)
                item = root.find(".//item")
                if item is not None:
                    print(f"✅ @{username} 数据获取成功")
                    title = item.find("title").text if item.find("title") is not None else ""
                    desc = item.find("description").text if item.find("description") is not None else ""
                    link = item.find("link").text
                    guid = item.find("guid").text if item.find("guid") is not None else link
                    return {"id": guid, "title": title, "desc": desc, "link": link}
        except: pass
    print(f"❌ @{username} 获取失败")
    return None

def main():
    print(f"=== 监控启动 {time.strftime('%Y-%m-%d %H:%M:%S')} ===")
    
    # 初始化或读取历史记录
    state = {"alpha_last_id": "", "binance_last_id": ""}
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            try: state = json.load(f)
            except: pass

    # ---------------------------------------------------------
    # 逻辑 1：处理 alpha123cc (无条件直接推送)
    # ---------------------------------------------------------
    t_alpha = fetch_tweets(TWITTER_ALPHA)
    if t_alpha:
        if t_alpha['id'] != state.get("alpha_last_id"):
            state["alpha_last_id"] = t_alpha['id']
            # 直接推送，不需要判断关键词
            send_wechat(t_alpha['title'], f"[🔗 点击直达推文]({t_alpha['link']})", "Alpha动态")
        else:
            print(f"ℹ️ @{TWITTER_ALPHA} 暂无新推文。")

    # ---------------------------------------------------------
    # 逻辑 2：处理 binancezh (关键词精准过滤)
    # ---------------------------------------------------------
    t_binance = fetch_tweets(TWITTER_BINANCE)
    if t_binance:
        if t_binance['id'] != state.get("binance_last_id"):
            state["binance_last_id"] = t_binance['id']
            # 将标题和正文合并，检查是否包含关键词
            full_text = t_binance['title'] + " " + t_binance['desc']
            matched_kws = [kw for kw in BINANCE_KEYWORDS if kw in full_text]
            
            if matched_kws:
                content = f"**命中关键词**：{', '.join(matched_kws)}\n\n[🔗 点击直达推文]({t_binance['link']})"
                send_wechat(t_binance['title'], content, "币安活动")
            else:
                print(f"ℹ️ @{TWITTER_BINANCE} 新推文未命中关键词，自动过滤。")
        else:
            print(f"ℹ️ @{TWITTER_BINANCE} 暂无新推文。")

    # ---------------------------------------------------------
    # 保存状态
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)
    print("=== 运行结束 ===")

if __name__ == "__main__":
    main()
