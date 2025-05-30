"""
数据验证工具模块
提供各种数据格式验证功能，确保数据完整性和安全性
"""

import re
import json
from typing import Any, Dict, List, Optional
from config.logger_config import get_logger
import os

# 获取专用日志记录器
logger = get_logger("utils", "validation")


def validate_email(email: str) -> bool:
    """
    验证邮箱地址格式
    
    Args:
        email: 邮箱地址字符串
        
    Returns:
        验证结果
    """
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    is_valid = bool(re.match(pattern, email))
    
    if not is_valid:
        logger.debug(f"邮箱格式验证失败: {email}")
    
    return is_valid


def validate_phone(phone: str) -> bool:
    """
    验证中国手机号码格式
    
    Args:
        phone: 手机号码字符串
        
    Returns:
        验证结果
    """
    if not phone:
        return False
    
    # 中国手机号码正则表达式
    pattern = r'^1[3-9]\d{9}$'
    is_valid = bool(re.match(pattern, phone))
    
    if not is_valid:
        logger.debug(f"手机号码格式验证失败: {phone}")
    
    return is_valid


def validate_json(json_str: str) -> bool:
    """
    验证JSON字符串格式
    
    Args:
        json_str: JSON字符串
        
    Returns:
        验证结果
    """
    if not json_str:
        return False
    
    try:
        json.loads(json_str)
        return True
    except json.JSONDecodeError as e:
        logger.debug(f"JSON格式验证失败: {e}")
        return False


def validate_url(url: str) -> bool:
    """
    验证URL格式
    
    Args:
        url: URL字符串
        
    Returns:
        验证结果
    """
    if not url:
        return False
    
    pattern = r'^https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?$'
    is_valid = bool(re.match(pattern, url))
    
    if not is_valid:
        logger.debug(f"URL格式验证失败: {url}")
    
    return is_valid


def validate_password(password: str, min_length: int = 8) -> Dict[str, Any]:
    """
    验证密码强度
    
    Args:
        password: 密码字符串
        min_length: 最小长度要求
        
    Returns:
        包含验证结果和详细信息的字典
    """
    result = {
        "valid": True,
        "messages": [],
        "score": 0
    }
    
    if not password:
        result["valid"] = False
        result["messages"].append("密码不能为空")
        return result
    
    # 长度检查
    if len(password) < min_length:
        result["valid"] = False
        result["messages"].append(f"密码长度至少需要{min_length}位")
    else:
        result["score"] += 1
    
    # 包含数字
    if re.search(r'\d', password):
        result["score"] += 1
    else:
        result["messages"].append("密码应包含数字")
    
    # 包含小写字母
    if re.search(r'[a-z]', password):
        result["score"] += 1
    else:
        result["messages"].append("密码应包含小写字母")
    
    # 包含大写字母
    if re.search(r'[A-Z]', password):
        result["score"] += 1
    else:
        result["messages"].append("密码应包含大写字母")
    
    # 包含特殊字符
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        result["score"] += 1
    else:
        result["messages"].append("密码应包含特殊字符")
    
    # 根据评分确定是否有效
    if result["score"] < 3:
        result["valid"] = False
    
    logger.debug(f"密码强度验证完成，评分: {result['score']}/5")
    return result


def validate_chinese_text(text: str) -> bool:
    """
    验证文本是否包含中文字符
    
    Args:
        text: 待验证的文本
        
    Returns:
        是否包含中文字符
    """
    if not text:
        return False
    
    chinese_pattern = r'[\u4e00-\u9fff]'
    has_chinese = bool(re.search(chinese_pattern, text))
    
    logger.debug(f"中文字符验证: {'包含' if has_chinese else '不包含'}")
    return has_chinese


def validate_user_input(text: str, max_length: int = 1000) -> Dict[str, Any]:
    """
    验证用户输入内容
    检查长度、特殊字符、潜在的安全风险等
    
    Args:
        text: 用户输入文本
        max_length: 最大长度限制
        
    Returns:
        验证结果字典
    """
    result = {
        "valid": True,
        "filtered_text": text,
        "warnings": []
    }
    
    if not text:
        result["valid"] = False
        result["warnings"].append("输入内容不能为空")
        return result
    
    # 长度检查
    if len(text) > max_length:
        result["valid"] = False
        result["warnings"].append(f"输入内容超过最大长度限制({max_length}字符)")
        return result
    
    # 检查潜在的SQL注入
    sql_patterns = [
        r'(union\s+select)',
        r'(drop\s+table)',
        r'(insert\s+into)',
        r'(delete\s+from)',
        r'(update\s+set)',
        r'(exec\s*\()',
        r'(script\s*>)'
    ]
    
    for pattern in sql_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            result["warnings"].append("检测到潜在的危险字符")
            logger.warning(f"检测到潜在危险输入: {pattern}")
            break
    
    # 检查XSS攻击
    xss_patterns = [
        r'<script[^>]*>',
        r'javascript:',
        r'on\w+\s*=',
        r'<iframe[^>]*>',
        r'<object[^>]*>'
    ]
    
    for pattern in xss_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            result["warnings"].append("检测到潜在的脚本注入")
            logger.warning(f"检测到潜在XSS攻击: {pattern}")
            break
    
    # 过滤HTML标签（保留纯文本）
    html_pattern = r'<[^>]+>'
    if re.search(html_pattern, text):
        result["filtered_text"] = re.sub(html_pattern, '', text)
        result["warnings"].append("已过滤HTML标签")
    
    logger.debug(f"用户输入验证完成，原长度: {len(text)}, 过滤后长度: {len(result['filtered_text'])}")
    return result


def validate_api_key(api_key: str) -> bool:
    """
    验证API密钥格式
    
    Args:
        api_key: API密钥字符串
        
    Returns:
        验证结果
    """
    if not api_key:
        return False
    
    # 基本格式检查：长度和字符
    if len(api_key) < 20:
        logger.debug("API密钥长度过短")
        return False
    
    # 检查是否包含有效字符
    valid_chars_pattern = r'^[A-Za-z0-9\-_\.]+$'
    if not re.match(valid_chars_pattern, api_key):
        logger.debug("API密钥包含无效字符")
        return False
    
    return True


def validate_cookies(cookies_str: str) -> Dict[str, Any]:
    """
    验证Cookies字符串格式
    
    Args:
        cookies_str: Cookies字符串
        
    Returns:
        验证结果字典
    """
    result = {
        "valid": True,
        "parsed_count": 0,
        "warnings": []
    }
    
    if not cookies_str:
        result["valid"] = False
        result["warnings"].append("Cookies字符串不能为空")
        return result
    
    # 尝试解析cookies
    cookies = {}
    for cookie in cookies_str.split("; "):
        if "=" in cookie:
            try:
                key, value = cookie.split('=', 1)
                cookies[key.strip()] = value.strip()
                result["parsed_count"] += 1
            except Exception:
                result["warnings"].append(f"无法解析cookie片段: {cookie}")
        else:
            result["warnings"].append(f"格式错误的cookie片段: {cookie}")
    
    # 检查必要的cookie字段
    required_fields = ['unb']  # 闲鱼必需的字段
    for field in required_fields:
        if field not in cookies:
            result["valid"] = False
            result["warnings"].append(f"缺少必需的cookie字段: {field}")
    
    logger.debug(f"Cookies验证完成，解析出{result['parsed_count']}个字段")
    return result


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除危险字符
    
    Args:
        filename: 原始文件名
        
    Returns:
        清理后的安全文件名
    """
    if not filename:
        return "untitled"
    
    # 移除危险字符
    dangerous_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(dangerous_chars, '_', filename)
    
    # 移除开头和结尾的点和空格
    sanitized = sanitized.strip('. ')
    
    # 限制长度
    if len(sanitized) > 255:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:251-len(ext)] + ext
    
    # 如果文件名为空，使用默认名称
    if not sanitized:
        sanitized = "untitled"
    
    logger.debug(f"文件名清理: {filename} -> {sanitized}")
    return sanitized 