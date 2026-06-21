#!/usr/bin/env python3
"""自动治 — 同类问题出现3次自动生成规则"""
import os, sys, json, datetime, collections

EVO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEMORY = os.path.expanduser("~/.claude/projects/I--1/memory")
RULES_FILE = os.path.join(EVO, "测试集", "同步规则.py")

ERROR_DB = os.path.join(EVO, "测试集", ".错误模式.json")

def load_errors():
    if os.path.exists(ERROR_DB):
        with open(ERROR_DB, 'r', encoding='utf-8') as f:
            try: return json.load(f)
            except: pass
    return {"patterns": [], "generated_rules": []}

def save_errors(data):
    with open(ERROR_DB, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def record_error(category, detail):
    db = load_errors()
    db["patterns"].append({
        "time": datetime.datetime.now().isoformat(),
        "category": category,
        "detail": detail,
    })
    save_errors(db)

    # 统计同类问题
    recent = [p for p in db["patterns"][-20:]]
    counts = collections.Counter(p["category"] for p in recent)
    for cat, cnt in counts.items():
        if cnt >= 3 and cat not in [r["category"] for r in db["generated_rules"]]:
            rule = generate_rule(cat)
            db["generated_rules"].append({"category": cat, "rule": rule, "time": datetime.datetime.now().isoformat()})
            save_errors(db)
            print(f"✅ 自动生成规则: {cat} → 已分发")
            return True
    return False

def generate_rule(category):
    """根据错误类别自动生成规则文本"""
    templates = {
        "编码": f"代码必须通过语法检查才能提交，禁止提交有语法错误的代码",
        "性能": f"数据量超过1000时必须考虑时间复杂度，O(n²)算法不可接受",
        "安全": f"禁止将用户输入直接拼接到SQL/Shell命令中，必须使用参数化查询",
        "UI": f"所有HTML页面必须包含 viewport、CSS变量≥5、响应式断点≥4",
        "并发": f"共享变量必须加锁，禁止无保护的并发写入",
    }
    rule_text = templates.get(category, f"注意{category}类问题，已发生多次")
    print(f"  生成规则: {rule_text[:50]}...")
    return rule_text

def show_report():
    db = load_errors()
    print(f"\n📊 自动治报告")
    print(f"  总错误记录: {len(db['patterns'])}")
    counts = collections.Counter(p["category"] for p in db["patterns"])
    for cat, cnt in counts.most_common():
        print(f"    {cat}: {cnt}次")
    print(f"  已生成规则: {len(db['generated_rules'])}")
    for r in db["generated_rules"]:
        print(f"    ✅ {r['category']}: {r['rule'][:40]}...")

if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "record":
        record_error(sys.argv[2], " ".join(sys.argv[3:]) if len(sys.argv) > 3 else "")
    else:
        show_report()