"""
认证路由模块
处理用户登录、注销等认证功能
"""

import json
import os
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import check_password_hash
from config.logger_config import get_logger

# 获取专用日志记录器
logger = get_logger("web", "auth_routes")

# 创建蓝图
auth_bp = Blueprint('auth', __name__)


def _load_web_ui_config() -> dict:
    """加载Web UI配置文件"""
    config_file = "web_ui_config.json"
    default_config = {
        "auth": {
            "username": "admin",
            "password": "admin123"
        }
    }
    
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return default_config
    except Exception as e:
        logger.error(f"读取配置文件失败: {e}")
        return default_config


@auth_bp.route('/login', methods=['GET'])
def login_page():
    """登录页面"""
    try:
        if session.get('logged_in'):
            return redirect(url_for('main.index'))
        return render_template('login.html')
        
    except Exception as e:
        logger.error(f"登录页面异常: {e}")
        return render_template('error.html', error="登录页面加载失败"), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """处理登录请求"""
    try:
        # 支持JSON和表单数据两种格式
        if request.is_json:
            data = request.get_json() or {}
        else:
            data = request.form.to_dict() or {}
            
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return jsonify({
                'status': 'error',
                'message': '用户名和密码不能为空'
            }), 400
        
        # 加载配置
        config = _load_web_ui_config()
        expected_username = config['auth']['username']
        expected_password = config['auth']['password']
        
        # 验证用户名和密码
        if username == expected_username and password == expected_password:
            session['logged_in'] = True
            session['username'] = username
            session.permanent = True
            
            logger.info(f"用户 {username} 登录成功")
            
            # 如果是表单提交，重定向到首页
            if not request.is_json:
                return redirect(url_for('main.index'))
            
            return jsonify({
                'status': 'success',
                'message': '登录成功'
            })
        else:
            logger.warning(f"用户 {username} 登录失败：用户名或密码错误")
            
            # 如果是表单提交，重定向回登录页面
            if not request.is_json:
                return render_template('login.html', error='用户名或密码错误')
            
            return jsonify({
                'status': 'error',
                'message': '用户名或密码错误'
            }), 401
            
    except Exception as e:
        logger.error(f"登录处理异常: {e}")
        return jsonify({
            'status': 'error',
            'message': '登录处理失败'
        }), 500


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """处理注销请求"""
    try:
        username = session.get('username', 'unknown')
        session.clear()
        
        logger.info(f"用户 {username} 已注销")
        return jsonify({
            'status': 'success',
            'message': '注销成功'
        })
        
    except Exception as e:
        logger.error(f"注销处理异常: {e}")
        return jsonify({
            'status': 'error',
            'message': '注销处理失败'
        }), 500


@auth_bp.route('/check', methods=['GET'])
def check_auth():
    """检查认证状态"""
    try:
        if session.get('logged_in'):
            return jsonify({
                'status': 'success',
                'authenticated': True,
                'username': session.get('username')
            })
        else:
            return jsonify({
                'status': 'success',
                'authenticated': False
            })
            
    except Exception as e:
        logger.error(f"认证检查异常: {e}")
        return jsonify({
            'status': 'error',
            'message': '认证检查失败'
        }), 500 