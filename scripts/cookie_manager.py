#!/usr/bin/env python3
"""
闲鱼Cookie管理工具
提供命令行接口用于管理、验证和更新闲鱼Cookie
"""

import os
import sys
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.cookie_utils import (
    parse_cookie_string, 
    validate_cookie_completeness,
    check_cookie_freshness,
    update_env_cookies_safely,
    get_cookie_status_report,
    backup_env_file
)
from config.logger_config import get_logger

# 获取专用日志记录器
logger = get_logger("script", "cookie_manager")


def print_banner():
    """打印工具横幅"""
    banner = """
╔══════════════════════════════════════════════════════╗
║              🍪 闲鱼Cookie管理工具                      ║
║          智能闲鱼客服机器人系统 - Cookie管理器            ║
╚══════════════════════════════════════════════════════╝
"""
    print(banner)


def cmd_status(args):
    """显示当前Cookie状态"""
    print("📊 Cookie状态检查...")
    
    try:
        # 从.env文件读取Cookie
        env_path = find_env_file()
        if not env_path:
            print("❌ 无法找到.env文件")
            return
        
        cookie_str = read_cookies_from_env(env_path)
        if not cookie_str:
            print("❌ .env文件中未找到COOKIES_STR")
            return
        
        # 生成状态报告
        report = get_cookie_status_report(cookie_str)
        
        print(f"\n🔍 Cookie状态报告:")
        print(f"  Cookie数量: {report['cookie_count']}")
        print(f"  完整性: {'✅ 完整' if report['is_complete'] else '❌ 不完整'}")
        
        if report['missing_fields']:
            print(f"  缺失字段: {', '.join(report['missing_fields'])}")
        
        print(f"  新鲜度: {'✅ 新鲜' if report['is_fresh'] else '⚠️ 可能过期'}")
        
        if report['age_hours'] is not None:
            print(f"  Cookie年龄: {report['age_hours']:.2f}小时")
        
        print(f"  用户ID: {report['user_id']}")
        print(f"  有Token: {'✅' if report['has_token'] else '❌'}")
        print(f"  有会话: {'✅' if report['has_session'] else '❌'}")
        
        # 健康度评分
        health_score = calculate_health_score(report)
        print(f"\n🎯 Cookie健康度: {health_score}/100")
        
        if health_score >= 80:
            print("✅ Cookie状态良好")
        elif health_score >= 60:
            print("⚠️ Cookie状态一般，建议关注")
        else:
            print("❌ Cookie状态较差，建议更新")
        
    except Exception as e:
        print(f"❌ 状态检查失败: {e}")
        logger.error(f"Cookie状态检查失败: {e}")


def cmd_update(args):
    """更新Cookie"""
    print("🔄 更新Cookie...")
    
    cookie_str = None
    
    if args.file:
        # 从文件读取
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                cookie_str = f.read().strip()
            print(f"📁 从文件读取Cookie: {args.file}")
        except Exception as e:
            print(f"❌ 读取文件失败: {e}")
            return
    
    elif args.cookie:
        # 从命令行参数读取
        cookie_str = args.cookie
        print("📝 使用命令行提供的Cookie")
    
    else:
        # 交互式输入
        print("请输入新的Cookie字符串 (格式: key1=value1; key2=value2):")
        print("可以从浏览器开发者工具的Network面板中复制")
        cookie_str = input("Cookie: ").strip()
    
    if not cookie_str:
        print("❌ Cookie字符串为空")
        return
    
    # 验证Cookie
    cookies = parse_cookie_string(cookie_str)
    is_complete, missing_fields = validate_cookie_completeness(cookies)
    
    print(f"\n🔍 Cookie验证结果:")
    print(f"  解析到 {len(cookies)} 个Cookie项")
    print(f"  完整性: {'✅ 完整' if is_complete else '❌ 不完整'}")
    
    if missing_fields:
        print(f"  ⚠️ 缺失关键字段: {', '.join(missing_fields)}")
        if not args.force:
            confirm = input("是否仍要继续更新? (y/N): ").lower().strip()
            if confirm != 'y':
                print("❌ 更新已取消")
                return
    
    # 执行更新
    try:
        success = update_env_cookies_safely(
            cookie_str, 
            create_backup=not args.no_backup
        )
        
        if success:
            print("✅ Cookie更新成功!")
            if not args.no_backup:
                print("📦 已自动创建.env文件备份")
        else:
            print("❌ Cookie更新失败")
            
    except Exception as e:
        print(f"❌ 更新过程中发生错误: {e}")
        logger.error(f"Cookie更新失败: {e}")


def cmd_backup(args):
    """备份.env文件"""
    print("📦 备份.env文件...")
    
    try:
        env_path = find_env_file()
        if not env_path:
            print("❌ 无法找到.env文件")
            return
        
        backup_path = backup_env_file(env_path)
        if backup_path:
            print(f"✅ 备份成功: {backup_path}")
        else:
            print("❌ 备份失败")
            
    except Exception as e:
        print(f"❌ 备份过程中发生错误: {e}")
        logger.error(f"备份失败: {e}")


def cmd_validate(args):
    """验证Cookie格式和完整性"""
    print("🔍 验证Cookie...")
    
    cookie_str = None
    
    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                cookie_str = f.read().strip()
        except Exception as e:
            print(f"❌ 读取文件失败: {e}")
            return
    elif args.cookie:
        cookie_str = args.cookie
    else:
        print("请输入要验证的Cookie字符串:")
        cookie_str = input("Cookie: ").strip()
    
    if not cookie_str:
        print("❌ Cookie字符串为空")
        return
    
    # 解析和验证
    cookies = parse_cookie_string(cookie_str)
    is_complete, missing_fields = validate_cookie_completeness(cookies)
    is_fresh, age_hours = check_cookie_freshness(cookies)
    
    print(f"\n📋 验证结果:")
    print(f"  Cookie数量: {len(cookies)}")
    print(f"  格式: {'✅ 有效' if len(cookies) > 0 else '❌ 无效'}")
    print(f"  完整性: {'✅ 完整' if is_complete else '❌ 不完整'}")
    print(f"  新鲜度: {'✅ 新鲜' if is_fresh else '⚠️ 可能过期'}")
    
    if missing_fields:
        print(f"  缺失字段: {', '.join(missing_fields)}")
    
    if age_hours is not None:
        print(f"  Cookie年龄: {age_hours:.2f}小时")
    
    # 显示关键字段
    key_fields = ['unb', '_m_h5_tk', 'cookie2', 'cna']
    print(f"\n🔑 关键字段检查:")
    for field in key_fields:
        value = cookies.get(field, '')
        status = "✅" if value else "❌"
        display_value = value[:20] + "..." if len(value) > 20 else value
        print(f"  {field}: {status} {display_value}")


def find_env_file() -> str:
    """查找.env文件"""
    possible_paths = [
        os.path.join(os.getcwd(), '.env'),
        os.path.join(project_root, '.env'),
        os.path.join(os.path.expanduser('~'), '.env')
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None


def read_cookies_from_env(env_path: str) -> str:
    """从.env文件读取Cookie"""
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('COOKIES_STR='):
                    return line[12:].strip()  # 去掉'COOKIES_STR='前缀
        return ""
    except Exception as e:
        logger.error(f"读取.env文件失败: {e}")
        return ""


def calculate_health_score(report: dict) -> int:
    """计算Cookie健康度评分"""
    score = 0
    
    # 完整性 (40分)
    if report['is_complete']:
        score += 40
    else:
        # 根据缺失字段数量减分
        missing_count = len(report['missing_fields'])
        score += max(0, 40 - missing_count * 10)
    
    # 新鲜度 (30分)
    if report['is_fresh']:
        score += 30
    elif report['age_hours'] is not None:
        if report['age_hours'] < 48:  # 48小时内
            score += 20
        elif report['age_hours'] < 72:  # 72小时内
            score += 10
    
    # 关键组件 (30分)
    if report['has_token']:
        score += 15
    if report['has_session']:
        score += 15
    
    return min(100, score)


def main():
    """主函数"""
    print_banner()
    
    parser = argparse.ArgumentParser(
        description="闲鱼Cookie管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s status                          # 显示当前Cookie状态
  %(prog)s update                          # 交互式更新Cookie
  %(prog)s update -c "key=value; key2=value2"  # 直接更新Cookie
  %(prog)s update -f cookies.txt           # 从文件更新Cookie
  %(prog)s validate -c "key=value"         # 验证Cookie格式
  %(prog)s backup                          # 备份.env文件
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # status命令
    parser_status = subparsers.add_parser('status', help='显示Cookie状态')
    
    # update命令
    parser_update = subparsers.add_parser('update', help='更新Cookie')
    parser_update.add_argument('-c', '--cookie', help='Cookie字符串')
    parser_update.add_argument('-f', '--file', help='从文件读取Cookie')
    parser_update.add_argument('--no-backup', action='store_true', help='不创建备份')
    parser_update.add_argument('--force', action='store_true', help='强制更新（忽略验证警告）')
    
    # validate命令
    parser_validate = subparsers.add_parser('validate', help='验证Cookie')
    parser_validate.add_argument('-c', '--cookie', help='Cookie字符串')
    parser_validate.add_argument('-f', '--file', help='从文件读取Cookie')
    
    # backup命令
    parser_backup = subparsers.add_parser('backup', help='备份.env文件')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 执行对应命令
    if args.command == 'status':
        cmd_status(args)
    elif args.command == 'update':
        cmd_update(args)
    elif args.command == 'validate':
        cmd_validate(args)
    elif args.command == 'backup':
        cmd_backup(args)


if __name__ == '__main__':
    main() 