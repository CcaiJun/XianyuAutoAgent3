"""
配置管理器模块
与settings.py中的ConfigManager保持一致，提供简化的导入接口
"""

from .settings import ConfigManager, get_config

__all__ = ['ConfigManager', 'get_config'] 