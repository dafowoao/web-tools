#!/usr/bin/env python3
"""AI 每日新闻更新脚本 — 全中文，多源聚合"""
import urllib.request, json, gzip, re, os, random, html
from datetime import datetime, timezone
from xml.etree import ElementTree

CACHE = {}

def get(url, binary=False, xml=False):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; AI-News-Bot/1.0)"
    })
    with urllib.request.urlopen(req, timeout=20) as r:
        data = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            data = gzip.decompress(data)
        if xml:
            return ElementTree.fromstring(data)
        if binary:
            return data
        return json.loads(data)

def fetch_rsshub(path):
    """从 RSSHub 获取中文新闻"""
    items = []
    url = f"https://rsshub.app{path}"
    try:
        xml_data = get(url, xml=True)
        for item in xml_data.findall(".//item") or xml_data.findall("channel/item"):
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            desc = item.findtext("description", "") or ""
            if desc:
                desc = re.sub(r'<[^>]+>', '', html.unescape(desc))[:200]
            pub_str = item.findtext("pubDate", "") or ""
            ts = 0
            if pub_str:
                try:
                    dt = datetime.strptime(pub_str[:25], "%a, %d %b %Y %H:%M:%S")
                    ts = int(dt.replace(tzinfo=timezone.utc).timestamp())
                except: pass
            if title:
                items.append({"title": title, "url": link, "desc": desc, "ts": ts})
    except Exception as e:
        print(f"  RSSHub {path} 错误: {e}")
    return items

# ========== 中文 AI 关键词 ==========
AI_KEYWORDS_CN = [
    "ai", "人工智能", "机器学习", "深度学习", "大模型", "大语言模型",
    "gpt", "chatgpt", "openai", "claude", "anthropic", "gemini",
    "llama", "mistral", "copilot", "神经网络", "扩散模型", "嵌入",
    "rag", "智能体", "微调", "多模态", "视觉模型", "hugging face",
    "pytorch", "tensorflow", "langchain", "向量数据库",
    "ai编程", "代码生成", "ai助手", "deepseek", "通义千问",
    "文心一言", "智谱", "kimi", "月之暗面", "minimax",
    "字节跳动", "百度", "阿里巴巴", "腾讯", "华为",
]

# ========== 来源配置 ==========
SOURCES = {
    "量子位": {"rss": "/qbitai", "color": "#2196f3"},
    "机器之心": {"rss": "/jiqizhixin", "color": "#e91e63"},
    "36氪 AI": {"rss": "/36kr/motif/ai?limit=10", "color": "#1db48c"},
    "IT之家 AI": {"rss": "/ithome/tag/AI?limit=10", "color": "#ff6a00"},
    "OSCHINA AI": {"rss": "/oschina/news?tags=AI&limit=10", "color": "#00a86b"},
    "品玩 AI": {"rss": "/pingwest/tag/AI?limit=10", "color": "#ff5722"},
    "DoNews AI": {"rss": "/donews?tag=AI&limit=10", "color": "#9c27b0"},
    "AI 科技评论": {"rss": "/leiphone?category=ai&limit=10", "color": "#00bcd4"},
    "新浪 AI": {"rss": "/sina/news?tag=AI&limit=8", "color": "#ff6a6a"},
    "腾讯 AI": {"rss": "/tencent/news/tag/AI/?limit=8", "color": "#2196f3"},
}

CAT_CN_KEYWORDS = {
    "llm": ["大模型", "语言模型", "gpt", "chatgpt", "claude", "gemini", "llama", "模型"],
    "tools": ["工具", "编程", "代码", "copilot", "cursor", "开发", "开源", "github"],
    "research": ["研究", "论文", "arxiv", "实验", "科学", "数据集"],
    "industry": ["融资", "投资", "市场", "上市", "营收", "监管", "政策", "法规", "财报"],
    "china": ["中国", "北京", "上海", "深圳", "华为", "百度", "阿里", "腾讯", "字节", "深度求索"],
}

def classify_cn(title, desc=""):
    t = (title + " " + desc)
    for cat, kws in CAT_CN_KEYWORDS.items():
        if any(k in t for k in kws):
            return cat
    return random.choice(["llm", "tools", "industry"])

def main():
    print("=" * 40)
    print("AI 每日新闻更新（国内源）")
    print("=" * 40)

    # 中文源
    all_items = []
    print("\n📡 获取中文源...")
    for name, cfg in SOURCES.items():
        print(f"  {name}...", end=" ", flush=True)
        items = fetch_rsshub(cfg["rss"])
        for it in items:
            it["source"] = name
            it["sourceColor"] = cfg["color"]
            it["category"] = classify_cn(it["title"], it.get("desc", ""))
            it["tags"] = []
        all_items.extend(items)
        print(f"{len(items)} 条")

    # 合并去重
    seen = set()
    unique = []
    for it in all_items:
        key = it["title"][:30]
        if key in seen: continue
        seen.add(key)
        unique.append(it)

    # 按时间排序
    unique.sort(key=lambda x: x["ts"], reverse=True)

    # 截断
    unique = unique[:50]

    output = {
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "count": len(unique),
        "items": unique,
    }

    path = os.path.join(os.path.dirname(__file__) or ".", "ai-news.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # 统计
    cats = {}
    srcs = {}
    for i in unique:
        cats[i["category"]] = cats.get(i["category"], 0) + 1
        srcs[i["source"]] = srcs.get(i["source"], 0) + 1
    print(f"\n✅ 总计 {len(unique)} 条新闻")
    print(f"分类: {json.dumps(cats, ensure_ascii=False)}")
    print(f"来源: {json.dumps(srcs, ensure_ascii=False)}")
    print(f"保存到: {path}")

if __name__ == "__main__":
    main()
