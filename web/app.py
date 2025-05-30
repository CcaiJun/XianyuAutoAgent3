"""
Flask应用工厂模块
负责创建和配置Flask应用实例
"""

import os
import json
from datetime import timedelta
from typing import Tuple
from flask import Flask
from flask_socketio import SocketIO
from config.logger_config import get_logger
from config.config_manager import ConfigManager

# 获取专用日志记录器
logger = get_logger("web", "app")


def create_app(config_name: str = 'default') -> Tuple[Flask, SocketIO]:
    """
    创建Flask应用实例
    
    Args:
        config_name: 配置名称
        
    Returns:
        Flask应用和SocketIO实例的元组
    """
    try:
        # 创建Flask应用
        app = Flask(__name__)
        
        # 加载配置
        _load_config(app)
        
        # 创建SocketIO实例
        socketio = SocketIO(
            app, 
            cors_allowed_origins="*",
            async_mode='threading'
        )
        
        # 注册路由
        _register_routes(app)
        
        # 注册WebSocket事件
        _register_socketio_events(socketio)
        
        # 注册错误处理器
        _register_error_handlers(app)
        
        logger.info("Flask应用创建完成")
        return app, socketio
        
    except Exception as e:
        logger.error(f"创建Flask应用失败: {e}")
        raise


def _load_config(app: Flask):
    """加载应用配置"""
    try:
        config_manager = ConfigManager()
        
        # 加载Web UI配置
        web_ui_config = _load_web_ui_config()
        
        # 基础配置
        app.config['SECRET_KEY'] = web_ui_config['auth']['secret_key']
        app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(
            hours=web_ui_config['session']['permanent_session_lifetime_hours']
        )
        
        # 开发配置
        app.config['DEBUG'] = False
        app.config['TESTING'] = False
        
        # JSON配置
        app.config['JSON_AS_ASCII'] = False
        app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
        
        # 上传配置
        app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
        
        logger.info("应用配置加载完成")
        
    except Exception as e:
        logger.error(f"加载应用配置失败: {e}")
        raise


def _load_web_ui_config() -> dict:
    """加载Web UI配置文件"""
    config_file = "web_ui_config.json"
    default_config = {
        "auth": {
            "username": "admin",
            "password": "admin123",
            "secret_key": "xianyu_auto_agent_secret_key_change_this_in_production"
        },
        "session": {
            "permanent_session_lifetime_hours": 24
        }
    }
    
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        else:
            # 创建默认配置文件
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4, ensure_ascii=False)
            logger.info(f"已创建默认配置文件: {config_file}")
            return default_config
            
    except Exception as e:
        logger.error(f"读取配置文件失败，使用默认配置: {e}")
        return default_config


def _register_routes(app: Flask):
    """注册路由"""
    try:
        from .routes.auth_routes import auth_bp
        from .routes.api_routes import api_bp
        from .routes.main_routes import main_bp
        
        # 注册蓝图
        app.register_blueprint(auth_bp, url_prefix='/auth')
        app.register_blueprint(api_bp, url_prefix='/api')
        app.register_blueprint(main_bp, url_prefix='/')
        
        logger.info("路由注册完成")
        
    except Exception as e:
        logger.error(f"注册路由失败: {e}")
        raise


def _register_socketio_events(socketio: SocketIO):
    """注册WebSocket事件"""
    try:
        from .routes.websocket_routes import register_socketio_events, start_heartbeat_thread
        register_socketio_events(socketio)
        
        # 启动心跳线程
        start_heartbeat_thread()
        
        logger.info("WebSocket事件注册完成")
        
    except Exception as e:
        logger.error(f"注册WebSocket事件失败: {e}")
        raise


def _register_error_handlers(app: Flask):
    """注册错误处理器"""
    try:
        @app.errorhandler(404)
        def not_found_error(error):
            return {'error': '页面未找到', 'code': 404}, 404
        
        @app.errorhandler(500)
        def internal_error(error):
            return {'error': '服务器内部错误', 'code': 500}, 500
        
        @app.errorhandler(403)
        def forbidden_error(error):
            return {'error': '权限不足', 'code': 403}, 403
        
        @app.errorhandler(401)
        def unauthorized_error(error):
            return {'error': '未授权访问', 'code': 401}, 401
        
        logger.info("错误处理器注册完成")
        
    except Exception as e:
        logger.error(f"注册错误处理器失败: {e}")
        raise 