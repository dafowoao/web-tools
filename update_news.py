#!/usr/bin/env python3
"""AI 每日新闻 — 纯中文源"""
import urllib.request, json, gzip, re, os, random
from datetime import datetime, timezone

def get(url, headers=None):
    h = {"User-Agent": "Mozilla/5.0 (compatible; AI-News-Bot/1.0)"}
    if headers: h.update(headers)
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=20) as r:
        data = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            data = gzip.decompress(data)
        return json.loads(data)

def fetch_36kr_cat(cat, limit=15):
    """从 36氪获取指定分类文章"""
    items = []
    try:
        data = get(f"https://36kr.com/api/newsflash?per_page={limit}&b_id={cat}")
        for item in data.get("data", {}).get("items", []):
            title = item.get("title", "")
            if not title: continue
            url = f"https://www.36kr.com/p/{item.get('id', '')}"
            desc = item.get("summary", "")[:200]
            ts = item.get("published_at", 0)
            if isinstance(ts, str):
                try: ts = int(datetime.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S").timestamp())
                except: ts = 0
            items.append({
                "title": title, "url": url, "desc": desc,
                "source": "36氪", "sourceColor": "#1db48c",
                "ts": ts, "score": 0,
                "category": classify_cn(title, desc), "tags": [],
            })
    except: pass
    return items

def fetch_hackernews_cn():
    """Hacker News AI 内容，标题保留英文但标注来源"""
    items = []
    try:
        top = get("https://hacker-news.firebaseio.com/v0/topstories.json")[:40]
        akw = ["ai", "artificial intelligence", "machine learning", "deep learning",
               "llm", "gpt", "chatgpt", "openai", "claude", "anthropic", "gemini",
               "llama", "mistral", "copilot", "neural", "transformer", "diffusion",
               "rag", "agent", "autonomous", "fine-tuning", "multimodal"]
        for sid in top:
            try:
                s = get(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json")
                if not s or not s.get("title"): continue
                title = s["title"]
                text = (title + " " + (s.get("text") or "")).lower()
                if not any(k in text for k in akw): continue
                url = s.get("url") or f"https://news.ycombinator.com/item?id={sid}"
                desc = s.get("text") or ""
                if desc: desc = re.sub(r'<[^>]+>', '', desc)[:200]
                items.append({
                    "title": title, "url": url, "desc": desc,
                    "source": "Hacker News", "sourceColor": "#ff6600",
                    "ts": s.get("time", 0), "score": s.get("score", 0),
                    "category": classify_cn(title, desc), "tags": ["国际"],
                })
            except: continue
    except: pass
    return items

def classify_cn(title, desc=""):
    t = (title + " " + desc)
    if any(k in t for k in ["模型", "gpt", "chatgpt", "claude", "gemini", "llama", "语言模型", "transformer"]):
        return "llm"
    if any(k in t for k in ["编程", "代码", "工具", "开源", "开发", "github", "copilot", "cursor"]):
        return "tools"
    if any(k in t for k in ["研究", "论文", "arxiv", "实验", "科学", "数据集"]):
        return "research"
    if any(k in t for k in ["融资", "投资", "市场", "上市", "营收", "监管", "政策", "财报"]):
        return "industry"
    if any(k in t for k in ["中国", "北京", "华为", "百度", "阿里", "腾讯", "字节"]):
        return "china"
    return random.choice(["llm", "tools", "industry"])

def main():
    print("=" * 40)
    print("AI 每日新闻更新")
    print("=" * 40)
    all_items = []

    # 36氪 AI 快讯
    print("36氪 AI...")
    kr = fetch_36kr_cat("ai", 30)
    all_items.extend(kr)
    print(f"  {len(kr)} 条")

    # Hacker News AI（国际资讯，英文标题）
    print("Hacker News AI...")
    hn = fetch_hackernews_cn()
    all_items.extend(hn)
    print(f"  {len(hn)} 条")

    # 去重排序
    seen = set()
    unique = []
    for it in all_items:
        key = it["title"][:25]
        if key in seen: continue
        seen.add(key)
        unique.append(it)
    unique.sort(key=lambda x: x["ts"], reverse=True)
    unique = unique[:50]

    output = {
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "count": len(unique), "items": unique,
    }

    path = os.path.join(os.path.dirname(__file__) or ".", "ai-news.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    cats = {}
    srcs = {}
    for i in unique:
        cats[i["category"]] = cats.get(i["category"], 0) + 1
        srcs[i["source"]] = srcs.get(i["source"], 0) + 1
    print(f"\n总计 {len(unique)} 条")
    print(f"分类: {json.dumps(cats, ensure_ascii=False)}")
    print(f"来源: {json.dumps(srcs, ensure_ascii=False)}")

if __name__ == "__main__":
    main()
