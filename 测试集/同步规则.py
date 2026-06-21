#!/usr/bin/env python3
"""进化中心 → 各工具 自动分发同步脚本 v3
用法:
  python 同步规则.py                        # 查看分发矩阵
  python 同步规则.py --apply [项目目录]     # 同步到各工具配置
  python 同步规则.py --rollback             # 回滚上一次同步
  python 同步规则.py --git-status           # 查看版本历史
  python 同步规则.py --auto [项目目录]      # 自动模式（检测变更 + 条件规则 + 同步）
"""
import os, sys, shutil, datetime, json, subprocess, glob

HOME = os.path.expanduser("~")
EVO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKUP_DIR = os.path.join(EVO_DIR, "测试集", ".backups")
CHANGELOG = os.path.join(EVO_DIR, "测试集", ".changelog.json")
GIT_DIR = os.path.join(EVO_DIR, "测试集", ".git")
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

# 规则分发映射 —— 每条规则: 优先级+条件+目标
# 优先级: 1=最高(必须) 2=高 3=中 4=低 5=建议
RULES = {
    "测试先行": {
        "tools": ["ATOMCODE", "Hermes", "Claude Code(我)"],
        "desc": "写完代码必须跑测试验证",
        "priority": 1,
        "condition": None,
    },
    "自检验证": {
        "tools": ["ATOMCODE", "Hermes", "CodeBuddy", "Claude Code(我)"],
        "desc": "输出必须包含验证报告",
        "priority": 1,
        "condition": None,
    },
    "精简代码": {
        "tools": ["ATOMCODE", "Hermes"],
        "desc": "函数不超过50行",
        "priority": 3,
        "condition": None,
    },
    "中文输出": {
        "tools": ["Hermes", "CodeBuddy", "Qwen Code"],
        "desc": "回复用中文",
        "priority": 2,
        "condition": None,
    },
    "防编造": {
        "tools": ["Hermes"],
        "desc": "禁止编造命令输出",
        "priority": 1,
        "condition": None,
    },
    "UI质量检查": {
        "tools": ["CodeBuddy"],
        "desc": "HTML/CSS/图片质量检查",
        "priority": 2,
        "condition": None,
    },
    "测试清理": {
        "tools": ["Claude Code(我)", "ATOMCODE"],
        "desc": "测试产生的文件验证后必须删除",
        "priority": 3,
        "condition": None,
    },
}
    },
    "自检验证": {
        "tools": ["ATOMCODE", "Hermes", "CodeBuddy"],
        "desc": "输出必须包含验证报告",
        "condition": None,
    },
    "精简代码": {
        "tools": ["ATOMCODE", "Hermes"],
        "desc": "函数不超过50行",
        "condition": None,
    },
    "中文输出": {
        "tools": ["Hermes", "CodeBuddy"],
        "desc": "回复用中文",
        "condition": None,
    },
    "防编造": {
        "tools": ["Hermes"],
        "desc": "禁止编造命令输出",
        "condition": None,
    },
    "UI质量检查": {
        "tools": ["CodeBuddy"],
        "desc": "HTML/CSS/图片质量检查",
        "condition": None,
    },
}

# ── 条件规则（按项目类型启用的规则）──
CONDITIONAL_RULES = {
    "has_typescript": {
        "desc": "项目含TypeScript",
        "check": lambda cwd: any(glob.glob(os.path.join(cwd, 'tsconfig.json'))),
    },
    "has_python": {
        "desc": "项目含Python",
        "check": lambda cwd: any(glob.glob(os.path.join(cwd, '*.py'))) or any(glob.glob(os.path.join(cwd, 'requirements.txt'))),
    },
    "has_frontend": {
        "desc": "项目含前端代码",
        "check": lambda cwd: any(glob.glob(os.path.join(cwd, '*.html'))) or os.path.isdir(os.path.join(cwd, 'src')),
    },
}

def log(msg):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")

def backup_config(path):
    if not os.path.exists(path): return None
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    name = os.path.basename(path)
    backup = os.path.join(BACKUP_DIR, f"{name}.{ts}.bak")
    shutil.copy2(path, backup)
    return backup

def write_changelog(action, tool, rule, backup_path):
    log_data = []
    if os.path.exists(CHANGELOG):
        with open(CHANGELOG, 'r', encoding='utf-8') as f:
            try: log_data = json.load(f)
            except: log_data = []
    log_data.append({
        "time": datetime.datetime.now().isoformat(),
        "action": action, "tool": tool, "rule": rule, "backup": backup_path,
    })
    with open(CHANGELOG, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)

def init_git():
    """初始化备份目录的git版本控制"""
    if not os.path.exists(os.path.join(BACKUP_DIR, ".git")):
        try:
            subprocess.run(["git", "init"], cwd=BACKUP_DIR, capture_output=True, timeout=10)
            subprocess.run(["git", "config", "user.name", "进化中心"], cwd=BACKUP_DIR, capture_output=True, timeout=10)
            subprocess.run(["git", "config", "user.email", "evo@center"], cwd=BACKUP_DIR, capture_output=True, timeout=10)
            with open(os.path.join(BACKUP_DIR, ".gitignore"), 'w') as f:
                f.write("*.raw\n")
            log("  📦 git 版本控制已初始化")
            return True
        except Exception as e:
            log(f"  ⚠️ git init 失败: {e}")
            return False
    return True

def git_commit(message):
    """提交一次变更到git"""
    try:
        subprocess.run(["git", "add", "-A"], cwd=BACKUP_DIR, capture_output=True, timeout=10)
        result = subprocess.run(
            ["git", "diff-index", "--quiet", "HEAD"],
            cwd=BACKUP_DIR, capture_output=True, timeout=10
        )
        if result.returncode != 0:
            subprocess.run(["git", "commit", "-m", message], cwd=BACKUP_DIR, capture_output=True, timeout=10)
            return True
    except:
        pass
    return False

def check_conditions(cwd=None):
    """检查当前目录满足哪些条件规则"""
    if cwd is None:
        cwd = os.getcwd()
    active = []
    for key, info in CONDITIONAL_RULES.items():
        if info["check"](cwd):
            active.append(key)
    return active

def get_evo_hash():
    """计算进化中心文件的hash，用于检测变更"""
    import hashlib
    h = hashlib.md5()
    for f in sorted(glob.glob(os.path.join(EVO_DIR, "*.md"))):
        try:
            with open(f, 'rb') as fh:
                h.update(fh.read())
        except:
            pass
    return h.hexdigest()

def detect_conflicts():
    """检测规则冲突 — 基于关键词重叠的简单检测"""
    conflicts = []
    rule_texts = {r: info["desc"] for r, info in RULES.items()}
    keywords = {r: set(info["desc"]) for r, info in RULES.items()}
    for r1 in RULES:
        for r2 in RULES:
            if r1 >= r2: continue
            # 检查是否涉及相反操作
            pairs = [
                ("必须", "禁止"), ("要", "不要"), ("开启", "关闭"),
                ("加", "删"), ("大", "小"), ("多", "少"),
            ]
            d1, d2 = RULES[r1]["desc"], RULES[r2]["desc"]
            for a, b in pairs:
                if a in d1 and b in d2:
                    common_tools = set(RULES[r1]["tools"]) & set(RULES[r2]["tools"])
                    if common_tools:
                        conflicts.append((r1, r2, list(common_tools), f"'{a}' vs '{b}'"))
                        break
    return conflicts

def check_changed():
    """检测进化中心文件是否有变更"""
    current = get_evo_hash()
    if not os.path.exists(HASH_FILE):
        return True, current
    with open(HASH_FILE, 'r') as f:
        last = f.read().strip()
    return current != last, current

# ── 子命令实现 ──

def show_status():
    print("=" * 55)
    print("进化中心 · 分发系统 v3")
    print("=" * 55)
    for tool, path in TARGETS.items():
        exists = os.path.exists(path)
        size = os.path.getsize(path) if exists else 0
        print(f"  {'✅' if exists else '❌'} {tool:12s} ({size:>5} bytes)")

    print(f"\n📋 全量规则 ({len(RULES)} 条):")
    print(f"  {'规则':12s} ", end="")
    for t in TARGETS: print(f" {t:>10s}", end="")
    print()
    print(f"  {'-'*55}")
    for rule, info in RULES.items():
        print(f"  {rule:12s} ", end="")
        for t in TARGETS:
            print(f" {'✅' if t in info['tools'] else '-':>10s}", end="")
        print(f"  {info['desc']}")

    active = check_conditions()
    if active:
        print(f"\n📌 条件规则(当前目录生效):")
        for k in active:
            print(f"    ✅ {CONDITIONAL_RULES[k]['desc']}")

    covered = sum(1 for r in RULES.values() for t in r["tools"])
    total = len(RULES) * len(TARGETS)
    print(f"\n  覆盖率: {covered}/{total} ({covered/total*100:.0f}%)")

    git_log = os.path.join(BACKUP_DIR, ".git")
    if os.path.exists(git_log):
        try:
            cnt = subprocess.run(["git", "rev-list", "--count", "HEAD"], cwd=BACKUP_DIR,
                capture_output=True, text=True, timeout=5)
            print(f"  版本数: {cnt.stdout.strip()}")
        except: pass

    if os.path.exists(CHANGELOG):
        with open(CHANGELOG, 'r', encoding='utf-8') as f:
            try:
                logs = json.load(f)
                if logs:
                    last = logs[-1]
                    print(f"  最近: {last['time'][:19]} | {last['tool']} | {last['action']}")
            except: pass

    # 冲突检测
    conflicts = detect_conflicts()
    if conflicts:
        print(f"\n  ⚠️ 检测到 {len(conflicts)} 条规则冲突:")
        for r1, r2, tools, reason in conflicts:
            print(f"     🔥 {r1} ↔ {r2} (影响: {', '.join(tools)}) — {reason}")

    changed, _ = check_changed()
    if changed:
        print(f"\n  ⚠️ 检测到进化中心文件有变更 → 运行 --auto 同步")

    print(f"\n  选项:")
    print(f"    --apply         同步规则到各工具")
    print(f"    --auto          自动检测变更+条件+同步")
    print(f"    --rollback      回滚上次同步")
    print(f"    --git-status    查看版本历史")

def apply_rules():
    log("开始同步规则...")
    init_git()
    results = []
    active_conditions = check_conditions()
    log(f"  📌 活跃条件: {active_conditions if active_conditions else '无条件规则'}")

    for tool, path in TARGETS.items():
        if not os.path.exists(path):
            log(f"  ⚠️ {tool}: 配置文件不存在，跳过")
            continue

        backup = backup_config(path)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 找出该工具适用的规则（包含条件规则匹配）
        tool_rules = [r for r, info in RULES.items() if tool in info["tools"]]

        added = 0
        for rule in tool_rules:
            marker = f"<!-- 进化中心规则: {rule} -->"
            if marker not in content:
                rule_line = f"\n{marker}\n# 🔄 [进化中心] {rule}: {RULES[rule]['desc']}\n"
                content += rule_line
                added += 1

        # 条件规则：额外写入
        for cond in active_conditions:
            for rule in CONDITIONAL_RULES:
                if cond == rule:
                    cmarker = f"<!-- 进化中心条件: {rule} -->"
                    if cmarker not in content:
                        content += f"\n{cmarker}\n# 🔄 [进化中心] 条件规则: {CONDITIONAL_RULES[rule]['desc']}\n"
                        added += 1

        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

        results.append((tool, added))
        write_changelog("sync", tool, ", ".join(tool_rules), backup)
        git_commit(f"sync {tool}: {added} rules")

    # 保存当前hash
    _, h = check_changed()
    with open(HASH_FILE, 'w') as f:
        f.write(h)

    log("同步完成!")
    for tool, n in results:
        log(f"  {'✅' if n >= 0 else '❌'} {tool}: {'新增 ' + str(n) + ' 条规则' if n > 0 else '已是最新'}")

def auto_sync():
    """自动模式：检测变更→条件规则→同步"""
    log("🔄 自动模式启动")
    changed, current_hash = check_changed()

    if not changed:
        log("  进化中心无变更，跳过同步")
        return

    log("  ⚠️ 检测到进化中心文件变更")
    active_conds = check_conditions()
    log(f"  当前目录条件: {active_conds}")

    # 检查每个工具是否需要同步
    synced = 0
    for tool, path in TARGETS.items():
        if not os.path.exists(path):
            continue
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        tool_rules = [r for r, info in RULES.items() if tool in info["tools"]]
        missing = [r for r in tool_rules if f"<!-- 进化中心规则: {r} -->" not in content]

        if missing:
            log(f"  {tool}: 缺少 {len(missing)} 条规则 → 需要同步")
            synced += 1

    if synced > 0:
        log(f"  有 {synced} 个工具需要同步，执行 --apply")
        apply_rules()
    else:
        log("  所有工具已是最新")
        with open(HASH_FILE, 'w') as f:
            f.write(current_hash)

def git_status():
    """查看git版本历史"""
    if not os.path.exists(os.path.join(BACKUP_DIR, ".git")):
        log("版本控制未初始化，运行 --apply 后自动初始化")
        return
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "--graph", "-20"],
            cwd=BACKUP_DIR, capture_output=True, text=True, timeout=10
        )
        print(result.stdout if result.stdout else "暂无提交记录")
    except Exception as e:
        log(f"git log 失败: {e}")

def do_rollback():
    if not os.path.exists(CHANGELOG):
        log("没有可回滚的记录"); return
    with open(CHANGELOG, 'r', encoding='utf-8') as f:
        try: logs = json.load(f)
        except: logs = []
    if not logs:
        log("没有可回滚的记录"); return
    last = logs[-1]
    if not last.get("backup") or not os.path.exists(last["backup"]):
        log(f"备份文件不存在: {last.get('backup')}"); return
    tool = last["tool"]
    path = TARGETS.get(tool)
    if not path or not os.path.exists(path):
        log(f"目标文件不存在: {path}"); return
    shutil.copy2(last["backup"], path)
    write_changelog("rollback", tool, last.get("rule", ""), None)
    log(f"✅ {tool}: 已回滚到 {os.path.basename(last['backup'])}")

if __name__ == "__main__":
    if "--apply" in sys.argv:
        apply_rules()
    elif "--auto" in sys.argv:
        auto_sync()
    elif "--rollback" in sys.argv:
        do_rollback()
    elif "--git-status" in sys.argv:
        git_status()
    else:
        show_status()