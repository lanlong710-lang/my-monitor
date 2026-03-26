import requests
import os
import json
import time
import urllib.parse

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
    url = f"https://nitter.net/{TWITTER_USER}/rss"
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        if res.status_code == 200:
            import xml.etree.ElementTree as ET
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
    print("--- 检查币安中文官网 (通过 RSS2JSON 高级节点穿透) ---")
    
    # 币安最新活动官方中文 RSS。加入时间戳防止节点缓存，强制获取最新！
    timestamp = int(time.time())
    binance_rss = f"https://www.binance.com/zh-CN/support/announcement/c-48?format=rss&_t={timestamp}"
    
    # 将币安链接进行 URL 编码
    encoded_url = urllib.parse.quote(binance_rss, safe='')
    
    # 使用国际公共 API 转换器，完美绕过币安对 GitHub 的 IP 封锁
    api_url = f"https://api.rss2json.com/v1/api.json?rss_url={encoded_url}"
    
    try:
        print("正在通过高级节点请求数据...")
        res = requests.get(api_url, timeout=20)
        data = res.json()
        
        if data.get("status") == "ok" and data.get("items"):
            latest = data["items"][0]
            # 提取清洗后的纯正中文标题
            title = latest.get("title", "").strip()
            link = latest.get("link", "")
            guid = latest.get("guid", link)
            
            print(f"✅ 成功穿透防火墙！抓取到中文标题: {title}")
            return {"id": guid, "title": title, "link": link}
        else:
            print(f"⚠️ 节点返回异常或无数据: {data.get('message', '未知')}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    return None

def main():
    print(f"=== 监控启动 {time.strftime('%Y-%m-%d %H:%M:%S')} ===")
    
    state = {"twitter_last_id": "", "binance_last_id": ""}
    if os.path.exists(STATE_FILE):
        print("读取历史状态中...")
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
            print("ℹ️ 推特无新内容，跳过")

    # 2. 币安逻辑
    b = get_binance_update()
    if b:
        if b['id'] != state.get("binance_last_id"):
            send_wechat(b['title'], f"链接: {b['link']}", "币安最新活动")
            state["binance_last_id"] = b['id']
        else:
            print("ℹ️ 币安无新内容，跳过")

    with open(STATE_FILE, "w") as f:
        json.dump(state, f)
    print("=== 运行结束 ===")

if __name__ == "__main__":
    main()
