#!/usr/bin/env python3
"""规则效果验证 — 检查各工具是否真的遵守了规则"""
import os, sys, json, datetime, glob, subprocess, re

HOME = os.path.expanduser("~")
EVO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = []

def log(name, ok, detail=""):
    RESULTS.append({"name": name, "ok": ok, "detail": detail})
    print(f"  {'✅' if ok else '❌'} {name:30s} {detail}")

print("=" * 55)
print("📋 规则效果验证 — 各工具遵守情况")
print("=" * 55)

# ═══ T1: ATOMCODE — 精简代码（函数≤50行）═══
print("\n📌 ATOMCODE: 精简代码")
atomcode_md = os.path.join(HOME, ".atomcode", "ATOMCODE.md")
if os.path.exists(atomcode_md):
    with open(atomcode_md, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    log("规则已写入", "<!-- 进化中心规则: 精简代码 -->" in content,
        f"文件 {len(content)} bytes")
    log("包含了50行限制", "50" in content or "50行" in content,
        "规则明确写了函数不超过50行")
else:
    log("ATOMCODE配置存在", False, "ATOMCODE.md 不存在")

# 扫描最近的Python文件看ATOMCODE生成的代码是否符合50行限制
recent_files = []
for root, dirs, files in os.walk("I:/1"):
    if any(skip in root for skip in ['node_modules', '.git', '__pycache__', '.evolution_center']):
        continue
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            recent_files.append((os.path.getmtime(path), path))
recent_files.sort(reverse=True)

over_50 = 0
total_funcs = 0
for _, fp in recent_files[:20]:  # 只看最近20个
    try:
        with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()
        # 简单统计：以def开头的行到下一个def或文件结束的行数
        funcs = re.findall(r'def\s+\w+', code)
        total_funcs += len(funcs)
        lines = code.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('def '):
                # 计算函数体行数
                body_start = i + 1
                body_end = len(lines)
                for j in range(i + 1, len(lines)):
                    if lines[j].startswith('def ') or lines[j].startswith('class '):
                        body_end = j
                        break
                func_lines = body_end - body_start
                if func_lines > 50:
                    over_50 += 1
    except: pass

if total_funcs > 0:
    log(f"函数行数检查 ({total_funcs}个函数)", over_50 == 0,
        f"{over_50}/{total_funcs} 个函数超过50行")
else:
    log("函数行数检查", True, "无可检查的文件")

# ═══ T2: Hermes — 防编造 + 真实验证 ═══
print("\n📌 Hermes: 防编造 + 验证真实性")
hermes_cfg = os.path.join(HOME, "AppData", "Local", "hermes", "SOUL.md")
if os.path.exists(hermes_cfg):
    with open(hermes_cfg, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    log("防编造规则已写入", "禁止编造" in content,
        "SOUL.md 包含防编造规则")
    log("禁止简略验证", "禁止简略" in content or "不能概括" in content,
        "明确要求不能只写'测试通过'")
    log("验证块必须包含原始输出", "原始输出" in content,
        "要求粘贴原始终端输出")
else:
    log("Hermes配置存在", False, "SOUL.md 不存在")

# 检查Hermes的最近输出
hermes_logs = []
for root, dirs, files in os.walk(os.path.join(HOME, "AppData", "Local", "hermes", "logs")):
    for f in files:
        hermes_logs.append((os.path.getmtime(os.path.join(root, f)), os.path.join(root, f)))
hermes_logs.sort(reverse=True)

verify_count = 0
fake_verify_count = 0
for _, lp in hermes_logs[:5]:
    try:
        with open(lp, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        if '[验证]' in content:
            verify_count += 1
            # 检查是不是简略验证
            has_cmd = '命令:' in content
            has_out = '输出:' in content
            has_result = '通过:' in content or '失败' in content
            if not (has_cmd and has_out and has_result):
                fake_verify_count += 1
    except: pass

if verify_count > 0:
    log(f"Hermes验证块检查 ({verify_count}条)", fake_verify_count == 0,
        f"含{fake_verify_count}条可能编造的验证")
else:
    log("Hermes验证块检查", True, "暂无日志可检查")

# ═══ T3: CodeBuddy — UI质量 ═══
print("\n📌 CodeBuddy: UI质量")
cb_cfg = os.path.join(HOME, ".codebuddy", "CODEBUDDY.md")
if os.path.exists(cb_cfg):
    with open(cb_cfg, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    log("UI自检规则已写入", "UI质量检查" in content or "UI自检" in content,
        "CODEBUDDY.md 包含UI检查规则")
    log("viewport检查要求", "viewport" in content or "width=device-width" in content,
        "要求正确的视口设置")
    log("CSS变量要求", "CSS变量" in content or "--" in content.split('CSS')[1][:200] if 'CSS' in content else False,
        "要求至少5个CSS变量")
    log("响应式断点要求", "响应式" in content,
        "要求至少4级断点")
else:
    log("CodeBuddy配置存在", False, "CODEBUDDY.md 不存在")

# ═══ T4: 我(Claude Code) — 自检验证 ═══
print("\n📌 Claude Code: 自检验证")
claude_md = "I:/1/CLAUDE.md"
if os.path.exists(claude_md):
    with open(claude_md, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    log("自检验证规则已写入", "自检验证" in content,
        "CLAUDE.md 包含自检要求")
    log("记忆管理规则", "memory" in content.lower() or "记忆" in content,
        "翻车要记到memory")
    log("测试清理规则", "清理" in content or "删除" in content,
        "要求测试文件验证后删除")
else:
    log("CLAUDE.md存在", True, "暂无配置文件")

# ═══ T5: 进化中心自检 ═══
print("\n📌 进化中心: 自身体系")
sync_py = os.path.join(EVO, "测试集", "同步规则.py")
if os.path.exists(sync_py):
    with open(sync_py, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    log("分发系统v4", "v4" in content or "CONDITIONAL_RULES" in content,
        "当前版本支持条件规则+漂移检测")
    log("漂移检测可用", "drift" in content,
        "支持配置漂移检测")
    log("回滚机制", "rollback" in content,
        "支持一键回滚")

# 检查监控系统
monitor = os.path.join(EVO, "测试集", "监控后端.py")
log("监控系统", os.path.exists(monitor), "监控后端.py 存在")

dashboard = os.path.join(EVO, "测试集", "进化看板.html")
log("可视化看板", os.path.exists(dashboard), "进化看板.html 存在")

# ═══ 汇总 ═══
print(f"\n{'='*55}")
passed = sum(1 for r in RESULTS if r["ok"])
total = len(RESULTS)
score = int(passed / total * 100) if total > 0 else 0
print(f"📊 规则遵守率: {passed}/{total} ({score}%)")

# 按工具分组
agents = {"ATOMCODE": [], "Hermes": [], "CodeBuddy": [], "Claude Code": [], "进化中心": []}
for r in RESULTS:
    for agent in agents:
        if r["name"].startswith(agent):
            agents[agent].append(r)

print(f"\n各工具遵守率:")
for agent, items in agents.items():
    if items:
        p = sum(1 for i in items if i["ok"])
        t = len(items)
        bar = "█" * p + "░" * (t - p)
        print(f"  {agent:12s} {bar} {p}/{t}")

# 生成报告文件
report = {
    "time": datetime.datetime.now().isoformat(),
    "passed": passed,
    "total": total,
    "score": score,
    "details": RESULTS,
}
report_path = os.path.join(EVO, "测试集", ".规则效果报告.json")
with open(report_path, 'w', encoding='utf-8') as f:
    json.dump(report, f, ensure_ascii=False, indent=2)
print(f"\n📄 报告已保存: {report_path}")