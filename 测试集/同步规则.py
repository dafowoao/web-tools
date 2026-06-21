#!/usr/bin/env python3
"""进化中心 · 分发系统 v4
用法:
  python 同步规则.py                             # 查看分发矩阵
  python 同步规则.py --apply [--tool NAME]       # 同步（可指定工具）
  python 同步规则.py --diff [--tool NAME]        # 预览变更
  python 同步规则.py --drift                     # 检测配置漂移
  python 同步规则.py --verify                    # 同步后验证
  python 同步规则.py --rollback                  # 回滚
  python 同步规则.py --git-status                # 版本历史
  python 同步规则.py --auto                      # 自动模式
  python 同步规则.py --drift --fix               # 自动修复漂移
  python 同步规则.py --rollout <规则名> <工具>    # A/B测试：只推到一个工具
"""
import os, sys, shutil, datetime, json, subprocess, glob, hashlib

HOME = os.path.expanduser("~")
EVO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKUP_DIR = os.path.join(EVO_DIR, "测试集", ".backups")
CHANGELOG = os.path.join(EVO_DIR, "测试集", ".changelog.json")
HASH_FILE = os.path.join(EVO_DIR, "测试集", ".last_hash.txt")
os.makedirs(BACKUP_DIR, exist_ok=True)

# 各工具配置路径
TARGETS = {
    "ATOMCODE": os.path.join(HOME, ".atomcode", "ATOMCODE.md"),
    "Hermes": os.path.join(HOME, "AppData", "Local", "hermes", "SOUL.md"),
    "CodeBuddy": os.path.join(HOME, ".codebuddy", "CODEBUDDY.md"),
    "Qwen Code": os.path.join(HOME, ".qwen", "output-language.md"),
    "Claude Code(我)": os.path.join("I:/1", "CLAUDE.md"),
}

# 规则定义：版本号 + 依赖 + 优先级
RULES = {
    "测试先行": {"tools": ["ATOMCODE","Hermes"], "desc": "写完代码必须跑测试验证",
        "priority": 1, "version": 2, "depends": [], "category": "编码"},
    "自检验证": {"tools": ["ATOMCODE","Hermes","CodeBuddy"], "desc": "输出必须包含验证报告",
        "priority": 1, "version": 2, "depends": ["测试先行"], "category": "编码"},
    "精简代码": {"tools": ["ATOMCODE","Hermes"], "desc": "函数不超过50行",
        "priority": 3, "version": 1, "depends": [], "category": "编码"},
    "中文输出": {"tools": ["Hermes","CodeBuddy","Qwen Code"], "desc": "回复用中文",
        "priority": 2, "version": 1, "depends": [], "category": "通用"},
    "防编造": {"tools": ["Hermes"], "desc": "禁止编造命令输出",
        "priority": 1, "version": 2, "depends": ["自检验证"], "category": "安全"},
    "UI质量检查": {"tools": ["CodeBuddy"], "desc": "HTML/CSS/图片质量检查",
        "priority": 2, "version": 1, "depends": [], "category": "UI"},
    "测试清理": {"tools": ["Claude Code(我)","ATOMCODE"], "desc": "测试文件验证后删除",
        "priority": 3, "version": 1, "depends": ["测试先行"], "category": "编码"},
}

CONDITIONAL_RULES = {
    "has_typescript": {"desc": "含TypeScript", "check": lambda cwd: any(glob.glob(os.path.join(cwd, 'tsconfig.json')))},
    "has_python": {"desc": "含Python", "check": lambda cwd: any(glob.glob(os.path.join(cwd, '*.py'))) or any(glob.glob(os.path.join(cwd, 'requirements.txt')))},
    "has_frontend": {"desc": "含前端", "check": lambda cwd: any(glob.glob(os.path.join(cwd, '*.html'))) or os.path.isdir(os.path.join(cwd, 'src'))},
}

DRIFT_FILE = os.path.join(EVO_DIR, "测试集", ".last_snapshot.json")

def log(msg): print(f"[{datetime.datetime.now():%H:%M:%S}] {msg}")

def backup_config(path):
    if not os.path.exists(path): return None
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = os.path.join(BACKUP_DIR, f"{os.path.basename(path)}.{ts}.bak")
    shutil.copy2(path, bak); return bak

def write_changelog(action, tool, rule, backup):
    d = []
    if os.path.exists(CHANGELOG):
        with open(CHANGELOG, 'r', encoding='utf-8') as f:
            try: d = json.load(f)
            except: pass
    d.append({"time": datetime.datetime.now().isoformat(), "action": action, "tool": tool, "rule": rule, "backup": backup})
    with open(CHANGELOG, 'w', encoding='utf-8') as f: json.dump(d, f, ensure_ascii=False, indent=2)

def get_tool_from_args():
    for i, a in enumerate(sys.argv):
        if a == '--tool' and i+1 < len(sys.argv):
            return sys.argv[i+1]
    return None

def filtered_targets():
    t = get_tool_from_args()
    if t:
        if t not in TARGETS: log(f"未知工具: {t}，可选: {', '.join(TARGETS.keys())}"); sys.exit(1)
        return {t: TARGETS[t]}
    return TARGETS

# ── 永久校验数据 ──
def save_snapshot():
    snap = {}
    for name, path in TARGETS.items():
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                snap[name] = hashlib.md5(f.read().encode()).hexdigest()
    with open(DRIFT_FILE, 'w', encoding='utf-8') as f:
        json.dump({"snapshot": snap, "time": datetime.datetime.now().isoformat()}, f)

def check_drift():
    if not os.path.exists(DRIFT_FILE): return []
    with open(DRIFT_FILE, 'r', encoding='utf-8') as f:
        saved = json.load(f).get("snapshot", {})
    drifted = []
    for name, path in TARGETS.items():
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                curr = hashlib.md5(f.read().encode()).hexdigest()
            if name in saved and curr != saved[name]:
                drifted.append(name)
    return drifted

def check_deps():
    """检查规则依赖是否满足"""
    missing = []
    for rule, info in RULES.items():
        for dep in info.get("depends", []):
            if dep not in RULES:
                missing.append(f"{rule} 依赖的 {dep} 不存在")
            # 检查依赖的工具覆盖
            for t in info["tools"]:
                if t not in RULES[dep]["tools"]:
                    missing.append(f"{rule}→{t}: 依赖的 {dep} 未覆盖 {t}")
    return missing

# ── 主命令 ──

def show_status():
    print("=" * 55)
    print("进化中心 · 分发系统 v4")
    print("=" * 55)
    for tool, path in TARGETS.items():
        exists = os.path.exists(path)
        size = os.path.getsize(path) if exists else 0
        print(f"  {'✅' if exists else '❌'} {tool:12s} ({size:,} bytes)")
    print(f"\n📋 全量规则 ({len(RULES)} 条):")
    for rule, info in sorted(RULES.items(), key=lambda x: x[1]["priority"]):
        tags = f"P{info['priority']} v{info['version']} {info['category']}"
        tools = " ".join(f"{'✅' if t in info['tools'] else '—'}" for t in TARGETS)
        print(f"  {rule:12s} {tools}  ({tags})")
    deps = check_deps()
    if deps:
        print(f"\n  ⚠️ 依赖问题: {len(deps)}")
        for d in deps[:3]: print(f"    {d}")
    drifted = check_drift()
    if drifted:
        print(f"\n  ⚠️ 配置漂移: {', '.join(drifted)} → 运行 --drift 查看")
    print(f"\n  选项:")
    print(f"    --apply [--tool NAME]    同步（可指定单工具）")
    print(f"    --diff  [--tool NAME]    预览变更")
    print(f"    --drift                  检测配置漂移")
    print(f"    --verify                 同步后验证")
    print(f"    --rollback               回滚")
    print(f"    --git-status             版本历史")
    print(f"    --auto                   自动模式")

def show_diff():
    """预览将要变更的内容"""
    tool_targets = filtered_targets()
    changes = []
    for tool, path in tool_targets.items():
        if not os.path.exists(path):
            changes.append((tool, "新增文件", 0))
            continue
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        tool_rules = [r for r, info in RULES.items() if tool in info["tools"]]
        for rule in tool_rules:
            marker = f"<!-- 进化中心规则: {rule} -->"
            if marker not in content:
                changes.append((tool, f"+{rule}", 1))
    if not changes:
        log("✅ 所有工具已是最新，无变更")
        return
    print(f"\n即将同步 {len(changes)} 项:")
    for tool, what, _ in changes:
        print(f"  📝 {tool:12s} {what}")

def apply_rules():
    log("开始同步规则...")
    tool_targets = filtered_targets()
    active_conditions = check_conditions()
    results = []
    for tool, path in tool_targets.items():
        if not os.path.exists(path):
            log(f"  ⚠️ {tool}: 配置不存在，跳过"); continue
        backup = backup_config(path)
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        tool_rules = [r for r, info in RULES.items() if tool in info["tools"]]
        added = 0
        for rule in tool_rules:
            marker = f"<!-- 进化中心规则: {rule} -->"
            if marker not in content:
                info = RULES[rule]
                content += f"\n{marker}\n# 🔄 [进化中心] {rule}: {info['desc']} (v{info['version']} P{info['priority']})\n"
                added += 1
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        results.append((tool, added))
        write_changelog("sync", tool, ", ".join(tool_rules), backup)
    save_snapshot()
    log("同步完成!")
    for tool, n in results:
        log(f"  {'✅' if n >= 0 else '❌'} {tool}: {'新增' if n else '已是最新'} ({n})")

def verify_sync():
    """同步后验证：检查规则是否真的写入了"""
    log("验证同步结果...")
    all_ok = True
    for tool, path in TARGETS.items():
        if not os.path.exists(path):
            log(f"  ⚠️ {tool}: 不存在"); continue
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        tool_rules = [r for r, info in RULES.items() if tool in info["tools"]]
        missing = [r for r in tool_rules if f"<!-- 进化中心规则: {r} -->" not in content]
        if missing:
            log(f"  ❌ {tool}: 缺少规则 {missing}")
            all_ok = False
        else:
            log(f"  ✅ {tool}: {len(tool_rules)}/{len(tool_rules)} 规则就位")
    if all_ok: log("✅ 验证通过")
    return all_ok

def check_drift_cmd():
    """检测配置漂移"""
    drifted = check_drift()
    if not drifted:
        log("✅ 无配置漂移，所有工具与上次同步一致")
        return
    log(f"⚠️ 检测到 {len(drifted)} 个工具被手动修改:")
    for name in drifted:
        path = TARGETS[name]
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        # 找出非进化中心的修改行
        manual = [l.strip() for l in lines if '进化中心' not in l and l.strip() and not l.startswith('#')]
        log(f"  {name}: {len(manual)} 行可能是手动修改")
    log("运行 --apply 将覆盖漂移，运行 --diff 预览")

def auto_sync():
    log("🔄 自动模式")
    changed, cur_hash = check_changed()
    if not changed: log("  无变更，跳过"); return
    log("  ⚠️ 检测到变更")
    apply_rules()
    verify_sync()

# ── 复用函数 ──

def check_conditions(cwd=None):
    if cwd is None: cwd = os.getcwd()
    return [k for k, v in CONDITIONAL_RULES.items() if v["check"](cwd)]

def get_evo_hash():
    h = hashlib.md5()
    for f in sorted(glob.glob(os.path.join(EVO_DIR, "*.md"))):
        try:
            with open(f, 'rb') as fh: h.update(fh.read())
        except: pass
    return h.hexdigest()

def check_changed():
    cur = get_evo_hash()
    if not os.path.exists(HASH_FILE): return True, cur
    with open(HASH_FILE) as f: last = f.read().strip()
    return cur != last, cur

def detect_conflicts():
    conflicts = []
    for r1 in RULES:
        for r2 in RULES:
            if r1 >= r2: continue
            pairs = [("必须","禁止"),("要","不要"),("加","删")]
            for a,b in pairs:
                if a in RULES[r1]["desc"] and b in RULES[r2]["desc"]:
                    shared = set(RULES[r1]["tools"]) & set(RULES[r2]["tools"])
                    if shared: conflicts.append((r1,r2,list(shared)))
    return conflicts

def do_rollback():
    if not os.path.exists(CHANGELOG): log("无记录"); return
    with open(CHANGELOG, encoding='utf-8') as f:
        try: logs = json.load(f)
        except: logs = []
    if not logs: log("无记录"); return
    last = logs[-1]
    if not last.get("backup") or not os.path.exists(last["backup"]): log("备份不存在"); return
    t, p = last["tool"], TARGETS.get(last["tool"])
    if not p or not os.path.exists(p): log(f"目标不存在: {p}"); return
    shutil.copy2(last["backup"], p)
    write_changelog("rollback", t, last.get("rule",""), None)
    log(f"✅ {t} 已回滚")

def git_status():
    gd = os.path.join(BACKUP_DIR, ".git")
    if not os.path.exists(gd): log("未初始化"); return
    r = subprocess.run(["git","log","--oneline","--graph","-15"], cwd=BACKUP_DIR, capture_output=True, text=True, timeout=10)
    print(r.stdout or "无提交")

if __name__ == "__main__":
    if "--apply" in sys.argv: apply_rules()
    elif "--diff" in sys.argv: show_diff()
    elif "--drift" in sys.argv:
        if "--fix" in sys.argv: auto_fix_drift()
        else: check_drift_cmd()
    elif "--verify" in sys.argv: verify_sync()
    elif "--auto" in sys.argv: auto_sync()
    elif "--rollback" in sys.argv: do_rollback()
    elif "--rollout" in sys.argv:
        if len(sys.argv) >= 4: rollout_rule(sys.argv[2], sys.argv[3])
        else: log("用法: --rollout <规则名> <工具>")
    elif "--git-status" in sys.argv: git_status()
    else: show_status()


def auto_fix_drift():
    """检测漂移并自动修复"""
    drifted = check_drift()
    if not drifted:
        log("✅ 无配置漂移"); return
    log(f"⚠️ 发现 {len(drifted)} 个工具漂移，自动修复...")
    for name in drifted:
        backup = backup_config(TARGETS[name])
        # 重新同步该工具
        apply_rules(tool_only=name)
        write_changelog("auto-fix", name, "漂移修复", backup)
        log(f"  ✅ {name} 已修复")

def rollout_rule(rule_name, tool_name):
    """A/B测试：将一条规则只推到一个工具"""
    if rule_name not in RULES:
        log(f"❌ 规则 {rule_name} 不存在"); return
    if tool_name not in TARGETS:
        log(f"❌ 工具 {tool_name} 不存在"); return
    path = TARGETS[tool_name]
    if not os.path.exists(path):
        log(f"⚠️ {tool_name} 配置不存在"); return
    backup = backup_config(path)
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    marker = f"<!-- 进化中心规则: {rule_name} -->"
    if marker in content:
        log(f"⚠️ {tool_name} 已有此规则"); return
    info = RULES[rule_name]
    content += f"\n{marker}\n# 🔄 [进化中心·试用] {rule_name}: {info['desc']} (v{info['version']})\n"
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    write_changelog("rollout", tool_name, rule_name, backup)
    log(f"✅ {rule_name} → {tool_name} 已部署（试用）")
