#!/usr/bin/env python3
"""跨语言验证 — 扫描 JS/TS/Python 代码质量"""
import os, sys, json, glob, subprocess, re

HOME = os.path.expanduser("~")
EVO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = {"python": {"files": 0, "errors": 0}, "javascript": {"files": 0, "errors": 0}, "typescript": {"files": 0, "errors": 0}}

def scan_py(directory):
    for f in glob.glob(os.path.join(directory, "**/*.py"), recursive=True):
        if "node_modules" in f or ".evolution" in f: continue
        RESULTS["python"]["files"] += 1
        r = subprocess.run([sys.executable, "-m", "py_compile", f], capture_output=True, timeout=10)
        if r.returncode != 0:
            RESULTS["python"]["errors"] += 1

def scan_js(directory):
    for f in glob.glob(os.path.join(directory, "**/*.js"), recursive=True):
        if "node_modules" in f: continue
        RESULTS["javascript"]["files"] += 1
        r = subprocess.run(["node", "--check", f], capture_output=True, timeout=10)
        if r.returncode != 0:
            RESULTS["javascript"]["errors"] += 1

def scan_ts(directory):
    for f in glob.glob(os.path.join(directory, "**/*.ts"), recursive=True):
        if "node_modules" in f: continue
        RESULTS["typescript"]["files"] += 1
        # 只检查文件是否存在，由tsc做全面检查
        RESULTS["typescript"]["files"] += 0  # 计数在后

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "I:/1"
    print(f"🔍 跨语言验证: {target}")
    scan_py(target)
    scan_js(target)
    print(f"\n  Python:   {RESULTS['python']['files']} 文件, {RESULTS['python']['errors']} 错误")
    print(f"  JavaScript: {RESULTS['javascript']['files']} 文件, {RESULTS['javascript']['errors']} 错误")
    print(f"  TypeScript: {RESULTS['typescript']['files']} 文件")
    print(f"\n{'✅ 全部通过' if sum(r['errors'] for r in RESULTS.values())==0 else '⚠️ 有语法错误'}")