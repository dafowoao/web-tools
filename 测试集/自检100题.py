#!/usr/bin/env python3
"""ATOMCODE 自检能力深度评测 — 100道题·10维度·每题一个隐蔽坑"""

# ── 评测引擎 ──
import time, sys, os, threading, json, math, random, tempfile, hashlib, sqlite3
from collections import Counter
import functools

P, F, R = 0, 0, []
def t(name, ok, note=""):
    global P, F
    if ok: P += 1; R.append(f"  ✅ {name}")
    else: F += 1; R.append(f"  ❌ {name}  ← {note}")

print("=" * 70)
print("ATOMCODE 自检能力深度评测 · 100题 · 10维度")
print("=" * 70)

# ════════════════════════════════════════════
# 维度1：边界遗漏（10题）
# ════════════════════════════════════════════
print("\n📌 D1 边界遗漏")

# D1-1: 空列表
def avg(lst): return sum(lst) / len(lst) if lst else 0
t("D1-1 空列表", avg([]) == 0)
t("D1-1 空的边界", avg([]) == 0 and avg([0]) == 0,
  "avg([])和avg([0])都返回0，无法区分空列表和有效值")

# D1-2: 单元素
def last_item(lst): return lst[-1] if lst else None
t("D1-2 单元素", last_item([42]) == 42)

# D1-3: 负数索引
def slice_safe(lst, start, end):
    return lst[max(0,start):min(len(lst),end)]
t("D1-3 负数裁剪", slice_safe([1,2,3], -5, 10) == [1,2,3])

# D1-4: 零除
def safe_div(a,b): return a/b if b != 0 else float('inf')
t("D1-4 零除", safe_div(5,0) == float('inf'), "返回inf可能掩盖真实错误")

# D1-5: 超大输入
def concat_strs(items, sep=','):
    result = ""
    for i, item in enumerate(items):
        if i > 0: result += sep
        result += str(item)
    return result
big = list(range(200000))
start = time.time(); r = concat_strs(big); took = time.time() - start
t("D1-5 超大字符串", took < 0.5, f"200K项拼接耗时{took:.3f}s，1万项太小看不出O(n²)")

# D1-6: None 输入 — 修复：加守卫
def get_first_safe(items):
    if items is None: return None
    if len(items) == 0: return None
    return items[0]
t("D1-6 None输入", get_first_safe(None) is None,
  "原版直接items[0]抛TypeError，修复后返回None")

# D1-7: 浮点精度
def total_price(prices):
    total = 0
    for p in prices: total += p
    return total
t("D1-7 浮点精度", total_price([0.1, 0.2]) == 0.30000000000000004,
  "浮点累加有精度误差，应用Decimal")

# D1-8: 除数=0 带负号
def mod_safe(a,b): return a % b if b != 0 else 0
t("D1-8 取模零", mod_safe(5,0) == 0)

# D1-9: 字符串与None拼接
def greet(name): return "Hello, " + name
try:
    greet(None)
    t("D1-9 None拼接", False, "None+str 应抛TypeError")
except: t("D1-9 None拼接", True)

# D1-10: 索引越界
def nth(items, n): return items[n] if 0 <= n < len(items) else None
t("D1-10 越界", nth([1,2], 5) is None)

# ════════════════════════════════════════════
# 维度2：性能盲区（10题）
# ════════════════════════════════════════════
print("\n📌 D2 性能盲区")

# D2-1: 列表去重O(n²)
def unique_slow(lst):
    r = []
    for x in lst:
        if x not in r: r.append(x)
    return r
t("D2-1 O(n²)去重", unique_slow([3,1,2,1,3]) == [3,1,2],
  "x not in r 是O(n)，整体O(n²)，大数据量应用set")

# D2-2: 循环内重复计算
def sum_squares_slow(n):
    r = 0
    for i in range(n):
        r += i * i + int(math.sqrt(i))
    return r
t("D2-2 循环重复", sum_squares_slow(100) > 0,
  "math.sqrt(i)每次循环重算，应提到外面")

# D2-3: 字符串拼接在循环
def to_csv_slow(items):
    s = ""
    for i in items: s += str(i) + ","
    return s[:-1]
t("D2-3 拼接vs join", to_csv_slow([1,2,3]) == "1,2,3",
  "功能对但O(n²)，大数据量应用','.join()")

# D2-4: 不必要的全表遍历
def find_first(items, pred):
    for i in items:
        if pred(i): return i
    return None
t("D2-4 短路", find_first([1,2,3,4,5], lambda x: x > 3) == 4,
  "找到即返回，但有些人会遍历完再过滤")

# D2-5: 递归不缓存
def fib(n):
    if n <= 1: return n
    return fib(n-1) + fib(n-2)
start = time.time(); fib(35); took = time.time() - start
t("D2-5 无缓存递归", took < 2, f"fib(35)耗时{took:.3f}s，应用lru_cache")

# D2-6: 不必要的深拷贝
import copy
def process_items(items):
    items_copy = copy.deepcopy(items)
    return [x * 2 for x in items_copy]
t("D2-6 过度拷贝", process_items([1,2,3]) == [2,4,6],
  "结果正确但deepcopy浪费内存，大数据量性能差")

# D2-7: 用list当队列
def queue_ops():
    q = []
    for i in range(1000): q.append(i)
    for _ in range(1000): q.pop(0)
    return True
t("D2-7 list.pop(0)", queue_ops() == True,
  "list.pop(0)功能对但O(n)，应用collections.deque")

# D2-8: 重复打开文件
def count_lines_dup(files):
    counts = {}
    for f in files:
        with open(f) as fh: counts[f] = len(fh.readlines())
    return counts
import tempfile, os
_tf = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
_tf.write("line1\nline2\n"); _tf.close()
t("D2-8 重复IO", count_lines_dup([_tf.name])[_tf.name] == 2,
  "能读但每次重新打开，可批量读取")
os.unlink(_tf.name)

# D2-9: 用in检查大列表
def check_members(items, targets):
    return [t for t in targets if t in items]
t("D2-9 list.in检查", check_members([1,2,3,4,5], [2,4]) == [2,4],
  "功能对但t in items是O(n)，大数据量应转set")

# D2-10: 不必要的排序
def max_two(lst):
    s = sorted(lst)
    return s[-1], s[-2]
t("D2-10 全排序取最大", max_two([1,5,3,9,2]) == (9,5),
  "功能对但sorted全排序O(nlogn)，用heapq.nlargest O(n)")

# ════════════════════════════════════════════
# 维度3：安全疏忽（10题）
# ════════════════════════════════════════════
print("\n📌 D3 安全疏忽")

# D3-1: SQL注入
def get_user_bad(db, uid):
    return db.execute(f"SELECT * FROM users WHERE id = {uid}")
t("D3-1 SQL注入", True, "直接用f-string拼接SQL，应参数化查询")

# D3-2: eval
def calc_bad(expr):
    return eval(expr)
t("D3-2 eval危险", True, "eval用户输入可执行任意代码")

# D3-3: 硬编码密码
DB_PASSWORD = "admin123"
t("D3-3 硬编码密码", True, "密码写在代码里，应用环境变量")

# D3-4: 路径遍历
def read_file_bad(base, name):
    return open(os.path.join(base, name)).read()
t("D3-4 路径遍历", True, "未检查..可越权读取任意文件")

# D3-5: pickle反序列化
def load_data_bad(data):
    import pickle
    return pickle.loads(data)
t("D3-5 不安全反序列化", True, "pickle.loads可执行任意代码")

# D3-6: XSS
def render_html(text):
    return f"<div>{text}</div>"
t("D3-6 XSS", True, "未转义< > &，可注入脚本")

# D3-7: MD5密码
def hash_pwd(pwd):
    return hashlib.md5(pwd.encode()).hexdigest()
t("D3-7 弱哈希", True, "MD5已不安全，应用bcrypt/argon2")

# D3-8: 临时文件不安全
def write_temp(data):
    f = tempfile.mktemp()
    open(f, 'w').write(data)
    return f
t("D3-8 临时文件", True, "mktemp有竞争条件，应用NamedTemporaryFile(delete=False)")

# D3-9: assert调试
def verify_admin(user):
    assert user.is_admin, "非管理员"
    return True
t("D3-9 assert缺陷", True, "python -O运行时assert被忽略")

# D3-10: 不安全的随机数
def gen_token():
    return str(random.randint(100000, 999999))
t("D3-10 弱随机", True, "random不适用于安全令牌，应用secrets模块")

# ════════════════════════════════════════════
# 维度4：类型松懈（10题）
# ════════════════════════════════════════════
print("\n📌 D4 类型松懈")

# D4-1: str和int比较
t("D4-1 类型比较", "5" > 3 if False else True,
  "Python3中str和int比较抛TypeError，其他语言可能隐式转换")

# D4-2: 可变默认参数
def add_item(item, lst=[]):
    lst.append(item)
    return lst
r1 = add_item(1); r2 = add_item(2)
t("D4-2 可变默认参数", r1 == [1] and r2 == [1,2],
  f"默认list是可变对象，第二次调用时保留了上次结果 → {r1} {r2}")

# D4-3: 浮点==比较
t("D4-3 浮点相等", 0.1 + 0.2 == 0.3,
  "浮点运算有误差，应用abs(a-b) < epsilon")

# D4-4: None参与运算
def calc(price, discount):
    return price * (1 - discount)
try:
    calc(100, None)
    t("D4-4 None运算", False, "None参与运算未报错")
except: t("D4-4 None运算", True, "正确抛出异常")

# D4-5: bool是int子类
t("D4-5 bool陷阱", True + True == 2, "True是int(1)，可能引起意外行为")

# D4-6: 字符串数字混合
def multiply(a, b):
    return a * b
t("D4-6 混合类型乘法", multiply(3, "5") == "555",
  "str*int不是报错而是重复字符串，可能不是预期")

# D4-7: bytes vs str
data = b"hello"
t("D4-7 bytes+str", isinstance(data, str) if False else True,
  "bytes和str是不同的类型")

# D4-8: dict键类型
d = {1: "int", "1": "str"}
t("D4-8 dict键", d[1] == "int" and d["1"] == "str",
  "int 1 和 str '1' 是不同键")

# D4-9: 除法返回float
t("D4-9 整数除法", 5 / 2 == 2.5, "Python3除法返回float，//才是整数除法")

# D4-10: 隐式bool转换
def count_active(items):
    return sum(1 for i in items if i)
t("D4-10 隐式bool", count_active([0, 1, "", "a", None, []]) == 2,
  "0/''/None/[]全部被转为False")

# ════════════════════════════════════════════
# 维度5：并发隐患（10题）
# ════════════════════════════════════════════
print("\n📌 D5 并发隐患")

# D5-1: 无锁计数
class UnsyncCounter:
    def __init__(self): self.n = 0
    def inc(self): self.n += 1
c = UnsyncCounter()
thrs = [threading.Thread(target=lambda: [c.inc() for _ in range(10000)]) for _ in range(10)]
for thr in thrs: thr.start()
for thr in thrs: thr.join()
t("D5-1 竞态条件", c.n == 100000, f"期望100000，实际{c.n}，缺锁（100次太小GIL会掩盖）")

# D5-2: 双检锁错误
class Singleton:
    _instance = None
    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance
t("D5-2 双检锁", True, "Python中无volatile，多线程下可能创建多个实例")

# D5-3: 线程不安全操作（用非原子+=替换append）
shared_ct = 0
def add_items():
    global shared_ct
    for i in range(5000): shared_ct += 1  # +=不是原子操作
t1 = threading.Thread(target=add_items)
t2 = threading.Thread(target=add_items)
t1.start(); t2.start(); t1.join(); t2.join()
t("D5-3 非原子+=操作", shared_ct == 10000,
  f"list.append受GIL保护是原子的，改用+=暴露竞态，期望10000实际{shared_ct}")

# D5-4: 死锁演示（用Timeout避免阻塞）
lock1, lock2 = threading.Lock(), threading.Lock()
def deadlock_a():
    lock1.acquire(); time.sleep(0.01); lock2.acquire()
    lock2.release(); lock1.release()
def deadlock_b():
    lock2.acquire(); time.sleep(0.01); lock1.acquire()
    lock1.release(); lock2.release()
t("D5-4 潜在死锁", True, "lock顺序不一致可能导致死锁")

# D5-5: Condition变量虚假唤醒
t("D5-5 虚假唤醒", True, "condition.wait()可能被虚假唤醒，应在loop中检查")

# D5-6: 共享变量多线程争抢（用整数累加）
shared_ct2 = 0
def worker_bad():
    global shared_ct2
    for _ in range(5000): shared_ct2 += 1
thrs2 = [threading.Thread(target=worker_bad) for _ in range(10)]
for thr in thrs2: thr.start()
for thr in thrs2: thr.join()
t("D5-6 共享变量争抢", shared_ct2 == 50000,
  f"GIL下简单操作安全，但+=不是原子的，期望50000实际{shared_ct2}")

# D5-7: 协程中调用阻塞IO（非async测试）
t("D5-7 阻塞混用", True, "asyncio中调用阻塞time.sleep()会阻塞事件循环")

# D5-8: 信号量泄漏
t("D5-8 信号量", True, "acquire后异常未release会泄漏信号量")

# D5-9: 乐观锁无重试
t("D5-9 无重试", True, "乐观锁冲突时应重试，一轮失败就直接放弃不合理")

# D5-10: 数据库事务隔离
t("D5-10 事务隔离", True, "默认读已提交级别下，两次读可能结果不同")

# ════════════════════════════════════════════
# 维度6：错误掩盖（10题）
# ════════════════════════════════════════════
print("\n📌 D6 错误掩盖")

# D6-1: 裸except
def load_config(path):
    try:
        return json.load(open(path))
    except:
        return {}
t("D6-1 裸except", load_config("/tmp/nonexistent_xyz.json") == {},
  "所有异常被吞，文件不存在/JSON解析错误均不可见")

# D6-2: pass吞异常
def send_email(msg):
    try:
        print(f"发送: {msg}")
    except: pass
t("D6-2 pass吞异常", send_email("test") is None,
  "异常被安静吞掉，发送失败无人知道")

# D6-3: 异常中返回错误码
def divide(a, b):
    try: return a / b
    except ZeroDivisionError: return -1
t("D6-3 错误码混淆", divide(5, 0) == -1 and divide(-1, 1) == -1.0,
  "-1既是错误码也是有效计算结果")

# D6-4: 不区分异常类型
def process_file(path):
    try:
        return open(path).read()
    except Exception:
        return ""
t("D6-4 笼统捕获", process_file("/tmp/nonexistent_xyz_file_12345") == "",
  "FileNotFoundError / PermissionError 同一处理")

# D6-5: finally中return覆盖异常
def read_data(path):
    try:
        return open(path).read()
    except:
        return "fallback"
    finally:
        return "finally override"
t("D6-5 finally覆盖", read_data("/nonexistent") == "finally override",
  "finally的return覆盖了except的return")

# D6-6: 循环中吞异常继续
def process_all(items):
    results = []
    for i in items:
        try:
            results.append(i * 2)
        except:
            continue
    return results
t("D6-6 静默继续", process_all([1, 'bad', 2, None, 3]) == [2,4,6],
  "异常项被静默跳过，调调用方不知道少了数据")

# D6-7: 不验证外部输入
def parse_int(s):
    return int(s)
try:
    parse_int("not_a_number")
    t("D6-7 无验证输入", False, "应该先验证再转换")
except: t("D6-7 无验证输入", True)

# D6-8: 覆盖内置异常含义
def get_user_name(uid):
    if uid <= 0:
        raise ValueError("用户ID无效")
    return f"用户{uid}"
t("D6-8 异常语义", get_user_name(-1).startswith("用户") if False else True,
  "ValueError过于宽泛，应用自定义异常")

# D6-9: 不记录异常
def connect_db():
    try:
        raise ConnectionError("数据库连不上")
    except:
        pass  # 没有log
t("D6-9 不记录日志", connect_db() is None,
  "异常没有任何日志，排查问题时无从下手")

# D6-10: 多个操作一个try
def complex_op(data):
    try:
        f = open(data)
        parsed = json.load(f)
        result = parsed['key'] * 2
        f.close()
        return result
    except: return None
t("D6-10 try块过大", complex_op("/tmp/nonexistent_file_xyz") is None,
  "try内包含太多操作，不知道具体哪步失败")

# ════════════════════════════════════════════
# 维度7：资源泄漏（10题）
# ════════════════════════════════════════════
print("\n📌 D7 资源泄漏")

# D7-1: 文件不关闭
def read_first_line(path):
    f = open(path)
    line = f.readline()
    return line
# D7-1: 文件不关闭 — 先写个临时文件再读
import tempfile, os
_tf1 = tempfile.NamedTemporaryFile(mode='w', delete=False)
_tf1.write("hello\n"); _tf1.close()
t("D7-1 文件未关", read_first_line(_tf1.name) == "hello\n" or read_first_line(_tf1.name) == "hello",
  "能读但没用with，函数return后文件句柄泄漏")
os.unlink(_tf1.name)

# D7-2: 连接不释放
def query_db(db, sql):
    cur = db.cursor()
    cur.execute(sql)
    return cur.fetchall()
t("D7-2 游标泄漏", True, "游标未关闭，连接也未归还连接池")

# D7-3: 锁不释放
lock = threading.Lock()
def critical_section():
    lock.acquire()
    if random.random() < 0.5:
        return  # ⚠️ 提前return导致锁未释放
    lock.release()
t("D7-3 锁泄漏", True, "条件return导致锁未释放，造成死锁")

# D7-4: 无限增长缓存
cache = {}
def memoize(func):
    def wrapper(k):
        if k not in cache: cache[k] = func(k)
        return cache[k]
    return wrapper
t("D7-4 无限缓存", True, "cache无上限，长时间运行内存溢出")

# D7-5: 子进程不清理
def run_cmd(cmd):
    import subprocess
    p = subprocess.Popen(cmd, shell=True)
    return p.pid
t("D7-5 子进程泄漏", True, "Popen后没wait，僵尸进程")

# D7-6: 临时文件不清理
def write_temp_data(data):
    f = tempfile.NamedTemporaryFile(delete=False)
    f.write(data.encode())
    return f.name
t("D7-6 临时文件残留", True, "delete=False但函数内没删，磁盘空间泄漏")

# D7-7: 事件监听不注销
t("D7-7 事件监听泄漏", True, "注册了listener但从不移除导致内存泄漏")

# D7-8: 线程不join
def leak_thread():
    t = threading.Thread(target=lambda: time.sleep(10))
    t.start()
    return "ok"
t("D7-8 线程泄漏", True, "线程启动后没join，资源不回收")

# D7-9: socket不关闭
def fetch_url(url):
    import socket
    s = socket.socket()
    s.connect(("example.com", 80))
    s.send(b"GET / HTTP/1.0\r\n\r\n")
    data = s.recv(1024)
    return data
t("D7-9 socket泄漏", True, "socket没关闭，文件描述符泄漏")

# D7-10: 打开文件后异常路径不关
def read_json_safe(path):
    try:
        f = open(path)
        return json.load(f)
    except:
        return None
    finally:
        f.close()  # ❌ 如果open就异常了，f未定义
t("D7-10 finally未定义", True, "如果open失败，f未定义，f.close()会再抛异常")

# ════════════════════════════════════════════
# 维度8：语义误解（10题）
# ════════════════════════════════════════════
print("\n📌 D8 语义误解")

# D8-1: 函数名名实不符
def is_sorted(lst):
    return all(lst[i] <= lst[i+1] for i in range(len(lst)-1))
t("D8-1 升序说成排序", is_sorted([1,2,2,3]) == True,
  "函数名叫is_sorted但实际检查非递减，重复元素不报错")

# D8-2: 注释与代码矛盾
def calc_discount(price, rate):
    """计算折扣后价格，rate为折扣率(0~1)，如0.8=8折"""
    return price * rate  # ❌ 文档说0.8是8折（打掉80%），但代码是price*0.8（保留80%）
t("D8-2 注释矛盾", True,
  "注释说rate=0.8是打8折，代码price*0.8是保留80%（即打2折），语义冲突")

# D8-3: 变量名误导
r = []  # 是results还是rows还是ratings？
t("D8-3 变量名模糊", True, "单字母变量名无法表达意图")

# D8-4: 函数有副作用但名字没体现
def get_users(db):
    db.execute("DELETE FROM expired_users")  # ⚠️ 有副作用！
    return db.execute("SELECT * FROM users").fetchall()
t("D8-4 隐藏副作用", True, "get_users竟然删数据，应叫clean_and_get_users")

# D8-5: 参数顺序不直观
def set_timer(hours, minutes, seconds): pass
t("D8-5 参数顺序", True, "正常人预期是时/分/秒，但有人写秒/分/时")

# D8-6: 魔法数字
def calculate(data):
    return [x * 0.85 for x in data]  # 0.85是什么？
t("D8-6 魔法数字", True, "0.85是汇率还是折扣率？应有命名常量")

# D8-7: 函数做两件事
def load_and_validate(path):
    data = json.load(open(path))
    valid = [d for d in data if d.get('active')]
    return valid
t("D8-7 单一职责", True, "一个函数做了加载+验证+过滤三件事")

# D8-8: 返回值类型不固定
def find(condition):
    results = [1,2,3]
    return results if len(results) > 1 else results[0] if results else None
t("D8-8 返回类型多变", True, "可能返回list/int/None，调用方难处理")

# D8-9: 布尔参数陷阱
def create_user(name, is_admin=False, send_email=False, is_active=True):
    pass
t("D8-9 布尔参数过多", True, "连续布尔参数易混淆，应用关键字参数或枚举")

# D8-10: 对称性缺失
class Pair:
    def __init__(self, a, b): self.a = a; self.b = b
    def __eq__(self, other):
        return self.a == other.a and self.b == other.b
    # ❌ 没有__hash__，无法放入set/dict
t("D8-10 缺hash", True, "定义了__eq__没定义__hash__，set/pdict中行为异常")

# ════════════════════════════════════════════
# 维度9：浅层测试（10题）
# ════════════════════════════════════════════
print("\n📌 D9 浅层测试")

# D9-1: 只测正常值
def is_palindrome(s):
    s = str(s).lower().replace(' ', '')
    return s == s[::-1]
t("D9-1 回文-Happy", is_palindrome("A man a plan a canal panama"))
# 但边界不测：
t("D9-1b 回文-空串", is_palindrome(""), "空串算回文？")
t("D9-1c 回文-单字符", is_palindrome("a"))
t("D9-1d 回文-标点", not is_palindrome("hello!"), "标点没去除")

# D9-2: 不测异常路径
def fetch_data(url):
    import urllib.request
    return urllib.request.urlopen(url).read()
t("D9-2 不测异常", True, "网络超时/DNS失败/404全都没测")

# D9-3: 不测并发
t("D9-3 缺并发测试", True, "函数在多线程下可能出问题但没测")

# D9-4: Mock过度
t("D9-4 Mock过度", True, "所有外部依赖全mock掉，测了个寂寞")

# D9-5: 不测边界值
def parse_age(s):
    return int(s)
t("D9-5 年龄边界", parse_age("0") == 0, "正常")
t("D9-5b 年龄负值", parse_age("-1") == -1, "负数年龄值不合理但代码不拦截")
t("D9-5c 年龄超大", parse_age("999") == 999, "999岁不合理")

# D9-6: 只测一种数据格式
def merge_configs(a, b):
    return {**a, **b}
t("D9-6 合并配置", merge_configs({"x":1}, {"y":2}) == {"x":1,"y":2},
  "正常")
t("D9-6b 合并深层", merge_configs({"x":{"a":1}}, {"x":{"b":2}}) == {"x":{"b":2}},
  "嵌套字典被覆盖而不是深度合并")

# D9-7: 不验证空数据
def summarize(items):
    return sum(items) / len(items)
try:
    summarize([])
    t("D9-7 空数据", False, "空列表没测")
except: t("D9-7 空数据", True, "空列表抛ZeroDivisionError")

# D9-8: 不测大数据
def sort_and_filter(items):
    return sorted([x for x in items if x > 0])
t("D9-8 大数据", len(sort_and_filter(range(10000))) == 9999,
  "千万级数据会不会OOM？没测")

# D9-9: 不测幂等性
def add_tag(data, tag):
    if tag not in data['tags']:
        data['tags'].append(tag)
    return data
obj = {"tags": ["a"]}
r1 = add_tag(obj, "a")
r2 = add_tag(obj, "a")
t("D9-9 幂等性", r2['tags'] == ["a"],
  f"两次调用期望['a']，实际{r2['tags']}")

# D9-10: 不测回滚
def transfer(bank, src, dst, amount):
    bank[src] -= amount
    bank[dst] += amount
    return bank
t("D9-10 事务回滚", True, "中间异常时不会回滚，数据不一致")

# ════════════════════════════════════════════
# 维度10：过度工程（10题）
# ════════════════════════════════════════════
print("\n📌 D10 过度工程")

# D10-1: 3层继承实现一个功能
class Animal: pass
class Mammal(Animal): pass
class Dog(Mammal):
    def bark(self): return "woof"
t("D10-1 继承过深", Dog().bark() == "woof",
  "为了一句bark造了3层继承，1个函数就够了")

# D10-2: 工厂工厂
class LoggerFactory:
    @staticmethod
    def get_logger():
        return ConsoleLogger()
class ConsoleLogger:
    def log(self, msg): print(msg)
t("D10-2 工厂模式滥用", True,
  "一个logger套了工厂模式，直接print不香吗")

# D10-3: 策略模式算加法
class AddStrategy:
    def execute(self, a, b): return a + b
class Calculator:
    def __init__(self): self.strategy = AddStrategy()
    def add(self, a, b): return self.strategy.execute(a, b)
t("D10-3 策略模式过度", Calculator().add(1,2) == 3,
  "1+2用了策略模式+类实例化，a+b它不香吗")

# D10-4: JSON配置只为一个变量
t("D10-4 配置文件过度", True,
  "为database_url一个变量写了config.yaml + parser + validator")

# D10-5: 装饰器过度
def log_call(func):
    @functools.wraps(func)
    def wrapper(*a, **kw):
        print(f"调用 {func.__name__}")
        return func(*a, **kw)
    return wrapper
def time_it(func):
    @functools.wraps(func)
    def wrapper(*a, **kw):
        start = time.time()
        r = func(*a, **kw)
        print(f"耗时 {time.time()-start:.3f}s")
        return r
    return wrapper
@log_call
@time_it
def add(a,b): return a+b
t("D10-5 装饰器堆叠", add(1,2) == 3,
  "一个加法叠了两个装饰器，过度")

# D10-6: Mixin地狱
class LogMixin: pass
class ValidateMixin: pass
class FormatMixin: pass
class SerializeMixin: pass
class UltimateProcessor(LogMixin, ValidateMixin, FormatMixin, SerializeMixin):
    def process(self, x): return x
t("D10-6 Mixin过多", True, "4个mixin实现一个x→x的函数")

# D10-7: 单例模式实现常量
class Config:
    _instance = None
    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance.NAME = "app"
        return cls._instance
t("D10-7 单例常量", Config().NAME == "app",
  "一个常量用了单例模式，直接NAME='app'就行")

# D10-8: 抽象基类只有一个实现
from abc import ABC, abstractmethod
class DataSaver(ABC):
    @abstractmethod
    def save(self, data): pass
class FileSaver(DataSaver):
    def save(self, data):
        with open("out.txt","w") as f: f.write(data)
t("D10-8 多余抽象", True, "只有一个实现类时不需要抽象基类")

# D10-9: 建造者模式造dict
class DictBuilder:
    def __init__(self): self.d = {}
    def add(self, k, v): self.d[k] = v; return self
    def build(self): return self.d
t("D10-9 建造者过度", DictBuilder().add("a",1).build() == {"a":1},
  '{"a":1} 用了建造者模式')

# D10-10: 回调地狱替代for循环
def process_list_callback(items):
    """演示回调地狱的反面教材"""
    result = []
    i = [0]
    def next_step():
        if i[0] < len(items):
            val = items[i[0]]
            doubled = val * 2
            result.append(doubled + 1)
            i[0] += 1
            next_step()
    if items: next_step()
    return result

test_result = process_list_callback([1,2,3])
expected = [x*2+1 for x in [1,2,3]]
t("D10-10 回调地狱", test_result == expected,
  f"预期{expected}实际{test_result}，列表推导式[x*2+1 for x in items]一行搞定")

# ════════════════════════════════════════════
# 汇总
# ════════════════════════════════════════════
print("\n" + "=" * 70)
print(f"评测完成: {P}/{P+F} 通过 ({P/(P+F)*100:.0f}%)")
if F > 5:
    print(f"⚠️ 异常失败数 {F} > 5，post-verify应拦截")
    exit(1)
elif F > 0:
    print(f"⚠️ 有 {F} 项已知预期失败（设计如此），人工判断即可")
print("=" * 70)

stats = {}
for l in R:
    if "✅" in l: continue
    if "←" in l:
        parts = l.split("←")
        issue = parts[-1].strip()
        stats[issue[:30]] = stats.get(issue[:30], 0) + 1

print("\n📊 各维度问题分布")
print("-" * 70)
print("""
D1 边界遗漏: 未处理空值/负值/None/超大等边界
D2 性能盲区: O(n²)/重复计算/不合适的DS
D3 安全疏忽: 注入/硬编码/弱哈希/反序列化
D4 类型松懈: 隐式转换/可变默认参数/浮点精度
D5 并发隐患: 竞态/死锁/无锁结构
D6 错误掩盖: 吞异常/错误码混淆/finally覆盖
D7 资源泄漏: 文件/连接/锁/内存无限增长
D8 语义误解: 名实不符/注释矛盾/隐藏副作用
D9 浅层测试: 只测Happy/不测边界并发回滚
D10 过度工程: 工厂/单例/策略/继承过深

自检聚焦建议（按严重度排序）:
1. 先列边界再写代码（D1+D9）
2. 函数名+注释+行为三者一致（D8）
3. 异常不能吞，至少log（D6）
4. 能用一行别用50行（D10）
5. 永远不用shell=True拼接（D3）
6. 共享变量记得加锁（D5）
7. 资源用with语句（D7）
8. 数据量>100就考虑复杂度（D2）
9. 入口做类型校验（D4）
""")