#!/usr/bin/env python3
"""效果度量 — 统计规则到底减少了多少 bug"""
import os, json, datetime, glob, subprocess

EVO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
METRICS_FILE = os.path.join(EVO, "测试集", ".效果数据.json")

def init_metrics():
    if os.path.exists(METRICS_FILE):
        with open(METRICS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "created": datetime.datetime.now().isoformat(),
        "bugs_found": 0,
        "bugs_fixed": 0,
        "rules_added": 0,
        "syncs_run": 0,
        "by_category": {},
        "by_rule": {},
    }

def save_metrics(m):
    with open(METRICS_FILE, 'w', encoding='utf-8') as f:
        json.dump(m, f, ensure_ascii=False, indent=2)

def record_bug(category="未知", rule=""):
    m = init_metrics()
    m["bugs_found"] += 1
    if category not in m["by_category"]:
        m["by_category"][category] = 0
    m["by_category"][category] += 1
    if rule:
        if rule not in m["by_rule"]:
            m["by_rule"][rule] = 0
        m["by_rule"][rule] += 1
    save_metrics(m)
    print(f"📊 已记录: {category} bug (+1)")

def record_fix():
    m = init_metrics()
    m["bugs_fixed"] += 1
    save_metrics(m)

def record_sync():
    m = init_metrics()
    m["syncs_run"] += 1
    save_metrics(m)

def show():
    m = init_metrics()
    print(f"\n{'='*45}")
    print(f"📈 效果度量")
    print(f"{'='*45}")
    print(f" 发现bug: {m['bugs_found']}")
    print(f" 修复bug: {m['bugs_fixed']}")
    print(f" 同步次数: {m['syncs_run']}")
    print(f" 规则总数: {m['rules_added']}")
    if m["bugs_found"] > 0:
        print(f" 修复率: {m['bugs_fixed']/m['bugs_found']*100:.0f}%")
    print(f"\n 分类统计:")
    for cat, cnt in sorted(m.get("by_category", {}).items(), key=lambda x: -x[1]):
        print(f"   {cat}: {cnt}次")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "bug":
            cat = sys.argv[2] if len(sys.argv) > 2 else "未知"
            rule = sys.argv[3] if len(sys.argv) > 3 else ""
            record_bug(cat, rule)
        elif sys.argv[1] == "fix":
            record_fix()
        elif sys.argv[1] == "sync":
            record_sync()
        else:
            show()
    else:
        show()