#!/usr/bin/env python3
"""AI 每日新闻更新脚本 — 从 Hacker News 获取 AI 相关资讯"""
import urllib.request, json, gzip, re, os, random
from datetime import datetime, timezone

CACHE = {}

def get(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; AI-News-Bot/1.0)"
    })
    with urllib.request.urlopen(req, timeout=15) as r:
        data = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            data = gzip.decompress(data)
        return json.loads(data)

# AI 关键词（匹配标题和描述）
AI_KEYWORDS = [
    "ai", "artificial intelligence", "machine learning", "deep learning",
    "llm", "large language model", "gpt", "chatgpt", "openai", "claude",
    "anthropic", "gemini", "llama", "mistral", "copilot", "neural",
    "transformer", "diffusion", "embedding", "rag", "agentic",
    "autonomous agent", "fine-tuning", "multimodal", "vision model",
    "open source ai", "hugging face", "pytorch", "tensorflow",
    "langchain", "vector database", "ai coding", "code generation",
    "ai assistant", "deepseek", "qwen", "yi-34b", "minimax",
]

# 来源颜色
SOURCE_COLORS = {
    "Hacker News": "#ff6600", "TechCrunch": "#0a9e01",
    "The Verge": "#1b7fed", "ArXiv": "#b31b1b",
    "GitHub": "#24292e", "Medium": "#00ab6c",
    "VentureBeat": "#f05a28", "其他": "#6b9eff",
}

def fetch_hackernews():
    """从 Hacker News 获取 AI 相关热门"""
    items = []
    try:
        top = get("https://hacker-news.firebaseio.com/v0/topstories.json")[:60]
        for sid in top:
            try:
                s = get(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json")
                if not s or not s.get("title"): continue
                title = s["title"]
                text = (title + " " + (s.get("text") or "")).lower()
                # 检查是否匹配 AI 关键词
                matches = [kw for kw in AI_KEYWORDS if kw in text]
                if not matches: continue
                url = s.get("url") or f"https://news.ycombinator.com/item?id={sid}"
                desc = s.get("text") or ""
                if desc: desc = re.sub(r'<[^>]+>', '', desc)[:200]
                score = s.get("score", 0)
                # 智能分类
                cat = classify(title, desc)
                tags = ["hot"] if score > 50 else []
                tags.append(random.choice(cat.split()))
                if matches:
                    tags.append(matches[0][:12] if len(matches[0])<=12 else matches[0])
                items.append({
                    "title": title, "url": url, "desc": desc,
                    "source": "Hacker News", "sourceColor": SOURCE_COLORS["Hacker News"],
                    "ts": s.get("time", 0), "score": score,
                    "category": cat, "tags": tags[:4],
                })
            except: continue
    except Exception as e:
        print(f"HN 错误: {e}")
    return items

def classify(title, desc=""):
    """基于关键词分类"""
    t = (title + " " + desc).lower()
    if any(k in t for k in ["china", "chinese", "bytedance", "baidu", "alibaba", "tencent", "deepseek", "qwen", "zhipu", "minimax", "kimi"]):
        return "china"
    if any(k in t for k in ["model", "llm", "gpt", "claude", "gemini", "llama", "mistral", "deepseek", "transformer"]):
        return "llm"
    if any(k in t for k in ["tool", "code", "copilot", "cursor", "dev", "programming", "github", "open source"]):
        return "tools"
    if any(k in t for k in ["paper", "research", "arxiv", "study", "scientific", "benchmark", "dataset"]):
        return "research"
    if any(k in t for k in ["startup", "funding", "invest", "market", "revenue", "ipo", "regulation", "law", "policy"]):
        return "industry"
    return random.choice(["llm", "tools", "industry"])

def main():
    print("获取 AI 新闻...")
    items = fetch_hackernews()

    # 按时间排序
    items.sort(key=lambda x: x["ts"], reverse=True)

    # 限制数量
    items = items[:40]

    output = {
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "count": len(items),
        "items": items,
    }

    path = os.path.join(os.path.dirname(__file__) or ".", "ai-news.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"已保存 {len(items)} 条新闻到 {path}")

    # 分类统计
    cats = {}
    for i in items:
        cats[i["category"]] = cats.get(i["category"], 0) + 1
    print("分类统计:", json.dumps(cats, ensure_ascii=False))

if __name__ == "__main__":
    main()
