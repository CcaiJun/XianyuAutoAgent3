#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web UI 登录信息修改工具
用于安全地修改 Web UI 的登录用户名和密码
"""

import json
import os
import getpass
from werkzeug.security import generate_password_hash

def load_config():
    """加载当前配置"""
    config_file = "web_ui_config.json"
    default_config = {
        "auth": {
            "username": "admin",
            "password": "admin123",
            "secret_key": "xianyu_auto_agent_secret_key_change_this_in_production"
        },
        "session": {
            "permanent_session_lifetime_hours": 24
        }
    }
    
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return default_config

def save_config(config):
    """保存配置"""
    with open("web_ui_config.json", 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

def main():
    print("=== 闲鱼自动助手 Web UI 登录信息修改工具 ===\n")
    
    # 加载当前配置
    config = load_config()
    current_username = config['auth']['username']
    
    print(f"当前用户名: {current_username}")
    print()
    
    # 获取新的用户名
    new_username = input(f"请输入新的用户名 (回车保持当前用户名 '{current_username}'): ").strip()
    if not new_username:
        new_username = current_username
    
    # 获取新密码
    print("\n请输入新密码:")
    new_password = getpass.getpass("新密码: ")
    if not new_password:
        print("密码不能为空！")
        return
    
    confirm_password = getpass.getpass("确认密码: ")
    if new_password != confirm_password:
        print("两次输入的密码不一致！")
        return
    
    # 询问是否更新session密钥
    update_secret = input("\n是否生成新的Session密钥? (y/N): ").lower().strip()
    if update_secret == 'y':
        import secrets
        new_secret_key = secrets.token_urlsafe(32)
        config['auth']['secret_key'] = new_secret_key
        print("已生成新的Session密钥")
    
    # 更新配置
    config['auth']['username'] = new_username
    config['auth']['password'] = new_password  # 注意：这里存储明文，web_ui.py会在加载时进行哈希
    
    # 保存配置
    save_config(config)
    
    print(f"\n✅ 登录信息已更新！")
    print(f"新用户名: {new_username}")
    print("新密码: ********")
    print("\n⚠️  请重启 Web UI 使新配置生效:")
    print("   pkill -f web_ui.py && python web_ui.py")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n操作已取消")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}") 