#!/usr/bin/env python3
"""文件工具 — 统一处理 GBK/UTF-8 编码问题"""
import os

def read_file(path):
    """统一读文件，自动尝试编码"""
    for enc in ['utf-8', 'gbk', 'gb2312', 'gb18030']:
        try:
            with open(path, 'r', encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError):
            continue
    # 最后的尝试：忽略错误
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()

def write_file(path, content):
    """统一写文件，用 UTF-8"""
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def safe_path(path):
    """安全路径，统一用正斜杠"""
    return path.replace('\\', '/')

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        content = read_file(sys.argv[1])
        print(f"✅ 读取成功: {len(content)} 字符")
    else:
        print("用法: python 文件工具.py <文件路径>")