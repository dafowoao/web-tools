import urllib.request, re, json, os

def fetch_lottery(url, td_reds, td_blues):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    html = urllib.request.urlopen(req, timeout=10).read().decode('gbk', errors='ignore')
    matches = re.findall(r'<tr class="t_tr1">(.*?)</tr>', html, re.DOTALL)
    data = []
    for m in matches:
        tds = re.findall(r'<td[^>]*>(.*?)</td>', m)
        clean = [re.sub(r'<[^>]+>', '', t).strip() for t in tds]
        idx = max(td_reds + td_blues) + 1
        if len(clean) <= idx: continue
        reds = [clean[i] for i in td_reds]
        blues = [clean[i] for i in td_blues]
        issue = clean[1] if len(clean) > 1 else ''
        date = clean[-1] if len(clean) > 2 else ''
        if all(r.isdigit() for r in reds) and all(b.isdigit() for b in blues):
            data.append({"reds": reds, "blue": blues, "issue": issue, "date": date})
    return data

def analyze(data, red_max, blue_max):
    red_freq = {i: 0 for i in range(1, red_max + 1)}
    blue_freq = {i: 0 for i in range(1, blue_max + 1)}
    for d in data:
        for r in d["reds"]:
            n = int(r)
            if n in red_freq: red_freq[n] += 1
        for b in d["blue"]:
            n = int(b)
            if n in blue_freq: blue_freq[n] += 1
    recent = data[:50] if len(data) >= 50 else data
    recent_red = {i: 0 for i in range(1, red_max + 1)}
    for d in recent:
        for r in d["reds"]:
            n = int(r)
            if n in recent_red: recent_red[n] += 1
    return {
        "red_freq": {str(k): v for k, v in red_freq.items()},
        "blue_freq": {str(k): v for k, v in blue_freq.items()},
        "hot_reds": sorted(recent_red, key=lambda x: -recent_red[x])[:8],
        "cold_reds": sorted(recent_red, key=lambda x: recent_red[x])[:8],
        "hot_blues": sorted(blue_freq, key=lambda x: -blue_freq[x])[:5],
        "recent": [{"reds": d["reds"], "blue": d["blue"], "issue": d.get("issue",""), "date": d.get("date","")} for d in data[:50]],
    }

print("正在获取双色球数据...")
ssq_data = fetch_lottery(
    "https://datachart.500.com/ssq/history/newinc/history.php?start=24001&end=26070",
    [2, 3, 4, 5, 6, 7], [8]
)
ssq = analyze(ssq_data, 33, 16)
print(f"  获取 {len(ssq_data)} 期")

print("正在获取大乐透数据...")
dlt_data = fetch_lottery(
    "https://datachart.500.com/dlt/history/newinc/history.php?start=24001&end=26070",
    [2, 3, 4, 5, 6], [7, 8]
)
dlt = analyze(dlt_data, 35, 12)
print(f"  获取 {len(dlt_data)} 期")

path = os.path.join(os.path.dirname(__file__) or '.', 'lottery_data.json')
with open(path, 'w', encoding='utf-8') as f:
    json.dump({"ssq": ssq, "dlt": dlt}, f, ensure_ascii=False)

# 同时生成 JS 嵌入文件（供 file:// 协议使用）
js_path = os.path.join(os.path.dirname(__file__) or '.', 'lottery_data.js')
with open(js_path, 'w', encoding='utf-8') as f:
    from datetime import datetime
    f.write(f'// 自动更新于 {datetime.now().strftime("%Y-%m-%d %H:%M")}\n')
    f.write('var LOTTERY_DATA_EMBEDDED = ')
    json.dump({"ssq": ssq, "dlt": dlt}, f, ensure_ascii=False)
    f.write(';\n')

print(f"数据已保存到 {path}")
print(f"JS 嵌入文件已保存到 {js_path}")
print(f"\n双色球热号: {ssq['hot_reds']}  冷号: {ssq['cold_reds']}")
print(f"大乐透热号: {dlt['hot_reds']}  冷号: {dlt['cold_reds']}")