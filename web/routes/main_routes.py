"""
主要路由模块
处理页面渲染和基础功能
"""

from flask import Blueprint, render_template, redirect, url_for, session, request
from functools import wraps
from config.logger_config import get_logger

# 获取专用日志记录器
logger = get_logger("web", "main_routes")

# 创建蓝图
main_bp = Blueprint('main', __name__)


def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('auth.login_page'))
        return f(*args, **kwargs)
    return decorated_function


@main_bp.route('/')
def index():
    """首页"""
    try:
        if not session.get('logged_in'):
            return redirect(url_for('auth.login_page'))
        return render_template('index.html')
        
    except Exception as e:
        logger.error(f"首页访问异常: {e}")
        return render_template('error.html', error="页面加载失败"), 500


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """控制台页面"""
    try:
        return render_template('dashboard.html')
        
    except Exception as e:
        logger.error(f"控制台页面异常: {e}")
        return render_template('error.html', error="控制台加载失败"), 500


@main_bp.route('/logs')
@login_required
def logs_page():
    """日志页面"""
    try:
        return render_template('logs.html')
        
    except Exception as e:
        logger.error(f"日志页面异常: {e}")
        return render_template('error.html', error="日志页面加载失败"), 500


@main_bp.route('/config')
@login_required
def config_page():
    """配置页面"""
    try:
        return render_template('config.html')
        
    except Exception as e:
        logger.error(f"配置页面异常: {e}")
        return render_template('error.html', error="配置页面加载失败"), 500


@main_bp.route('/prompts')
@login_required
def prompts_page():
    """提示词管理页面"""
    try:
        return render_template('prompts.html')
        
    except Exception as e:
        logger.error(f"提示词页面异常: {e}")
        return render_template('error.html', error="提示词页面加载失败"), 500


@main_bp.route('/statistics')
@login_required
def statistics_page():
    """统计页面"""
    try:
        return render_template('statistics.html')
        
    except Exception as e:
        logger.error(f"统计页面异常: {e}")
        return render_template('error.html', error="统计页面加载失败"), 500


@main_bp.route('/health')
def health_check():
    """健康检查页面"""
    try:
        return {'status': 'healthy', 'message': 'Web服务运行正常'}
        
    except Exception as e:
        logger.error(f"健康检查异常: {e}")
        return {'status': 'error', 'message': '服务异常'}, 500 