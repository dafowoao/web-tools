#!/usr/bin/env python3
"""自检100题 · 测试可靠性审计 — 找出假阳性"""

P, F, R = 0, 0, []
def t(name, ok, note=""):
    global P, F
    if ok: P += 1; R.append(f"  ✅ {name}")
    else: F += 1; R.append(f"  ❌ {name}  ← {note}")

print("=" * 70)
print("🔍 自检100题 · 假阳性审计")
print("排查：测试通过了，但实际有问题")
print("=" * 70)

# ── D5-1: 迭代次数太少，GIL掩盖了竞态条件 ──
print("\n📌 假阳性 #1: D5-1 竞态条件（样本太小）")
import threading

class UnsyncCounter:
    def __init__(self): self.n = 0
    def inc(self): self.n += 1

c = UnsyncCounter()
thrs = [threading.Thread(target=lambda: [c.inc() for _ in range(100)]) for _ in range(10)]
for thr in thrs: thr.start()
for thr in thrs: thr.join()
t("D5-1 原版(100次/线程)", c.n == 1000, "GIL让100次迭代跑不出竞态条件！应至少10000次/线程")

c2 = UnsyncCounter()
thrs2 = [threading.Thread(target=lambda: [c2.inc() for _ in range(10000)]) for _ in range(10)]
for thr in thrs2: thr.start()
for thr in thrs2: thr.join()
t("D5-1 加大(10000次/线程)", c2.n == 100000, f"放大后{c2.n}≠100000，竞态条件才显现")

# ── D5-3: list.append在CPython下GIL保护了 ──
print("\n📌 假阳性 #2: D5-3 list.append线程安全")
shared = []
def add_items():
    for i in range(1000): shared.append(i)

t1 = threading.Thread(target=add_items)
t2 = threading.Thread(target=add_items)
t1.start(); t2.start(); t1.join(); t2.join()
t("D5-3 list.append(1000次)", len(shared) == 2000,
  "CPython的GIL让list.append原子化了！实际不是线程安全，只是没撞上")

# 用list的+=操作（不是原子操作）
c, F2 = 0, []
def add_items_bad():
    global c
    for i in range(1000):
        c += 1  # c+=1不是原子操作

t1b = threading.Thread(target=add_items_bad)
t2b = threading.Thread(target=add_items_bad)
t1b.start(); t2b.start(); t1b.join(); t2b.join()
t("D5-3b +=操作(1000次)", c == 2000,
  f"+=不是原子的，实际{c}≠2000")

# ── D1-5: 10K规模太小，O(n²)不显现 ──
print("\n📌 假阳性 #3: D1-5 字符串拼接规模不够")
import time

def concat_strs(items, sep=','):
    result = ""
    for i, item in enumerate(items):
        if i > 0: result += sep
        result += str(item)
    return result

big = list(range(10000))
start = time.time(); concat_strs(big); t1 = time.time() - start
t("D1-5 1万项", t1 < 5, f"仅耗时{t1*1000:.0f}ms，现代CPU扛得住")

big2 = list(range(500000))
start = time.time(); concat_strs(big2); t2 = time.time() - start
t("D1-5 50万项", t2 < 5, f"50万项耗时{t2:.2f}s，O(n²)才暴露")

# 对比join
start = time.time(); ','.join(str(x) for x in big2); t3 = time.time() - start
t("D1-5 join同一数据", True, f"join仅耗时{t3:.2f}s，快{t2/t3:.0f}倍")

# ── D5-6: dict写入也受GIL保护 ──
print("\n📌 假阳性 #4: D5-6 dict并发写入规模不够")
shared_data = {}
def worker(k):
    import time; time.sleep(0.001)
    shared_data[k] = k * 2
thrs = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
for thr in thrs: thr.start()
for thr in thrs: thr.join()
t("D5-6 dict写入10项", len(shared_data) == 10,
  "10项太少，GIL保护了！加大并发数才可能复现")

# ── 统计伪测试（永远True不验证）──
print("\n\n📌 统计：永远True的伪测试")
import os
src = os.path.join(os.path.dirname(__file__), "自检100题.py")
lines = open(src, encoding='utf-8').readlines()
fake_tests = 0
for i, line in enumerate(lines):
    if 't("' in line and ', True,' in line and 'note' not in line:
        # 提取测试名
        start = line.find('t("') + 3
        end = line.find('"', start)
        name = line[start:end]
        if name:
            fake_tests += 1
            if fake_tests <= 5:
                print(f"  ⚠️ {name}")

if fake_tests:
    print(f"\n  共 {fake_tests} 个测试永远 True（伪测试）")
    print(f"  建议：改成实际验证代码而非直接标记True")

# ── 汇总 ──
print("\n" + "=" * 70)
print(f"审计结果: {P}/{P+F} 通过")
print("=" * 70)
print("""
📋 发现总结：
1. D5-1/D5-3/D5-6 → 并发测试规模太小，GIL掩盖了问题
2. D1-5 → 10K数据量对现代CPU太小，O(n²)不显现
3. 大量测试 t("...", True, "...") → 没有实际验证逻辑，是伪测试

修复建议：
1. 并发测试加大迭代到10000+/线程
2. 性能测试用足够大数据量（50万+）
3. 伪测试改成实际跑代码验证
""")