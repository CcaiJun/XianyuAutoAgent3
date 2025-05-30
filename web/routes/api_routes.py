"""
API路由模块
处理各种API请求和管理功能
"""

import os
import json
from flask import Blueprint, request, jsonify, session, current_app
from functools import wraps
from web.manager import WebManager
from config.logger_config import get_logger

# 获取专用日志记录器
logger = get_logger("web", "api_routes")

# 创建蓝图
api_bp = Blueprint('api', __name__)

# 全局Web管理器实例
web_manager = WebManager()


def login_required(f):
    """API登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return jsonify({'error': '需要登录', 'code': 401}), 401
        return f(*args, **kwargs)
    return decorated_function


# === 主程序控制 ===

@api_bp.route('/start', methods=['POST'])
@login_required
def start_main():
    """启动主程序"""
    try:
        result = web_manager.start_main_program()
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"启动主程序API异常: {e}")
        return jsonify({"status": "error", "message": f"启动失败: {str(e)}"}), 500


@api_bp.route('/stop', methods=['POST'])
@login_required
def stop_main():
    """停止主程序"""
    try:
        result = web_manager.stop_main_program()
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"停止主程序API异常: {e}")
        return jsonify({"status": "error", "message": f"停止失败: {str(e)}"}), 500


@api_bp.route('/status', methods=['GET'])
@login_required
def get_status():
    """获取程序状态"""
    try:
        process_status = web_manager.get_process_status()
        heartbeat_status = web_manager.get_heartbeat_status()
        
        return jsonify({
            "status": "success",
            "data": {
                "process": process_status,
                "heartbeat": heartbeat_status
            }
        })
        
    except Exception as e:
        logger.error(f"获取状态API异常: {e}")
        return jsonify({"status": "error", "message": f"获取状态失败: {str(e)}"}), 500


# === 日志管理 ===

@api_bp.route('/logs', methods=['GET'])
@login_required
def get_logs():
    """获取历史日志"""
    try:
        logs = web_manager.get_logs()
        return jsonify(logs)
        
    except Exception as e:
        logger.error(f"获取日志API异常: {e}")
        return jsonify({"status": "error", "message": f"获取日志失败: {str(e)}"}), 500


# === 提示词管理 (重新定义以匹配前端) ===

@api_bp.route('/prompts/<prompt_type>', methods=['GET', 'POST'])
@login_required
def manage_prompt_by_type(prompt_type):
    """按类型获取或更新提示词"""
    try:
        # 映射提示词类型到文件名
        prompt_files = {
            'classify': 'classify_prompt.txt',
            'price': 'price_prompt.txt',
            'tech': 'tech_prompt.txt',
            'default': 'default_prompt.txt'
        }
        
        if prompt_type not in prompt_files:
            return jsonify({"status": "error", "message": "无效的提示词类型"}), 400
        
        filename = prompt_files[prompt_type]
        filepath = os.path.join("config/prompts", filename)
        
        if request.method == 'GET':
            content = ""
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
            
            return jsonify({
                "status": "success",
                "data": {
                    "content": content,
                    "type": prompt_type,
                    "filename": filename
                }
            })
        
        elif request.method == 'POST':
            data = request.get_json()
            content = data.get('content', '')
            
            # 确保目录存在
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"提示词文件已更新: {filename}")
            return jsonify({"status": "success", "message": f"{prompt_type}提示词保存成功"})
            
    except Exception as e:
        logger.error(f"管理提示词API异常: {e}")
        return jsonify({"status": "error", "message": f"操作失败: {str(e)}"}), 500


# === 环境变量管理 ===

@api_bp.route('/env', methods=['GET', 'POST'])
@login_required
def manage_env():
    """获取或更新环境变量文件"""
    try:
        env_file = ".env"
        
        if request.method == 'GET':
            env_vars = {}
            if os.path.exists(env_file):
                with open(env_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and '=' in line and not line.startswith('#'):
                            key, value = line.split('=', 1)
                            env_vars[key.strip()] = value.strip()
            
            return jsonify(env_vars)
        
        elif request.method == 'POST':
            data = request.get_json()
            env_vars = data.get('env_vars', {})
            
            with open(env_file, 'w', encoding='utf-8') as f:
                for key, value in env_vars.items():
                    f.write(f"{key}={value}\n")
            
            logger.info("环境变量文件已更新")
            return jsonify({"status": "success", "message": "环境变量保存成功"})
            
    except Exception as e:
        logger.error(f"管理环境变量API异常: {e}")
        return jsonify({"status": "error", "message": f"操作失败: {str(e)}"}), 500


# === 配置管理 ===

@api_bp.route('/config', methods=['GET', 'POST'])
@login_required
def manage_config():
    """获取或更新配置信息"""
    try:
        if request.method == 'GET':
            # 获取环境变量配置信息
            config_info = {}
            
            # 读取.env文件
            env_file = ".env"
            if os.path.exists(env_file):
                with open(env_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and '=' in line and not line.startswith('#'):
                            key, value = line.split('=', 1)
                            config_info[key.strip()] = value.strip()
            
            return jsonify({
                "status": "success",
                "data": {
                    "apiKey": config_info.get("API_KEY", ""),
                    "cookiesStr": config_info.get("COOKIES_STR", ""),
                    "modelBaseUrl": config_info.get("MODEL_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
                    "modelName": config_info.get("MODEL_NAME", "qwen-max")
                }
            })
        
        elif request.method == 'POST':
            data = request.get_json()
            
            # 更新.env文件
            env_file = ".env"
            env_content = []
            
            # 添加必要的环境变量
            env_content.append(f"API_KEY={data.get('apiKey', '')}")
            env_content.append(f"COOKIES_STR={data.get('cookiesStr', '')}")
            env_content.append(f"MODEL_BASE_URL={data.get('modelBaseUrl', 'https://dashscope.aliyuncs.com/compatible-mode/v1')}")
            env_content.append(f"MODEL_NAME={data.get('modelName', 'qwen-max')}")
            
            # 添加其他默认配置
            env_content.append("TOGGLE_KEYWORDS=.")
            env_content.append("HEARTBEAT_INTERVAL=15")
            env_content.append("HEARTBEAT_TIMEOUT=5")
            env_content.append("TOKEN_REFRESH_INTERVAL=3600")
            env_content.append("TOKEN_RETRY_INTERVAL=300")
            env_content.append("MANUAL_MODE_TIMEOUT=3600")
            env_content.append("MESSAGE_EXPIRE_TIME=300000")
            
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(env_content))
            
            logger.info("环境变量配置已更新")
            return jsonify({"status": "success", "message": "配置保存成功，重启程序后生效"})
                
    except Exception as e:
        logger.error(f"管理配置API异常: {e}")
        return jsonify({"status": "error", "message": f"操作失败: {str(e)}"}), 500


# === 统计信息 ===

@api_bp.route('/statistics', methods=['GET'])
@login_required
def get_statistics():
    """获取统计信息"""
    try:
        # 获取Web管理器健康信息
        health_info = web_manager.get_health_info()
        
        # 添加其他统计信息
        stats = {
            "web_manager": health_info,
            "logs_count": len(web_manager.get_logs()),
            "session_info": {
                "user": session.get('username'),
                "logged_in": session.get('logged_in', False)
            }
        }
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"获取统计信息API异常: {e}")
        return jsonify({"status": "error", "message": f"获取统计失败: {str(e)}"}), 500


# === 健康检查 ===

@api_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查API（无需认证）"""
    try:
        health_info = web_manager.get_health_info()
        
        return jsonify({
            "status": "healthy",
            "timestamp": current_app.config.get('START_TIME', 'unknown'),
            "components": health_info
        })
        
    except Exception as e:
        logger.error(f"健康检查API异常: {e}")
        return jsonify({
            "status": "error", 
            "message": f"健康检查失败: {str(e)}"
        }), 500 