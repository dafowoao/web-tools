#!/usr/bin/env python3
"""将进化中心安装到任意项目目录
用法: python 安装到项目.py <项目目录>
"""
import os, sys, shutil

EVO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def install(project_dir):
    if not os.path.isdir(project_dir):
        print(f"❌ 目录不存在: {project_dir}")
        return False

    claude_dir = os.path.join(project_dir, ".claude")
    os.makedirs(claude_dir, exist_ok=True)

    # 写 hooks 配置
    settings = os.path.join(claude_dir, "settings.local.json")
    config = {
        "hooks": {
            "SessionStart": [
                {"hooks": [{"type": "command",
                    "command": f"python {EVO}/测试集/同步规则.py --auto",
                    "timeout": 30}]}
            ],
            "PostToolUse": [
                {"matcher": "Write|Edit",
                 "hooks": [{"type": "command",
                    "command": "C:\\Users\\2026\\.claude\\verify_hook.bat",
                    "timeout": 60}]}
            ]
        }
    }

    import json
    if os.path.exists(settings):
        with open(settings, 'r', encoding='utf-8') as f:
            existing = json.load(f)
        existing["hooks"] = config["hooks"]
    else:
        existing = config

    with open(settings, 'w', encoding='utf-8') as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

    print(f"✅ 进化中心已安装到 {project_dir}")
    print(f"   {settings}")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python 安装到项目.py <项目目录>")
        sys.exit(1)
    install(sys.argv[1])