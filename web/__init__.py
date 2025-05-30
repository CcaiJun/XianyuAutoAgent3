"""
Web模块
提供Web界面管理、API接口、WebSocket通信等功能
"""

from .app import create_app
from .manager import WebManager

__all__ = [
    'create_app',
    'WebManager'
]
