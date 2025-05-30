#!/usr/bin/env python3
"""
XianyuAutoAgent2 系统功能测试脚本
测试所有核心功能是否正常工作
"""

import requests
import json
import time
import os
import sys
from config.logger_config import get_logger

# 获取专用日志记录器
logger = get_logger("test", "system")


class SystemTester:
    """系统测试器"""
    
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def test_web_server(self):
        """测试Web服务器是否响应"""
        try:
            response = self.session.get(f"{self.base_url}/auth/login")
            if response.status_code == 200:
                logger.info("✓ Web服务器正常响应")
                return True
            else:
                logger.error(f"✗ Web服务器响应异常: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"✗ Web服务器连接失败: {e}")
            return False
    
    def test_login(self):
        """测试登录功能"""
        try:
            # 首先获取登录页面
            login_page = self.session.get(f"{self.base_url}/auth/login")
            if login_page.status_code != 200:
                logger.error("无法访问登录页面")
                return False
            
            # 尝试登录 - 使用JSON格式
            login_data = {
                "username": "cai",
                "password": "22446688"
            }
            
            response = self.session.post(
                f"{self.base_url}/auth/login", 
                json=login_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                response_data = response.json()
                if response_data.get('status') == 'success':
                    logger.info("✓ 登录功能正常")
                    return True
                else:
                    logger.error(f"✗ 登录失败: {response_data.get('message')}")
                    return False
            else:
                logger.error(f"✗ 登录请求失败: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"✗ 登录测试异常: {e}")
            return False
    
    def test_api_endpoints(self):
        """测试API端点"""
        endpoints = [
            "/api/status",
            "/api/config",
            "/api/logs",
            "/api/health"
        ]
        
        results = []
        for endpoint in endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                if response.status_code == 200:
                    logger.info(f"✓ API端点 {endpoint} 正常")
                    results.append(True)
                else:
                    logger.error(f"✗ API端点 {endpoint} 异常: {response.status_code}")
                    results.append(False)
            except Exception as e:
                logger.error(f"✗ API端点 {endpoint} 测试失败: {e}")
                results.append(False)
        
        return all(results)
    
    def test_configuration_files(self):
        """测试配置文件是否存在"""
        required_files = [
            "web_ui_config.json",
            "config/prompts/classify_prompt.txt",
            "config/prompts/price_prompt.txt", 
            "config/prompts/tech_prompt.txt",
            "config/prompts/default_prompt.txt"
        ]
        
        results = []
        for file_path in required_files:
            if os.path.exists(file_path):
                logger.info(f"✓ 配置文件存在: {file_path}")
                results.append(True)
            else:
                logger.warning(f"⚠ 配置文件缺失: {file_path}")
                results.append(False)
        
        return all(results)
    
    def test_main_program_control(self):
        """测试主程序控制功能"""
        try:
            # 测试获取状态
            status_response = self.session.get(f"{self.base_url}/api/status")
            if status_response.status_code == 200:
                status_data = status_response.json()
                logger.info(f"✓ 状态获取正常: {status_data.get('status')}")
                
                # 尝试启动主程序
                start_response = self.session.post(f"{self.base_url}/api/start")
                if start_response.status_code == 200:
                    logger.info("✓ 主程序启动命令发送成功")
                    
                    # 等待一会儿再检查状态
                    time.sleep(3)
                    
                    # 再次检查状态
                    status_response2 = self.session.get(f"{self.base_url}/api/status")
                    if status_response2.status_code == 200:
                        logger.info("✓ 主程序状态监控正常")
                        return True
                
                return True
            else:
                logger.error("✗ 状态获取失败")
                return False
                
        except Exception as e:
            logger.error(f"✗ 主程序控制测试失败: {e}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        logger.info("开始系统功能测试...")
        
        tests = [
            ("Web服务器连接", self.test_web_server),
            ("用户登录", self.test_login),
            ("API端点", self.test_api_endpoints),
            ("配置文件", self.test_configuration_files),
            ("主程序控制", self.test_main_program_control)
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            logger.info(f"\n=== 测试: {test_name} ===")
            try:
                result = test_func()
                results[test_name] = result
                if result:
                    logger.info(f"✓ {test_name} 测试通过")
                else:
                    logger.error(f"✗ {test_name} 测试失败")
            except Exception as e:
                logger.error(f"✗ {test_name} 测试异常: {e}")
                results[test_name] = False
        
        # 总结
        logger.info("\n" + "="*50)
        logger.info("测试结果总结:")
        passed = sum(1 for r in results.values() if r)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✓ 通过" if result else "✗ 失败"
            logger.info(f"  {test_name}: {status}")
        
        logger.info(f"\n总计: {passed}/{total} 个测试通过")
        
        if passed == total:
            logger.info("🎉 所有测试都通过了！系统运行正常！")
            return True
        else:
            logger.warning(f"⚠️  有 {total-passed} 个测试失败，请检查相关功能")
            return False


def main():
    """主函数"""
    print("XianyuAutoAgent2 系统功能测试")
    print("="*50)
    
    tester = SystemTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 系统测试完成！所有功能正常！")
        sys.exit(0)
    else:
        print("\n⚠️  系统测试发现问题，请检查日志")
        sys.exit(1)


if __name__ == '__main__':
    main() 