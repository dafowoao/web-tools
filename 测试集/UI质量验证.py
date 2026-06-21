#!/usr/bin/env python3
"""CodeBuddy UI 质量验证器 — 检查HTML/CSS/图片"""
import os, sys, re, json
from html.parser import HTMLParser

P, F, W = 0, 0, 0  # pass, fail, warn

class HTMLChecker(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []  # (has_alt, alt_text)
        self.buttons = []  # has_text
        self.meta_viewport = None
        self.labels = set()
        self.inputs = set()
        self.semantic_tags = []
        self.errors = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == 'img':
            has_alt = 'alt' in attrs_dict
            self.images.append((has_alt, attrs_dict.get('alt', '')))
        if tag == 'button':
            has_text = False
            self.buttons.append(has_text)  # 简版
        if tag == 'meta' and attrs_dict.get('name') == 'viewport':
            self.meta_viewport = attrs_dict.get('content', '')
        if tag == 'label':
            self.labels.add(attrs_dict.get('for', ''))
        if tag == 'input':
            self.inputs.add(attrs_dict.get('id', ''))
        if tag in ('nav', 'main', 'article', 'section', 'aside', 'header', 'footer'):
            self.semantic_tags.append(tag)

def check_html(filepath):
    """检查HTML文件"""
    global P, F
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        W += 1; return

    checker = HTMLChecker()
    try:
        checker.feed(content)
    except:
        pass

    # 检查viewport
    if checker.meta_viewport:
        if 'width=device-width' in checker.meta_viewport and 'initial-scale=1.0' in checker.meta_viewport:
            P += 1
        else:
            F += 1; print(f'  ❌ viewport 不是 width=device-width: {checker.meta_viewport}')
    else:
        W += 1; print(f'  ⚠️ 无 <meta viewport>')

    # 检查图片alt
    no_alt = [i for i, (has_alt, _) in enumerate(checker.images) if not has_alt]
    if no_alt:
        F += 1; print(f'  ❌ {len(no_alt)} 张图片缺少 alt 属性')
    elif checker.images:
        P += 1

    # 检查语义标签
    if checker.semantic_tags:
        P += 1
    else:
        W += 1; print(f'  ⚠️ 没有使用语义标签（nav/main/article等）')

    # 检查font-size: 16px以下（移动端隐患）
    font_small = re.findall(r'font-size:\s*(\d+)px', content)
    too_small = [int(s) for s in font_small if int(s) < 12]
    if too_small:
        print(f'  ⚠️ 有字号 < 12px: {too_small}')

def check_css(filepath):
    """检查CSS/HTML文件中的CSS质量"""
    global P, F
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        return

    # CSS变量数量
    css_vars = re.findall(r'--[\w-]+:', content)
    if len(css_vars) >= 5:
        P += 1
    else:
        F += 1; print(f'  ❌ CSS变量太少: {len(css_vars)} 个（需≥5）')

    # 响应式断点
    breakpoints = re.findall(r'@media\s*\([^)]+\)', content)
    if len(breakpoints) >= 3:
        P += 1
    else:
        F += 1; print(f'  ❌ 响应式断点太少: {len(breakpoints)} 个（需≥3）')

    # box-sizing
    if 'box-sizing: border-box' in content or 'box-sizing:border-box' in content:
        P += 1
    else:
        F += 1; print(f'  ❌ 缺少全局 box-sizing: border-box')

    # !important
    important_count = content.count('!important')
    if important_count <= 2:
        P += 1
    else:
        F += 1; print(f'  ❌ 用了 {important_count} 次 !important（过度）')

    # z-index: 9999
    z_high = re.findall(r'z-index:\s*99\d+', content)
    if z_high:
        print(f'  ⚠️ 使用了高 z-index: {z_high}')

    # 动画属性
    anim_top = re.findall(r'animation.*\btop\b', content)
    anim_left = re.findall(r'animation.*\bleft\b', content)
    if anim_top or anim_left:
        print(f'  ⚠️ 动画用了 top/left（应改用 transform）')

def check_images_in_dir(directory):
    """检查目录中的图片文件"""
    global P, F, W
    image_exts = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.ico')
    images = [f for f in os.listdir(directory) if f.lower().endswith(image_exts)]
    if not images:
        W += 1; return

    # 检查SVG有无viewBox
    for img in images:
        if img.endswith('.svg'):
            path = os.path.join(directory, img)
            try:
                with open(path, 'r') as f:
                    content = f.read()
                if 'viewBox' not in content:
                    print(f'  ⚠️ SVG "{img}" 缺少 viewBox')
            except:
                pass

        # 检查文件大小
        path = os.path.join(directory, img)
        size = os.path.getsize(path)
        if size > 500 * 1024:  # >500KB
            print(f'  ⚠️ 图片过大: {img} ({size/1024:.0f}KB)')
        elif size < 100 and not img.endswith('.svg'):
            print(f'  ⚠️ 图片过小: {img} ({size}B)，可能占位符')

def scan_html_files(directory):
    """扫描目录中所有HTML/CSS文件"""
    html_files = []
    css_files = []
    for root, dirs, files in os.walk(directory):
        # 跳过node_modules, dist等
        if any(skip in root for skip in ['node_modules', 'dist', '.git', '__pycache__']):
            continue
        for f in files:
            if f.endswith('.html'):
                html_files.append(os.path.join(root, f))
            if f.endswith('.css'):
                css_files.append(os.path.join(root, f))

    if not html_files and not css_files:
        print('  未发现HTML/CSS文件')
        return

    for hf in html_files[:5]:  # 最多检查5个
        print(f'\n  📄 {os.path.relpath(hf, directory)}')
        check_html(hf)
        check_css(hf)

    for cf in css_files[:5]:
        if cf not in html_files:
            print(f'\n  📄 {os.path.relpath(cf, directory)}')
            check_css(cf)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('用法: python UI质量验证.py <目录>')
        sys.exit(1)

    target = sys.argv[1]
    if not os.path.isdir(target):
        print(f'目录不存在: {target}')
        sys.exit(1)

    print(f'🔍 CodeBuddy UI 质量验证: {target}')
    print('=' * 50)
    scan_html_files(target)
    print()
    print(f'  通过: {P}  失败: {F}  警告: {W}')
    if F > 0:
        print(f'  ❌ 有 {F} 项未通过，建议修复')
        sys.exit(1)
    else:
        print(f'  ✅ UI质量达标')