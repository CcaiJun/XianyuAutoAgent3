"""
Cookie管理工具模块
提供Cookie相关的实用工具函数，包括格式化、验证、更新等功能
"""

import os
import re
import time
from typing import Dict, List, Optional, Tuple
from config.logger_config import get_logger

# 获取专用日志记录器
logger = get_logger("utils", "cookie")


def parse_cookie_string(cookie_str: str) -> Dict[str, str]:
    """
    解析Cookie字符串为字典
    
    Args:
        cookie_str: Cookie字符串，格式如 "key1=value1; key2=value2"
        
    Returns:
        Cookie字典
    """
    cookies = {}
    if not cookie_str:
        return cookies
    
    try:
        for cookie in cookie_str.split(';'):
            if '=' in cookie:
                key, value = cookie.split('=', 1)
                cookies[key.strip()] = value.strip()
    except Exception as e:
        logger.warning(f"解析Cookie字符串失败: {e}")
    
    return cookies


def format_cookies_to_string(cookies: Dict[str, str]) -> str:
    """
    将Cookie字典格式化为字符串
    
    Args:
        cookies: Cookie字典
        
    Returns:
        格式化的Cookie字符串
    """
    if not cookies:
        return ""
    
    return '; '.join([f"{key}={value}" for key, value in cookies.items()])


def validate_cookie_completeness(cookies: Dict[str, str]) -> Tuple[bool, List[str]]:
    """
    验证闲鱼Cookie的完整性
    
    Args:
        cookies: Cookie字典
        
    Returns:
        (是否完整, 缺失的关键字段列表)
    """
    # 闲鱼必需的关键Cookie字段
    required_fields = [
        'unb',          # 用户唯一标识
        '_m_h5_tk',     # H5 Token
        'cookie2',      # 会话标识
        'cna',          # 客户端标识
        'sgcookie'      # 安全Cookie
    ]
    
    # 重要但非必需的字段
    important_fields = [
        'x',            # 扩展信息
        't',            # 时间戳
        'tracknick',    # 用户昵称
        'XSRF-TOKEN'    # CSRF保护
    ]
    
    missing_required = [field for field in required_fields if field not in cookies]
    missing_important = [field for field in important_fields if field not in cookies]
    
    is_complete = len(missing_required) == 0
    
    if missing_required:
        logger.warning(f"缺少必需的Cookie字段: {missing_required}")
    
    if missing_important:
        logger.debug(f"缺少重要的Cookie字段: {missing_important}")
    
    return is_complete, missing_required


def check_cookie_freshness(cookies: Dict[str, str]) -> Tuple[bool, Optional[float]]:
    """
    检查Cookie的新鲜度
    
    Args:
        cookies: Cookie字典
        
    Returns:
        (是否新鲜, Cookie年龄小时数)
    """
    try:
        # 从_m_h5_tk中提取时间戳
        h5_tk = cookies.get('_m_h5_tk', '')
        if '_' in h5_tk:
            timestamp_str = h5_tk.split('_')[1]
            if timestamp_str.isdigit():
                cookie_timestamp = int(timestamp_str) / 1000  # 转换为秒
                current_timestamp = time.time()
                age_hours = (current_timestamp - cookie_timestamp) / 3600
                
                # 一般认为超过24小时的Cookie可能需要刷新
                is_fresh = age_hours < 24
                
                logger.debug(f"Cookie年龄: {age_hours:.2f}小时, 新鲜度: {'新鲜' if is_fresh else '过期'}")
                return is_fresh, age_hours
    
    except Exception as e:
        logger.warning(f"检查Cookie新鲜度失败: {e}")
    
    return True, None  # 无法确定时默认认为是新鲜的


def backup_env_file(env_path: str) -> Optional[str]:
    """
    备份.env文件
    
    Args:
        env_path: .env文件路径
        
    Returns:
        备份文件路径，失败返回None
    """
    try:
        if not os.path.exists(env_path):
            logger.warning(f".env文件不存在: {env_path}")
            return None
        
        # 生成备份文件名（包含时间戳）
        timestamp = int(time.time())
        backup_path = f"{env_path}.backup.{timestamp}"
        
        # 复制文件内容
        with open(env_path, 'r', encoding='utf-8') as src:
            content = src.read()
        
        with open(backup_path, 'w', encoding='utf-8') as dst:
            dst.write(content)
        
        logger.info(f"✅ .env文件备份成功: {backup_path}")
        return backup_path
        
    except Exception as e:
        logger.error(f"备份.env文件失败: {e}")
        return None


def cleanup_old_backups(env_dir: str, keep_count: int = 5):
    """
    清理旧的.env备份文件
    
    Args:
        env_dir: .env文件所在目录
        keep_count: 保留的备份文件数量
    """
    try:
        # 查找所有备份文件
        backup_files = []
        for filename in os.listdir(env_dir):
            if filename.startswith('.env.backup.'):
                backup_path = os.path.join(env_dir, filename)
                backup_files.append((backup_path, os.path.getmtime(backup_path)))
        
        # 按修改时间排序（新的在前）
        backup_files.sort(key=lambda x: x[1], reverse=True)
        
        # 删除多余的备份文件
        if len(backup_files) > keep_count:
            for backup_path, _ in backup_files[keep_count:]:
                try:
                    os.remove(backup_path)
                    logger.debug(f"删除旧备份文件: {backup_path}")
                except Exception as e:
                    logger.warning(f"删除备份文件失败 {backup_path}: {e}")
        
        if len(backup_files) > keep_count:
            logger.info(f"清理了 {len(backup_files) - keep_count} 个旧备份文件")
            
    except Exception as e:
        logger.warning(f"清理备份文件失败: {e}")


def update_env_cookies_safely(cookie_str: str, create_backup: bool = True) -> bool:
    """
    安全地更新.env文件中的COOKIES_STR
    
    Args:
        cookie_str: 新的Cookie字符串
        create_backup: 是否创建备份
        
    Returns:
        更新是否成功
    """
    try:
        # 验证Cookie格式
        cookies = parse_cookie_string(cookie_str)
        is_complete, missing_fields = validate_cookie_completeness(cookies)
        
        if not is_complete:
            logger.warning(f"Cookie不完整，缺少字段: {missing_fields}")
            # 但仍然继续更新，只是发出警告
        
        # 查找.env文件
        possible_paths = [
            os.path.join(os.getcwd(), '.env'),
            os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'),
            os.path.join(os.path.expanduser('~'), '.env')
        ]
        
        env_path = None
        for path in possible_paths:
            if os.path.exists(path):
                env_path = path
                break
        
        if not env_path:
            logger.error("无法找到.env文件")
            return False
        
        # 创建备份
        if create_backup:
            backup_path = backup_env_file(env_path)
            if backup_path:
                # 清理旧备份
                cleanup_old_backups(os.path.dirname(env_path))
        
        # 读取并更新.env文件
        with open(env_path, 'r', encoding='utf-8') as f:
            env_content = f.read()
        
        # 处理特殊字符
        escaped_cookie_str = cookie_str.replace('\\', '\\\\').replace('$', '\\$')
        
        if 'COOKIES_STR=' in env_content:
            # 更新现有配置
            new_env_content = re.sub(
                r'COOKIES_STR=.*?(?=\n|$)',
                f'COOKIES_STR={escaped_cookie_str}',
                env_content,
                flags=re.MULTILINE
            )
        else:
            # 添加新配置
            if not env_content.endswith('\n'):
                env_content += '\n'
            new_env_content = env_content + f'COOKIES_STR={escaped_cookie_str}\n'
        
        # 写回文件
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(new_env_content)
        
        logger.info(f"✅ 成功更新.env文件中的COOKIES_STR ({len(cookies)} 个cookies)")
        
        # 检查Cookie新鲜度
        is_fresh, age_hours = check_cookie_freshness(cookies)
        if age_hours is not None:
            logger.info(f"🕒 Cookie年龄: {age_hours:.2f}小时 ({'新鲜' if is_fresh else '可能需要刷新'})")
        
        return True
        
    except Exception as e:
        logger.error(f"安全更新.env文件失败: {e}")
        return False


def get_cookie_status_report(cookie_str: str) -> Dict[str, any]:
    """
    生成Cookie状态报告
    
    Args:
        cookie_str: Cookie字符串
        
    Returns:
        包含完整状态信息的字典
    """
    cookies = parse_cookie_string(cookie_str)
    is_complete, missing_fields = validate_cookie_completeness(cookies)
    is_fresh, age_hours = check_cookie_freshness(cookies)
    
    return {
        "cookie_count": len(cookies),
        "is_complete": is_complete,
        "missing_fields": missing_fields,
        "is_fresh": is_fresh,
        "age_hours": age_hours,
        "user_id": cookies.get('unb', 'unknown'),
        "has_token": bool(cookies.get('_m_h5_tk')),
        "has_session": bool(cookies.get('cookie2')),
        "timestamp": time.time()
    } 