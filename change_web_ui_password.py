#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
闲鱼自动回复管理面板 - 密码修改工具
"""

import json
import os
import getpass
import sys
from werkzeug.security import generate_password_hash

def load_web_ui_config():
    """加载Web UI配置文件"""
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
    
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config, config_file
        else:
            return default_config, config_file
    except Exception as e:
        print(f"读取配置文件失败: {e}")
        return default_config, config_file

def save_web_ui_config(config, config_file):
    """保存Web UI配置文件"""
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"保存配置文件失败: {e}")
        return False

def change_password():
    """修改密码"""
    print("闲鱼自动回复管理面板 - 密码修改工具")
    print("=" * 50)
    
    # 加载配置
    config, config_file = load_web_ui_config()
    
    print(f"当前用户名: {config['auth']['username']}")
    print()
    
    # 输入新用户名（可选）
    new_username = input("请输入新用户名 (留空保持不变): ").strip()
    if new_username:
        config['auth']['username'] = new_username
        print(f"用户名已更新为: {new_username}")
    
    # 输入新密码
    while True:
        new_password = getpass.getpass("请输入新密码: ")
        if len(new_password) < 6:
            print("密码长度至少6位，请重新输入")
            continue
        
        confirm_password = getpass.getpass("请确认新密码: ")
        if new_password != confirm_password:
            print("两次输入的密码不一致，请重新输入")
            continue
        
        break
    
    # 更新配置
    config['auth']['password'] = new_password
    
    # 询问是否更新session密钥
    update_secret = input("是否同时更新session密钥? (y/N): ").strip().lower()
    if update_secret in ['y', 'yes']:
        import secrets
        import string
        # 生成随机密钥
        alphabet = string.ascii_letters + string.digits
        new_secret = ''.join(secrets.choice(alphabet) for _ in range(50))
        config['auth']['secret_key'] = new_secret
        print("Session密钥已更新")
    
    # 保存配置
    if save_web_ui_config(config, config_file):
        print()
        print("✅ 密码修改成功!")
        print(f"用户名: {config['auth']['username']}")
        print("密码: ********")
        print()
        print("请重启Web UI服务以使更改生效:")
        print("  ./web_ui_control.sh restart")
    else:
        print("❌ 密码修改失败!")
        sys.exit(1)

def main():
    """主函数"""
    try:
        change_password()
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(0)
    except Exception as e:
        print(f"\n发生错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 