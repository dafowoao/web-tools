#!/usr/bin/env python3
"""进化中心监控后端 — 采集数据 + 生成看板 + 告警"""
import os, sys, json, datetime, subprocess, glob, hashlib

HOME = os.path.expanduser("~")
EVO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(EVO, "测试集", ".监控数据.json")
LAST_RUN = os.path.join(EVO, "测试集", ".上次告警.txt")

def collect():
    """采集各工具配置状态"""
    targets = {
        "ATOMCODE": os.path.join(HOME, ".atomcode", "ATOMCODE.md"),
        "Hermes": os.path.join(HOME, "AppData", "Local", "hermes", "SOUL.md"),
        "CodeBuddy": os.path.join(HOME, ".codebuddy", "CODEBUDDY.md"),
    }

    data = {
        "time": datetime.datetime.now().isoformat(),
        "agents": {},
        "rules": {"total": 0, "applied": 0},
        "alerts": [],
    }

    # 采集各工具
    for name, path in targets.items():
        if not os.path.exists(path):
            data["agents"][name] = {"status": "missing", "size": 0}
            data["alerts"].append(f"{name}: 配置文件缺失")
            continue
        size = os.path.getsize(path)
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        rules_found = [line for line in content.split('\n') if '进化中心规则' in line]
        data["agents"][name] = {"status": "ok", "size": size, "rules": len(rules_found)}
        data["rules"]["applied"] += len(rules_found)

    data["rules"]["total"] = 7  # 总规则数

    # 检查测试状态
    test_files = glob.glob(os.path.join(EVO, "测试集", "*test*.py")) + \
                 glob.glob(os.path.join(EVO, "测试集", "*评测*.py"))
    data["tests"] = {"total": len(test_files), "passed": 0}

    # 保存
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return data

def check_alerts(data):
    """检查是否需要告警"""
    alerts = []
    for name, info in data.get("agents", {}).items():
        if info.get("status") == "missing":
            alerts.append(f"⚠️ {name} 配置丢失")
    if data.get("rules", {}).get("applied", 0) == 0:
        alerts.append("⚠️ 没有规则被分发到任何工具")

    # 桌面弹窗（仅当有新的告警）
    if alerts:
        last = ""
        if os.path.exists(LAST_RUN):
            with open(LAST_RUN, 'r') as f:
                last = f.read().strip()
        now = str(alerts)
        if now != last:
            try:
                msg = " | ".join(alerts)
                subprocess.run(['powershell', '-Command',
                    f'Write-Host "{msg}"'], capture_output=True, timeout=10)
                print(f"\n🔔 告警: {msg}")
            except: pass
            with open(LAST_RUN, 'w') as f:
                f.write(now)

    return alerts

def gen_report(data):
    """生成可读报告"""
    t = data.get("time", "")[:19]
    print(f"\n{'='*50}")
    print(f"📊 进化中心监控报告 {t}")
    print(f"{'='*50}")
    for name, info in data.get("agents", {}).items():
        s = info.get("status", "?")
        r = info.get("rules", 0)
        sz = info.get("size", 0)
        print(f"  {'✅' if s=='ok' else '❌'} {name:12s} {r}条规则 ({sz:,} bytes)")

    rt = data.get("rules", {})
    pct = rt["applied"] / rt["total"] * 100 if rt["total"] else 0
    print(f"\n  规则覆盖率: {rt['applied']}/{rt['total']} ({pct:.0f}%)")
    print(f"  测试文件: {data.get('tests', {}).get('total', 0)} 个")

    alerts = data.get("alerts", [])
    if alerts:
        print(f"  ⚠️ {len(alerts)} 条告警")
        for a in alerts:
            print(f"    {a}")

if __name__ == "__main__":
    data = collect()
    check_alerts(data)
    gen_report(data)

    # 定时运行模式
    if "--watch" in sys.argv:
        import time
        print(f"\n🔄 监控模式启动 (每30分钟采集一次)")
        while True:
            time.sleep(1800)
            data = collect()
            check_alerts(data)
            gen_report(data)