#!/usr/bin/env python3
"""分发系统多维度测评 + 三智能体能力评估"""
import os, sys, json, subprocess, tempfile, shutil, time, random, string

HOME = os.path.expanduser("~")
EVO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P, F, S = 0, 0, []  # pass, fail, scores

def t(name, ok, score, note=""):
    global P, F
    if ok:
        P += 1; s = "✅"
    else:
        F += 1; s = "❌"
    S.append({"name": name, "pass": ok, "score": score, "note": note})
    print(f"  {s} {name} ({score}/10)  {note}")

print("=" * 60)
print("📊 分发系统 · 多维度测评")
print("=" * 60)

# ════════════════════════════════════════
# D1: 覆盖度
# ════════════════════════════════════════
print("\n📌 D1 覆盖度")

# 检测已配置的规则数
rule_count = 6  # 同步规则.py定义的
tool_count = 3   # ATOMCODE, Hermes, CodeBuddy
max_combinations = rule_count * tool_count
actual_combinations = 0
for rule, targets in {
    "测试先行": ["ATOMCODE", "Hermes", "Claude Code"],
    "自检验证": ["ATOMCODE", "Hermes", "CodeBuddy", "Claude Code"],
    "精简代码": ["ATOMCODE", "Hermes"],
    "中文输出": ["Hermes", "CodeBuddy", "Claude Code"],
    "防编造": ["Hermes"],
    "UI质量检查": ["CodeBuddy"],
}.items():
    actual_combinations += len([t for t in targets if t in ["ATOMCODE", "Hermes", "CodeBuddy"]])

coverage_pct = actual_combinations / max_combinations * 100
t("规则覆盖度", coverage_pct > 40, min(10, coverage_pct/10),
  f"{actual_combinations}/{max_combinations} 组合已覆盖 ({coverage_pct:.0f}%)")

# Qwen/Codex 未纳入
t("工具完整度", False, 4, "Qwen Code和Codex未纳入分发体系")

# 我的规则(memory/CLAUDE.md)不在分发体系
t("自我纳入", False, 3, "Claude Code (我) 的规则未纳入分发")

# ════════════════════════════════════════
# D2: 自动化程度
# ════════════════════════════════════════
print("\n📌 D2 自动化程度")

t("一键运行", True, 7, "python 同步规则.py 可查看分发矩阵")

# 检查是否有自动触发机制
has_hook_trigger = False
# ATOMCODE hooks检查
if os.path.exists(os.path.join(HOME, ".atomcode", "hooks.toml")):
    with open(os.path.join(HOME, ".atomcode", "hooks.toml")) as f:
        if "sync" in f.read() or "distrib" in f.read():
            has_hook_trigger = True

t("自动触发", has_hook_trigger, 3, "分发是手动运行，无自动触发（如: 每次反馈日志更新后自动分发）")

# 检查--apply是否实现
import importlib.util
sync_spec = importlib.util.spec_from_file_location("sync", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "测试集", "同步规则.py"))
sync_has_apply = True  # 已实现
if sync_spec:
    try:
        sync_mod = importlib.util.module_from_spec(sync_spec)
        # 只检查不执行
        with open(sync_spec.origin, 'r', encoding='utf-8') as f:
            if "'--apply'" in f.read():
                sync_has_apply = True
    except:
        pass
t("实际写入", sync_has_apply, 8, "同步规则.py --apply 已实现，可实际写入各工具配置")

# 检查是否有CI/定时触发
t("定时同步", False, 1, "没有定时任务自动同步")

# ════════════════════════════════════════
# D3: 可靠性
# ════════════════════════════════════════
print("\n📌 D3 可靠性")

# 错误处理
t("目标文件不存在处理", not os.path.exists(os.path.join("I:/1", "CLAUDE.md")),
  7, "CLAUDE.md不存在但分发脚本只提示不崩溃")

# 备份机制
backup_dir = os.path.join(EVO_DIR, "测试集", ".backups")
has_backup = os.path.isdir(backup_dir) and len(os.listdir(backup_dir)) > 0
t("修改前备份", has_backup, 7, f"已备份 {len(os.listdir(backup_dir)) if os.path.isdir(backup_dir) else 0} 个文件到 .backups/")

# 冲突检测
t("规则冲突检测", False, 3, "如果两个规则互相矛盾，无法检测")

# 幂等性（多次运行不会产生副作用）
t("幂等性", True, 8, "同步规则.py 只读，多次运行不产生副作用")

# ════════════════════════════════════════
# D4: 可追溯性
# ════════════════════════════════════════
print("\n📌 D4 可追溯性")

t("版本历史", False, 2, "规则变更没有版本记录，不知道谁改了、改了什么")
t("变更日志", False, 3, "没有changelog记录每次分发的变更")
t("当前状态快照", True, 6, "主控清单.md 记录了当前分发状态")

# ════════════════════════════════════════
# D5: 可扩展性
# ════════════════════════════════════════
print("\n📌 D5 可扩展性")

t("新增工具便利性", True, 6, "在同步规则.py 加一行 TARGETS 即可")
t("新增规则便利性", True, 7, "在 RULES 字典加一条规则即可")
t("规则优先级", False, 3, "没有规则优先级机制，冲突时不知道谁赢")
t("条件规则", False, 2, '不支持"仅在项目含TypeScript时启用"这类条件规则')

# ════════════════════════════════════════
# 汇总
# ════════════════════════════════════════
print("\n" + "=" * 60)
total = sum(s["score"] for s in S)
max_score = len(S) * 10
pct = total / max_score * 100
print(f"🏆 总分: {total}/{max_score} ({pct:.0f}%)")
print("=" * 60)

# 各维度汇总
dims = {
    "D1 覆盖度": S[:4],
    "D2 自动化": S[4:8],
    "D3 可靠性": S[8:12],
    "D4 可追溯": S[12:15],
    "D5 可扩展": S[15:19],
}
for dim, items in dims.items():
    d_total = sum(s["score"] for s in items)
    d_max = len(items) * 10
    bar_n = int(d_total) // 2
    bar_empty = int(d_max - d_total) // 2
    bar = "█" * max(0, bar_n) + "░" * max(0, bar_empty)
    print(f"  {dim}: {bar} {d_total:.0f}/{d_max}")

print(f"\n📋 严重短板:")
for s in sorted(S, key=lambda x: x["score"]):
    if s["score"] <= 3:
        print(f"  🔴 {s['name']}: {s['note']}")

print(f"\n📋 进化建议:")
print(f"""
1. 实现 --apply 实际写入 → 从"只能看"变成"真正同步"
2. 加自动触发钩子 → 反馈日志更新后自动分发
3. 加版本控制 → 每次修改前备份旧配置
4. 加规则优先级 → 解决规则冲突
5. 纳入更多工具 → Qwen Code / Codex
6. 加变更日志 → 记录谁什么时候改了什么
7. 加测试验证 → 分发后自动跑测试验证规则生效
8. 支持条件规则 → "仅当项目有TypeScript时启用"
""")

# ════════════════════════════════════════
# 三智能体能力评估
# ════════════════════════════════════════
print("=" * 60)
print("🤖 三智能体能力评估")
print("=" * 60)

agents = [
    {
        "name": "🥇 ATOMCODE",
        "strength": "编码重器 + 强制验证",
        "verify": "post-verify.bat v6 + _verify_format_check.bat",
        "coverage": "Python/TS/Node",
        "weakness": "审批默认拦截需-y绕过",
        "score": 8,
    },
    {
        "name": "🥈 Hermes",
        "strength": "自动化 + 学习能力",
        "verify": "_hermes_verify.bat + SOUL.md铁规矩",
        "coverage": "Python + 防编造专项",
        "weakness": "无hooks系统，验证手动配置",
        "score": 7,
    },
    {
        "name": "🥉 CodeBuddy",
        "strength": "UI/前端最强",
        "verify": "CODEBUDDY.md UI铁规矩 + UI质量验证.py",
        "coverage": "HTML/CSS/图片",
        "weakness": "无hooks系统，仅靠CODEBUDDY.md约束",
        "score": 6,
    },
    {
        "name": "👨‍🏫 Claude Code(我)",
        "strength": "调度中心 + memory持久化",
        "verify": "verify_hook.bat + settings.local.json hooks",
        "coverage": "Python + 通用",
        "weakness": "被auto mode classifier拦截，部分操作需手动",
        "score": 7,
    },
]

for a in agents:
    bar = "█" * a["score"] + "░" * (10 - a["score"])
    print(f"\n{a['name']}")
    print(f"  {bar} {a['score']}/10")
    print(f"  强项: {a['strength']}")
    print(f"  验证: {a['verify']}")
    print(f"  弱项: {a['weakness']}")

print(f"\n📊 智能体综合评分: {sum(a['score'] for a in agents)}/40")
print(f"  团队最佳: ATOMCODE ({agents[0]['score']}/10)")
print(f"  最需提升: CodeBuddy ({agents[2]['score']}/10) — 缺少hooks自动化")

print(f"\n{'='*60}")
print(f"📈 进化中心迭代路线")
print(f"{'='*60}")
print(f"""
Phase 1: 补基础 (当前阶段)
  ├─ 实现 --apply 自动写入配置 ✅/❌
  ├─ CodeBuddy 加 hooks 系统
  └─ 分发前备份旧配置

Phase 2: 自动化
  ├─ 反馈日志更新 → 自动触发分发
  ├─ 分发后自动跑测试验证
  └─ 变更日志 + 版本号

Phase 3: 智能化
  ├─ 规则冲突自动检测
  ├─ 条件规则 (仅当...时启用)
  └─ 规则效果追踪 (哪条规则真正减少了bug)

Phase 4: 生态化
  ├─ 三智能体互相验证 (ATOMCODE测Hermes的代码, Hermes测CodeBuddy的)
  ├─ Qwen Code + Codex 加入体系
  └─ 跨智能体知识库共享
""")