#!/usr/bin/env python3
"""AI 每日新闻 — 知乎热门 + GitHub AI 趋势"""
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

# ========== 知乎 AI 相关话题 ==========
ZHIHU_TOPICS = [
    "人工智能", "大模型", "ChatGPT", "AI编程", "机器学习",
    "深度学习", "OpenAI", "自动驾驶", "AI绘画", "AI助手",
]

def fetch_zhihu():
    """从知乎搜索 AI 相关内容"""
    items = []
    try:
        for topic in ZHIHU_TOPICS:
            try:
                url = f"https://api.zhihu.com/search?q={urllib.request.quote(topic)}&limit=5"
                data = get(url, headers={"x-udid": "dummy"})
                for entry in data.get("data", []):
                    obj = entry.get("object", entry)
                    title = obj.get("title", "") or obj.get("question", {}).get("title", "")
                    url_link = obj.get("url", "")
                    excerpt = obj.get("excerpt", "")[:200]
                    vote = obj.get("voteup_count", 0)
                    if not title:
                        continue
                    items.append({
                        "title": title, "url": url_link.replace("api.zhihu.com", "www.zhihu.com"),
                        "desc": excerpt, "source": "知乎", "sourceColor": "#0066ff",
                        "ts": int(datetime.now().timestamp()), "score": vote,
                        "category": classify_cn(title, excerpt), "tags": ["知乎热榜"],
                    })
            except: continue
    except Exception as e:
        print(f"  知乎错误: {e}")
    return items

def fetch_github_trending():
    """从 GitHub Trending 获取 AI 相关仓库"""
    items = []
    try:
        data = get("https://api.github.com/search/repositories?q=AI+created:>2026-06-01&sort=stars&per_page=15",
                   headers={"Accept": "application/vnd.github+json"})
        for repo in data.get("items", []):
            name = repo.get("full_name", "")
            desc = repo.get("description", "") or ""
            stars = repo.get("stargazers_count", 0)
            url = repo.get("html_url", "")
            lang = repo.get("language") or ""
            created = repo.get("created_at", "")
            ts = 0
            if created:
                try:
                    dt = datetime.strptime(created[:19], "%Y-%m-%dT%H:%M:%S")
                    ts = int(dt.replace(tzinfo=timezone.utc).timestamp())
                except: pass
            items.append({
                "title": f"[{lang}] {name}" if lang else name,
                "url": url, "desc": desc[:200],
                "source": "GitHub Trending", "sourceColor": "#24292e",
                "ts": ts, "score": stars,
                "category": "tools", "tags": ["🔥 热门"] if stars > 200 else [],
            })
    except Exception as e:
        print(f"  GitHub 错误: {e}")
    return items

def fetch_36kr():
    """从 36kr 获取 AI 文章（直接用 JSON API）"""
    items = []
    try:
        data = get("https://36kr.com/api/newsflash?per_page=20")
        for item in data.get("data", {}).get("items", []):
            title = item.get("title", "")
            if not title: continue
            url = f"https://www.36kr.com/p/{item.get('id', '')}"
            desc = item.get("summary", "")[:200]
            ts = item.get("published_at", 0)
            items.append({
                "title": title, "url": url, "desc": desc,
                "source": "36氪", "sourceColor": "#1db48c",
                "ts": ts, "score": 0,
                "category": classify_cn(title, desc), "tags": [],
            })
    except: pass
    return items

def classify_cn(title, desc=""):
    t = (title + " " + desc)
    if any(k in t for k in ["模型", "gpt", "chatgpt", "claude", "gemini", "llama", "语言模型"]):
        return "llm"
    if any(k in t for k in ["编程", "代码", "工具", "开源", "开发", "github"]):
        return "tools"
    if any(k in t for k in ["研究", "论文", "实验", "科学", "数据集"]):
        return "research"
    if any(k in t for k in ["融资", "投资", "市场", "上市", "监管", "政策"]):
        return "industry"
    if any(k in t for k in ["中国", "北京", "华为", "百度", "阿里", "腾讯", "字节"]):
        return "china"
    return random.choice(["llm", "tools", "industry"])

def main():
    print("=" * 40)
    print("AI 每日新闻更新")
    print("=" * 40)

    all_items = []

    print("= 知乎 AI...")
    zhihu = fetch_zhihu()
    all_items.extend(zhihu)
    print(f"  {len(zhihu)} 条")

    print("= GitHub AI 趋势...")
    github = fetch_github_trending()
    all_items.extend(github)
    print(f"  {len(github)} 条")

    print("= 36氪...")
    kr36 = fetch_36kr()
    all_items.extend(kr36)
    print(f"  {len(kr36)} 条")

    # 去重
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
        "count": len(unique),
        "items": unique,
    }

    path = os.path.join(os.path.dirname(__file__) or ".", "ai-news.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    cats = {}
    srcs = {}
    for i in unique:
        cats[i["category"]] = cats.get(i["category"], 0) + 1
        srcs[i["source"]] = srcs.get(i["source"], 0) + 1
    print(f"\n✅ 总计 {len(unique)} 条")
    print(f"分类: {json.dumps(cats, ensure_ascii=False)}")
    print(f"来源: {json.dumps(srcs, ensure_ascii=False)}")

if __name__ == "__main__":
    main()
