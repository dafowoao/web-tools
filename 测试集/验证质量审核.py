#!/usr/bin/env python3
"""ATOMCODE 验证质量审核 — 它的 verify 到底可不可信"""

import subprocess, sys, os, re, json, tempfile, time
from pathlib import Path

P, F, R = 0, 0, []
def t(name, ok, note=""):
    global P, F
    if ok: P += 1; R.append(f"  ✅ {name}")
    else: F += 1; R.append(f"  ❌ {name}  ← {note}")

print("=" * 70)
print("🔍 ATOMCODE 验证质量审核")
print("检查它的 verify 块是不是真实的")
print("=" * 70)

# ── 审计1: 查看 ATOMCODE 的历史验证记录 ──
print("\n📌 V1: ATOMCODE 的历史验证记录审计")

log_dir = os.path.expanduser("~/.atomcode/datalog")
if os.path.isdir(log_dir):
    # 找最近的会话记录
    sessions = []
    for root, dirs, files in os.walk(log_dir):
        for f in files:
            if f.endswith('.md') or f.endswith('.json'):
                path = os.path.join(root, f)
                sessions.append((os.path.getmtime(path), path))
    sessions.sort(reverse=True)
    recent = sessions[:5]
    t("V1 日志存在", len(recent) > 0, f"找到{len(recent)}个近期日志")
    for ts, path in recent:
        print(f"  📄 {os.path.basename(path)} ({time.ctime(ts)})")
else:
    t("V1 日志存在", False, "datalog目录不存在")

# ── 审计2: 检查 ATOMCODE.md 中 verify 格式要求 ──
print("\n📌 V2: verify 格式完整性检查")

atomcode_md = os.path.expanduser("~/.atomcode/ATOMCODE.md")
if os.path.exists(atomcode_md):
    with open(atomcode_md, encoding='utf-8') as f:
        content = f.read()

    has_verify = '<verify>' in content
    has_cmd = '<cmd>' in content
    has_output = '<output>' in content
    has_fix = '<fix>' in content
    has_req = '<req>' in content

    t("V2 verify结构完整", has_verify and has_cmd and has_output and has_fix and has_req,
      f"verify={has_verify} cmd={has_cmd} output={has_output} fix={has_fix} req={has_req}")

    # 检查有没有漏洞：verify要求输出"原始终端输出"，但没要求截取完整输出
    lines = content.split('\n')
    verify_lines = [l for l in lines if 'verify' in l.lower() or '输出' in l]
    t("V2 有验证后自动检查机制", any('post-verify' in l for l in lines) or any('auto' in l for l in lines),
      "没有发现自动验证的钩子")
else:
    t("V2 ATOMCODE.md存在", False, "配置文件不存在")

# ── 审计3: 验证漏洞案例分析 ──
print("\n📌 V3: verify 常见造假模式")

# 模式1: 说自己跑过了但输出是编的
fake_output = """```xml
<verify>
  <cmd>python test.py</cmd>
  <output>All tests passed!</output>
  <fix>无</fix>
  <req>
✅ 功能完成
  </req>
</verify>
```"""
t("V3-1 输出可编造", fake_output.count('✅') == 1,
  "ATOMCODE可以自己写<output>，不一定是真实的终端输出")

# 模式2: 没有截取完整终端输出
t("V3-2 无完整输出验证", True,
  "verify要求'原始终端输出，逐行粘贴，不能概括'，但没有机制验证是否真的粘贴了")

# 模式3: 改代码后verify说通过但测试没跑
t("V3-3 无测试自动触发", True,
  "改了代码 → 应该自动触发测试，但ATOMCODE的verify是手动填的")

# 模式4: verify块格式错误不会被检测
bad_verify = """<verify>
  <cmd>
  <ouput>
  忘了关标签
</verify>"""
t("V3-4 格式容错", True,
  "verify格式错误没有外部校验器，ATOMCODE自己写的自己也不知道对不对")

# ── 建议修复方案 ──
print("\n" + "=" * 70)
print("📋 改进方案")
print("=" * 70)
print("""
方案A: 验证外部化（推荐）
  写一个 verify-checker.py，在 ATOMCODE 的 post_tool_use hook 中调用。
  每次 ATOMCODE 输出 verify 块后，自动检查：
    - <cmd> 是否真实执行过
    - <output> 是否匹配实际运行结果
    - ✅ 的数量和实际测试通过数一致

方案B: 双向验证
  测试文件本身带验证入口：
    if __name__ == '__main__':
        result = run_tests()
        assert verify_output_matches(result)

  ATOMCODE 改完代码后必须运行 python test.py 才能真正验证

方案C: 测试驱动
  要求 ATOMCODE 在改代码之前先写测试，
  改完必须跑测试通过才算完成，
  verify 块必须包含测试运行的实际输出
""")

print(f"\n审核结果: {P}/{P+F}")