#!/usr/bin/env python3
"""
验证Web界面心跳显示的脚本
"""

import requests

def verify_ui():
    """验证Web界面心跳显示"""
    base_url = "http://localhost:8080"
    
    # 创建会话
    session = requests.Session()
    
    # 登录
    login_data = {
        "username": "cai",
        "password": "22446688"
    }
    
    print("正在登录...")
    login_response = session.post(f"{base_url}/auth/login", json=login_data)
    if login_response.status_code != 200:
        print(f"登录失败: {login_response.text}")
        return
    
    print("登录成功!")
    
    # 获取主页面
    print("获取主页面...")
    response = session.get(f"{base_url}/")
    if response.status_code == 200:
        # 查找"最后检查"文本
        if "最后检查" in response.text:
            print("✅ 找到了'最后检查'文本")
            
            # 查找更多相关文本
            if "lastHeartbeat" in response.text:
                print("✅ 找到了lastHeartbeat元素ID")
            else:
                print("❌ 没有找到lastHeartbeat元素ID")
                
            # 检查是否还有旧的"最后心跳"文本
            if "最后心跳" in response.text:
                print("⚠️  仍然存在'最后心跳'文本（可能需要清理）")
            else:
                print("✅ 已成功替换为'最后检查'")
                
        else:
            print("❌ 没有找到'最后检查'文本")
    else:
        print(f"获取主页面失败: {response.status_code}")
    
    # 获取状态API
    print("\n获取状态API...")
    status_response = session.get(f"{base_url}/api/status")
    if status_response.status_code == 200:
        data = status_response.json()
        if data.get('status') == 'success':
            heartbeat_info = data.get('data', {}).get('heartbeat', {})
            print(f"✅ API返回的心跳信息:")
            print(f"   状态: {heartbeat_info.get('status', 'unknown')}")
            print(f"   最后检查: {heartbeat_info.get('last_check', 'N/A')}")
            print(f"   最后心跳: {heartbeat_info.get('last_heartbeat', 'N/A')}")
            print(f"   秒前: {heartbeat_info.get('seconds_ago', 'N/A')}")
        else:
            print(f"❌ API返回错误: {data}")
    else:
        print(f"❌ 状态API失败: {status_response.status_code}")

if __name__ == "__main__":
    verify_ui() 