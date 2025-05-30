"""
设备相关工具模块
提供设备ID生成、UUID生成、消息ID生成等设备标识相关功能
"""

import time
import hashlib
import random
import string
from typing import Dict
from config.logger_config import get_logger

# 获取专用日志记录器
logger = get_logger("utils", "device")


def trans_cookies(cookies_str: str) -> Dict[str, str]:
    """
    解析cookie字符串为字典格式
    
    Args:
        cookies_str: cookie字符串，格式如 "key1=value1; key2=value2"
        
    Returns:
        解析后的cookie字典
    """
    cookies = {}
    logger.debug(f"开始解析cookie字符串，长度: {len(cookies_str)} 字符")
    
    for cookie in cookies_str.split("; "):
        try:
            parts = cookie.split('=', 1)
            if len(parts) == 2:
                cookies[parts[0]] = parts[1]
        except Exception as e:
            logger.warning(f"解析cookie部分失败: {cookie}, 错误: {e}")
            continue
    
    logger.debug(f"cookie解析完成，共解析出 {len(cookies)} 个键值对")
    return cookies


def generate_uuid() -> str:
    """
    生成32位随机UUID字符串
    使用小写字母和数字组合
    
    Returns:
        32位随机UUID字符串
    """
    uuid = ''.join(random.choices(string.ascii_lowercase + string.digits, k=32))
    logger.debug(f"生成UUID: {uuid[:8]}...{uuid[-8:]}")
    return uuid


def generate_mid() -> str:
    """
    生成消息ID
    格式为：时间戳毫秒 + 空格 + 5位随机数
    
    Returns:
        消息ID字符串
    """
    timestamp = str(int(time.time() * 1000))
    random_num = str(random.randint(10000, 99999))
    mid = timestamp + " " + random_num
    
    logger.debug(f"生成消息ID: {mid}")
    return mid


def generate_device_id(unb: str) -> str:
    """
    根据用户UNB生成设备ID
    使用MD5哈希确保同一用户生成相同的设备ID
    
    Args:
        unb: 用户唯一标识符
        
    Returns:
        32位MD5设备ID
    """
    # 构造基础字符串，包含固定前缀、用户标识和当前时间
    base_string = f"xianyu_device_{unb}_{int(time.time())}"
    
    # 计算MD5哈希
    hash_object = hashlib.md5(base_string.encode())
    device_id = hash_object.hexdigest()
    
    logger.info(f"为用户 {unb} 生成设备ID: {device_id[:8]}...{device_id[-8:]}")
    return device_id


def generate_random_user_agent() -> str:
    """
    生成随机的用户代理字符串
    模拟不同的浏览器和操作系统
    
    Returns:
        随机用户代理字符串
    """
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 DingTalk(2.1.5)",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
    ]
    
    selected_ua = random.choice(user_agents)
    logger.debug(f"选择用户代理: {selected_ua}")
    return selected_ua


def validate_device_id(device_id: str) -> bool:
    """
    验证设备ID格式是否正确
    
    Args:
        device_id: 待验证的设备ID
        
    Returns:
        验证结果，True表示格式正确
    """
    if not device_id:
        return False
    
    # 检查长度（MD5哈希为32位）
    if len(device_id) != 32:
        return False
    
    # 检查是否为有效的十六进制字符串
    try:
        int(device_id, 16)
        return True
    except ValueError:
        return False


def get_device_fingerprint() -> Dict[str, str]:
    """
    获取设备指纹信息
    用于构建更真实的设备标识
    
    Returns:
        设备指纹信息字典
    """
    fingerprint = {
        "screen_resolution": random.choice(["1920x1080", "1366x768", "1440x900", "1600x900"]),
        "timezone": "Asia/Shanghai",
        "language": "zh-CN",
        "platform": random.choice(["Win32", "MacIntel", "Linux x86_64"]),
        "webgl_vendor": random.choice(["Intel Inc.", "NVIDIA Corporation", "AMD"]),
        "canvas_fingerprint": generate_uuid()[:16]  # 简化的Canvas指纹
    }
    
    logger.debug(f"生成设备指纹: {fingerprint}")
    return fingerprint 