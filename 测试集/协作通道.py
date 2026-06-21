#!/usr/bin/env python3
"""三徒协作通道 — 师父分发任务到各徒弟"""
import subprocess, sys, os, json, datetime

HOME = os.path.expanduser("~")
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".协作日志.json")

def log_task(agent, task, result, status):
    data = []
    if os.path.exists(LOG):
        with open(LOG, 'r', encoding='utf-8') as f:
            try: data = json.load(f)
            except: pass
    data.append({
        "time": datetime.datetime.now().isoformat(),
        "agent": agent, "task": task[:50],
        "result": str(result)[:100], "status": status,
    })
    with open(LOG, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def run_atomcode(task, cwd="I:/1"):
    print(f"[ATOMCODE] 下发任务...")
    r = subprocess.run(
        [os.path.join(os.environ.get('LOCALAPPDATA', 'C:/Users/2026/AppData/Local'), 'AtomCode', 'atomcode.exe'),
         '-C', cwd, '-p', task, '-y'],
        capture_output=True, text=True, timeout=300
    )
    out = r.stdout[-300:] if r.stdout else r.stderr[-300:]
    status = "✅" if r.returncode == 0 else "❌"
    log_task("ATOMCODE", task, out, status)
    print(f"  {status} exit={r.returncode}")
    return out, r.returncode

def run_hermes(task):
    print(f"[Hermes] 下发任务...")
    r = subprocess.run(
        [sys.executable, os.path.join(HOME, 'bin', 'hermes'),
         'chat', '-q', task, '--accept-hooks', '--yolo'],
        capture_output=True, text=True, timeout=300
    )
    out = r.stdout[-300:] if r.stdout else r.stderr[-300:]
    status = "✅"
    log_task("Hermes", task, out, status)
    print(f"  ✅ done")
    return out, 0

def run_codebuddy(task):
    print(f"[CodeBuddy] 下发任务...")
    r = subprocess.run(
        ['cmd.exe', '/c', 'codebuddy', '-p', '-y', task],
        capture_output=True, text=True, timeout=300
    )
    out = r.stdout[-300:] if r.stdout else r.stderr[-300:]
    status = "✅" if r.returncode == 0 else "❌"
    log_task("CodeBuddy", task, out, status)
    print(f"  {status} exit={r.returncode}")
    return out, r.returncode

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python 协作通道.py <徒弟> <任务描述>")
        print("  徒弟: atomcode / hermes / codebuddy / all")
        sys.exit(1)

    agent = sys.argv[1].lower()
    task = " ".join(sys.argv[2:])

    agents = {
        "atomcode": run_atomcode,
        "hermes": run_hermes,
        "codebuddy": run_codebuddy,
    }

    if agent == "all":
        results = {}
        for name, fn in agents.items():
            out, code = fn(task)
            results[name] = {"exit": code, "output": out[-100:]}
        print(f"\n📊 全部完成: {json.dumps(results, ensure_ascii=False, indent=2)}")
    elif agent in agents:
        agents[agent](task)
    else:
        print(f"未知徒弟: {agent}，可选: atomcode/hermes/codebuddy/all")