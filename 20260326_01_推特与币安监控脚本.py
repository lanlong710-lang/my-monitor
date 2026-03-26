import requests
import os
import json
import time
import xml.etree.ElementTree as ET

# --- 配置区 ---
TWITTER_USER = "binancezh"  # 监控币安中文官推
KEYWORDS = ["交易竞赛", "瓜分", "积分"] # 触发推送的关键词
SERVERCHAN_SENDKEY = os.environ.get("SCKEY")
STATE_FILE = "monitor_state.json"

def send_wechat(title, link, matched_kws):
    if not SERVERCHAN_SENDKEY: return
    print(f"🚀 触发关键词 {matched_kws}，准备推送微信...")
    url = f"https://sctapi.ftqq.com/{SERVERCHAN_SENDKEY}.send"
    
    # 微信卡片内容排版
    desp = f"### {title}\n\n**命中关键词**：{', '.join(matched_kws)}\n\n[🔗 点击这里直达推文]({link})"
    data = {"title": "🚨 币安活动预警", "desp": desp}
    
    try:
        requests.post(url, data=data, timeout=10)
        print("✅ 微信推送成功！")
    except Exception as e:
        print(f"❌ 微信推送失败: {e}")

def get_twitter_update():
    print(f"--- 正在检查推特 (@{TWITTER_USER}) ---")
    # 使用多个 Nitter 镜像源确保高可用
    urls = [
        f"https://nitter.net/{TWITTER_USER}/rss",
        f"https://nitter.cz/{TWITTER_USER}/rss",
        f"https://nitter.poast.org/{TWITTER_USER}/rss"
    ]
    for url in urls:
        try:
            res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
            if res.status_code == 200:
                root = ET.fromstring(res.content)
                item = root.find(".//item")
                if item is not None:
                    print("✅ 推特数据获取成功")
                    title = item.find("title").text if item.find("title") is not None else ""
                    desc = item.find("description").text if item.find("description") is not None else ""
                    link = item.find("link").text
                    guid = item.find("guid").text if item.find("guid") is not None else link
                    
                    # 把标题和正文拼在一起，全方位检测关键词
                    full_text = title + " " + desc
                    matched_kws = [kw for kw in KEYWORDS if kw in full_text]
                    
                    return {
                        "id": guid,
                        "title": title,
                        "link": link,
                        "matched": matched_kws
                    }
        except: pass
    print("❌ 所有推特源获取失败")
    return None

def main():
    print(f"=== 监控启动 {time.strftime('%Y-%m-%d %H:%M:%S')} ===")
    
    state = {"twitter_last_id": ""}
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            try: state = json.load(f)
            except: pass

    # 获取最新推文
    t = get_twitter_update()
    
    if t:
        if t['id'] != state.get("twitter_last_id"):
            # 发现新推文，更新记录防止下次重复处理
            state["twitter_last_id"] = t['id']
            
            # 判断是否包含我们想要的关键词
            if t['matched']:
                send_wechat(t['title'], t['link'], t['matched'])
            else:
                print(f"ℹ️ 最新推文未包含关键词。标题摘要: {t['title'][:30]}...")
        else:
            print("ℹ️ 暂无新推文发布。")

    # 保存状态
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)
    print("=== 运行结束 ===")

if __name__ == "__main__":
    main()
