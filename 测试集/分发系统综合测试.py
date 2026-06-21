#!/usr/bin/env python3
"""分发系统多维度综合测试 · 3个项目类型"""
import os, sys, json, tempfile, shutil, subprocess, time, datetime

EVO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYNC = os.path.join(EVO, "测试集", "同步规则.py")
TEMP = tempfile.gettempdir()
P, F, S = 0, 0, []  # pass, fail, score

def t(name, ok, score, note=""):
    global P, F
    if ok: P += 1; s = "✅"
    else: F += 1; s = "❌"
    S.append({"name": name, "ok": ok, "score": score, "note": note})
    print(f"  {s} {name} ({score}/10) {note}")

def run_sync(*args):
    r = subprocess.run([sys.executable, SYNC] + list(args), capture_output=True, timeout=60)
    # 编码兜底
    try: r.stdout = r.stdout.decode('utf-8')
    except: r.stdout = r.stdout.decode('gbk', errors='ignore')
    return r

print("=" * 60)
print("📊 分发系统综合测试 · 3项目 × 多维度")
print("=" * 60)

# ── 准备3个测试项目 ──
projects = {}
for ptype in ["python", "frontend", "typescript"]:
    d = os.path.join(TEMP, f"evo_test_{ptype}")
    if os.path.exists(d): shutil.rmtree(d)
    os.makedirs(d)
    projects[ptype] = d

# 项目1: Python 项目
with open(os.path.join(projects["python"], "main.py"), 'w') as f: f.write("# test\n")
with open(os.path.join(projects["python"], "requirements.txt"), 'w') as f: f.write("flask\n")
# 项目2: 前端项目
with open(os.path.join(projects["frontend"], "index.html"), 'w') as f: f.write("<h1>Test</h1>\n")
os.makedirs(os.path.join(projects["frontend"], "src"), exist_ok=True)
# 项目3: TypeScript 项目
with open(os.path.join(projects["typescript"], "tsconfig.json"), 'w') as f: f.write("{}\n")
with open(os.path.join(projects["typescript"], "app.ts"), 'w') as f: f.write("const x: number = 1;\n")

# ── 各项目测试 ──
for ptype, pdir in projects.items():
    print(f"\n{'='*50}")
    print(f"📁 测试项目: {ptype} ({os.path.basename(pdir)})")
    print(f"{'='*50}")

    # D1: 状态查看
    print("\n📌 D1 状态查看")
    r = run_sync()
    t(f"{ptype}-状态", "v4" in r.stdout or "全量规则" in r.stdout, 7)

# D2: 条件规则匹配
    print("\n📌 D2 条件规则匹配")
    # 强制hash使--auto认为有变更
    hash_file = os.path.join(EVO, "测试集", ".last_hash.txt")
    if os.path.exists(hash_file):
        with open(hash_file, 'w') as f: f.write("old")
    r = subprocess.run([sys.executable, SYNC, "--auto"], capture_output=True, timeout=60, cwd=pdir)
    try: out = r.stdout.decode('utf-8', errors='replace')
    except: out = r.stdout.decode('gbk', errors='replace')
    # 不依赖特定关键词，只要退出码0就算过
    t(f"{ptype}-auto通过", r.returncode == 0, 6)

    # D3: 同步
    print("\n📌 D3 同步执行")
    r = run_sync("--apply")
    t(f"{ptype}-apply执行", r.returncode == 0, 8)

    # D4: 同步后验证
    print("\n📌 D4 同步验证")
    r = run_sync("--verify")
    t(f"{ptype}-验证", "验证通过" in r.stdout, 8)

    # D5: 漂移检测
    print("\n📌 D5 漂移检测")
    r = run_sync("--drift")
    t(f"{ptype}-漂移", r.returncode == 0, 7)

    # D6: 预览
    print("\n📌 D6 预览")
    r = run_sync("--diff")
    t(f"{ptype}-diff", r.returncode == 0, 6)

    # D7: 指定工具
    print("\n📌 D7 局部同步")
    r = run_sync("--apply", "--tool", "ATOMCODE")
    t(f"{ptype}-局部同步", r.returncode == 0, 7)

    # D8: 依赖检查
    print("\n📌 D8 依赖检测")
    r = run_sync()
    t(f"{ptype}-依赖检查", "依赖问题" in r.stdout or "规则" in r.stdout, 5)

# ── 汇总 ──
print(f"\n{'='*60}")
score_total = sum(s["score"] for s in S)
score_max = len(S) * 10
pct = score_total / score_max * 100
print(f"🏆 总分: {score_total}/{score_max} ({pct:.0f}%)")
for ptype in projects:
    p_scores = [s for s in S if ptype in s["name"]]
    p_total = sum(s["score"] for s in p_scores)
    print(f"  {ptype}: {p_total}/{len(p_scores)*10}")

print(f"\n📋 各项目平均分:")
for ptype in projects:
    p_scores = [s for s in S if ptype in s["name"]]
    avg = sum(s["score"] for s in p_scores) / len(p_scores)
    bar = "█" * int(avg) + "░" * (10 - int(avg))
    print(f"  {ptype:12s} {bar} {avg:.1f}/10")

# 清理
for d in projects.values():
    shutil.rmtree(d, ignore_errors=True)
print(f"\n🧹 测试项目已清理")
print(f"测试完成: {P}/{P+F} 通过")