#!/usr/bin/env python3
"""
Cookie自动更新功能测试脚本
验证自动更新.env文件中COOKIES_STR功能是否正常工作
"""

import os
import sys
import time
import tempfile
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.cookie_utils import (
    parse_cookie_string,
    validate_cookie_completeness,
    check_cookie_freshness,
    update_env_cookies_safely,
    get_cookie_status_report
)
from config.logger_config import get_logger

# 获取专用日志记录器
logger = get_logger("test", "cookie_update")


def test_cookie_parsing():
    """测试Cookie解析功能"""
    print("🧪 测试Cookie解析功能...")
    
    test_cookie = "unb=1234567890; _m_h5_tk=token123_1672531200000; cookie2=session123; cna=client123; sgcookie=secure123"
    
    cookies = parse_cookie_string(test_cookie)
    
    assert len(cookies) == 5, f"应该解析出5个cookie，实际: {len(cookies)}"
    assert cookies['unb'] == '1234567890', "unb字段解析错误"
    assert cookies['_m_h5_tk'] == 'token123_1672531200000', "_m_h5_tk字段解析错误"
    
    print("✅ Cookie解析测试通过")


def test_cookie_validation():
    """测试Cookie验证功能"""
    print("🧪 测试Cookie验证功能...")
    
    # 完整的cookie
    complete_cookie = "unb=1234567890; _m_h5_tk=token123_1672531200000; cookie2=session123; cna=client123; sgcookie=secure123"
    cookies = parse_cookie_string(complete_cookie)
    is_complete, missing = validate_cookie_completeness(cookies)
    
    assert is_complete, f"完整cookie应该通过验证，缺失字段: {missing}"
    
    # 不完整的cookie
    incomplete_cookie = "unb=1234567890; _m_h5_tk=token123"
    cookies = parse_cookie_string(incomplete_cookie)
    is_complete, missing = validate_cookie_completeness(cookies)
    
    assert not is_complete, "不完整cookie应该验证失败"
    assert len(missing) > 0, "应该检测到缺失字段"
    
    print("✅ Cookie验证测试通过")


def test_cookie_freshness():
    """测试Cookie新鲜度检测"""
    print("🧪 测试Cookie新鲜度检测...")
    
    # 创建新鲜的cookie（当前时间戳）
    current_timestamp = int(time.time() * 1000)
    fresh_cookie = f"_m_h5_tk=token123_{current_timestamp}; unb=1234567890"
    cookies = parse_cookie_string(fresh_cookie)
    is_fresh, age_hours = check_cookie_freshness(cookies)
    
    assert is_fresh, "当前时间戳的cookie应该是新鲜的"
    assert age_hours is not None and age_hours < 1, f"cookie年龄应该小于1小时，实际: {age_hours}"
    
    # 创建过期的cookie（25小时前）
    old_timestamp = int((time.time() - 25 * 3600) * 1000)
    old_cookie = f"_m_h5_tk=token123_{old_timestamp}; unb=1234567890"
    cookies = parse_cookie_string(old_cookie)
    is_fresh, age_hours = check_cookie_freshness(cookies)
    
    assert not is_fresh, "25小时前的cookie应该是过期的"
    assert age_hours is not None and age_hours > 24, f"cookie年龄应该大于24小时，实际: {age_hours}"
    
    print("✅ Cookie新鲜度测试通过")


def test_env_update():
    """测试.env文件更新功能"""
    print("🧪 测试.env文件更新功能...")
    
    # 创建临时.env文件
    temp_dir = tempfile.mkdtemp()
    temp_env_path = os.path.join(temp_dir, '.env')
    
    # 写入初始内容
    initial_content = """# 测试环境配置
API_KEY=test_key
MODEL_NAME=test_model
COOKIES_STR=old_cookie=old_value
OTHER_CONFIG=test_value
"""
    
    with open(temp_env_path, 'w', encoding='utf-8') as f:
        f.write(initial_content)
    
    # 模拟当前工作目录为临时目录
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    
    try:
        # 测试更新功能
        test_cookie = "unb=1234567890; _m_h5_tk=token123_1672531200000; cookie2=session123; cna=client123; sgcookie=secure123"
        
        success = update_env_cookies_safely(test_cookie, create_backup=True)
        assert success, "Cookie更新应该成功"
        
        # 验证文件内容
        with open(temp_env_path, 'r', encoding='utf-8') as f:
            updated_content = f.read()
        
        assert test_cookie in updated_content, "新cookie应该在文件中"
        assert "old_cookie=old_value" not in updated_content, "旧cookie应该被替换"
        assert "API_KEY=test_key" in updated_content, "其他配置应该保持不变"
        
        # 检查备份文件是否创建
        backup_files = [f for f in os.listdir(temp_dir) if f.startswith('.env.backup.')]
        assert len(backup_files) > 0, "应该创建备份文件"
        
        print("✅ .env文件更新测试通过")
        
    finally:
        # 恢复原始工作目录
        os.chdir(original_cwd)
        
        # 清理临时文件
        import shutil
        shutil.rmtree(temp_dir)


def test_status_report():
    """测试状态报告功能"""
    print("🧪 测试状态报告功能...")
    
    test_cookie = "unb=1234567890; _m_h5_tk=token123_1672531200000; cookie2=session123; cna=client123; sgcookie=secure123"
    
    report = get_cookie_status_report(test_cookie)
    
    # 验证报告字段
    required_fields = ['cookie_count', 'is_complete', 'missing_fields', 'is_fresh', 'user_id', 'has_token', 'has_session']
    for field in required_fields:
        assert field in report, f"状态报告缺少字段: {field}"
    
    assert report['cookie_count'] == 5, f"cookie数量应该是5，实际: {report['cookie_count']}"
    assert report['user_id'] == '1234567890', f"用户ID应该是1234567890，实际: {report['user_id']}"
    assert report['has_token'], "应该检测到token"
    assert report['has_session'], "应该检测到session"
    
    print("✅ 状态报告测试通过")


def run_integration_test():
    """运行集成测试"""
    print("🧪 运行集成测试...")
    
    try:
        # 如果存在真实的API客户端，测试自动更新功能
        from apis.xianyu_apis import XianyuAPIClient
        
        # 注意：这里只测试初始化，不进行实际API调用
        client = XianyuAPIClient()
        
        # 验证client有update_env_cookies方法
        assert hasattr(client, 'update_env_cookies'), "API客户端应该有update_env_cookies方法"
        assert hasattr(client, 'clear_duplicate_cookies'), "API客户端应该有clear_duplicate_cookies方法"
        
        print("✅ 集成测试通过")
        
    except ImportError as e:
        print(f"⚠️ 集成测试跳过（缺少依赖）: {e}")
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        raise


def main():
    """主测试函数"""
    print("🚀 开始Cookie自动更新功能测试")
    print("=" * 50)
    
    tests = [
        test_cookie_parsing,
        test_cookie_validation, 
        test_cookie_freshness,
        test_env_update,
        test_status_report,
        run_integration_test
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"❌ 测试失败: {test_func.__name__}")
            print(f"   错误信息: {e}")
            logger.error(f"测试失败 {test_func.__name__}: {e}")
    
    print("=" * 50)
    print(f"🎯 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！Cookie自动更新功能正常工作")
        return 0
    else:
        print("💥 部分测试失败，请检查错误信息")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code) 