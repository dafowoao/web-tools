#!/usr/bin/env python3
"""错误日志沉淀 — 翻车自动记入 memory"""
import os, sys, json, datetime

MEMORY_DIR = os.path.expanduser("~/.claude/projects/I--1/memory")
FEEDBACK_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "反馈日志.md")

def save_error(category, problem, root_cause, fix, prevention):
    """记一条翻车记录到 memory"""
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    slug = problem.lower().replace(" ", "-")[:30]

    # 写 memory 文件
    mem_file = os.path.join(MEMORY_DIR, f"error-{slug}.md")
    with open(mem_file, 'w', encoding='utf-8') as f:
        f.write(f"""---
name: error-{slug}
description: {problem[:60]}
metadata:
  type: feedback
---

# {problem}

**时间:** {ts}
**分类:** {category}

**问题:** {problem}
**根因:** {root_cause}
**修复:** {fix}
**预防:** {prevention}
""")

    # 追加到反馈日志
    if os.path.exists(FEEDBACK_LOG):
        with open(FEEDBACK_LOG, 'a', encoding='utf-8') as f:
            f.write(f"\n## {ts}\n### {problem}\n- **分类**: {category}\n- **根因**: {root_cause}\n- **修复**: {fix}\n- **预防**: {prevention}\n- **状态**: 已记录 ✅\n")

    print(f"✅ 错误已记录: {problem[:40]}")
    print(f"   memory: {mem_file}")
    print(f"   日志: {FEEDBACK_LOG}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python 错误日志沉淀.py <分类> <问题描述> [根因] [修复] [预防]")
        sys.exit(1)

    category = sys.argv[1]
    problem = sys.argv[2]
    root_cause = sys.argv[3] if len(sys.argv) > 3 else ""
    fix = sys.argv[4] if len(sys.argv) > 4 else ""
    prevention = sys.argv[5] if len(sys.argv) > 5 else ""

    save_error(category, problem, root_cause, fix, prevention)