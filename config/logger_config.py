"""
日志配置模块
使用loguru进行统一的日志管理，支持文件轮转、级别过滤等功能
"""

import os
import sys
from loguru import logger
from typing import Optional


class LoggerConfig:
    """日志配置管理器"""
    
    def __init__(self):
        """初始化日志配置"""
        self.log_dir = "logs"
        self._ensure_log_dir()
        self._setup_loggers()
    
    def _ensure_log_dir(self):
        """确保日志目录存在"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
    
    def _setup_loggers(self):
        """设置日志记录器"""
        # 清除默认的控制台输出
        logger.remove()
        
        # 添加控制台输出（彩色）
        logger.add(
            sys.stdout,
            colorize=True,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                   "<level>{message}</level>",
            level="INFO"
        )
        
        # 添加主日志文件（所有级别）
        logger.add(
            os.path.join(self.log_dir, "main.log"),
            rotation="10 MB",
            retention="10 days",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
            level="DEBUG",
            encoding="utf-8"
        )
        
        # 添加错误日志文件（仅错误和警告）
        logger.add(
            os.path.join(self.log_dir, "error.log"),
            rotation="5 MB",
            retention="30 days",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
            level="WARNING",
            encoding="utf-8"
        )
        
        # 添加Web UI专用日志文件
        logger.add(
            os.path.join(self.log_dir, "web_ui.log"),
            rotation="5 MB",
            retention="7 days",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
            level="DEBUG",
            encoding="utf-8",
            filter=lambda record: "web" in record["name"].lower() or "flask" in record["name"].lower()
        )
        
        # 添加代理专用日志文件
        logger.add(
            os.path.join(self.log_dir, "agents.log"),
            rotation="5 MB",
            retention="7 days",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
            level="DEBUG",
            encoding="utf-8",
            filter=lambda record: "agent" in record["name"].lower()
        )
        
        logger.info("日志系统初始化完成")
    
    def get_web_logger(self, name: str):
        """获取Web模块专用的日志记录器"""
        return logger.bind(name=f"web.{name}")
    
    def get_agent_logger(self, name: str):
        """获取Agent模块专用的日志记录器"""
        return logger.bind(name=f"agent.{name}")
    
    def get_api_logger(self, name: str):
        """获取API模块专用的日志记录器"""
        return logger.bind(name=f"api.{name}")
    
    def get_core_logger(self, name: str):
        """获取核心模块专用的日志记录器"""
        return logger.bind(name=f"core.{name}")


# 全局日志配置实例
logger_config = LoggerConfig()


def get_logger(module_type: str, name: str):
    """
    获取指定模块类型的日志记录器
    
    Args:
        module_type: 模块类型 (web, agent, api, core)
        name: 具体模块名称
        
    Returns:
        配置好的日志记录器
    """
    if module_type == "web":
        return logger_config.get_web_logger(name)
    elif module_type == "agent":
        return logger_config.get_agent_logger(name)
    elif module_type == "api":
        return logger_config.get_api_logger(name)
    elif module_type == "core":
        return logger_config.get_core_logger(name)
    else:
        return logger.bind(name=f"{module_type}.{name}")


def setup_winston_style_logging():
    """
    设置类似Winston的日志记录风格
    为了满足用户的Winston日志需求
    """
    # 添加类似Winston的日志级别和格式
    winston_format = "{time:YYYY-MM-DD HH:mm:ss} [{level}] {name} - {message}"
    
    # 添加Winston风格的日志文件
    logger.add(
        os.path.join(logger_config.log_dir, "winston_style.log"),
        rotation="10 MB",
        retention="10 days",
        format=winston_format,
        level="DEBUG",
        encoding="utf-8"
    )
    
    logger.info("Winston风格日志记录器已启用") 