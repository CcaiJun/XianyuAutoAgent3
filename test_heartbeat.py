#!/usr/bin/env python3
"""
心跳功能测试脚本
"""

import requests
import json
import time

def test_heartbeat():
    """测试心跳功能"""
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
    
    # 测试状态API
    print("\n测试心跳状态...")
    for i in range(5):
        try:
            response = session.get(f"{base_url}/api/status")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    heartbeat_info = data.get('data', {}).get('heartbeat', {})
                    print(f"第{i+1}次检查:")
                    print(f"  状态: {heartbeat_info.get('status', 'unknown')}")
                    print(f"  最后检查: {heartbeat_info.get('last_check', 'N/A')}")
                    print(f"  最后心跳: {heartbeat_info.get('last_heartbeat', 'N/A')}")
                    print(f"  秒前: {heartbeat_info.get('seconds_ago', 'N/A')}")
                else:
                    print(f"API返回错误: {data}")
            else:
                print(f"HTTP错误: {response.status_code}")
        except Exception as e:
            print(f"请求异常: {e}")
        
        if i < 4:  # 不是最后一次
            print("等待5秒...")
            time.sleep(5)
    
    print("\n测试完成!")

if __name__ == "__main__":
    test_heartbeat() 