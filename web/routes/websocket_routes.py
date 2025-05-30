"""
WebSocket路由模块
处理实时通信功能，包括实时日志传输和状态更新
"""

import time
import threading
from flask_socketio import emit, disconnect, join_room, leave_room
from flask import session
from config.logger_config import get_logger

# 获取专用日志记录器
logger = get_logger("web", "websocket_routes")

# 全局WebSocket应用实例，用于从外部发送消息
_socketio_app = None


def register_socketio_events(socketio):
    """注册WebSocket事件处理器"""
    global _socketio_app
    _socketio_app = socketio
    
    @socketio.on('connect')
    def handle_connect():
        """处理WebSocket连接建立"""
        try:
            # 检查认证状态
            if not session.get('logged_in'):
                logger.warning("未认证的WebSocket连接尝试")
                disconnect()
                return False
            
            username = session.get('username', 'unknown')
            logger.info(f"用户 {username} 建立WebSocket连接")
            
            # 加入日志房间以接收日志推送
            join_room('logs')
            join_room('status')
            
            emit('connect_response', {
                'status': 'success',
                'message': '连接成功',
                'username': username,
                'timestamp': time.time()
            })
            
            # 发送初始状态
            emit('status_update', {
                'type': 'initial',
                'data': get_initial_status()
            })
            
        except Exception as e:
            logger.error(f"WebSocket连接处理异常: {e}")
            disconnect()
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """处理WebSocket连接断开"""
        try:
            username = session.get('username', 'unknown')
            logger.info(f"用户 {username} 断开WebSocket连接")
            
            # 离开所有房间
            leave_room('logs')
            leave_room('status')
            
        except Exception as e:
            logger.error(f"WebSocket断开处理异常: {e}")
    
    @socketio.on('ping')
    def handle_ping():
        """处理ping请求"""
        try:
            emit('pong', {
                'timestamp': time.time(),
                'server_time': time.strftime('%Y-%m-%d %H:%M:%S')
            })
            
        except Exception as e:
            logger.error(f"WebSocket ping处理异常: {e}")
    
    @socketio.on('request_status')
    def handle_request_status():
        """请求状态更新"""
        try:
            if not session.get('logged_in'):
                disconnect()
                return
            
            # 获取当前状态并发送
            from web.manager import WebManager
            web_manager = WebManager()
            
            process_status = web_manager.get_process_status()
            heartbeat_status = web_manager.get_heartbeat_status()
            
            emit('status_update', {
                'type': 'requested',
                'data': {
                    'process': process_status,
                    'heartbeat': heartbeat_status,
                    'timestamp': time.time()
                }
            })
            
        except Exception as e:
            logger.error(f"状态请求处理异常: {e}")
    
    @socketio.on('request_logs')
    def handle_request_logs():
        """请求最新日志"""
        try:
            if not session.get('logged_in'):
                disconnect()
                return
            
            from web.manager import WebManager
            web_manager = WebManager()
            logs = web_manager.get_logs()
            
            # 发送最新的50条日志
            recent_logs = logs[-50:] if len(logs) > 50 else logs
            
            emit('logs_batch', {
                'logs': recent_logs,
                'total_count': len(logs),
                'timestamp': time.time()
            })
            
        except Exception as e:
            logger.error(f"日志请求处理异常: {e}")
    
    logger.info("WebSocket事件处理器注册完成")


def get_initial_status():
    """获取初始状态信息"""
    try:
        from web.manager import WebManager
        web_manager = WebManager()
        
        return {
            'process': web_manager.get_process_status(),
            'heartbeat': web_manager.get_heartbeat_status(),
            'health': web_manager.get_health_info()
        }
    except Exception as e:
        logger.error(f"获取初始状态失败: {e}")
        return {
            'process': {'running': False, 'pid': None},
            'heartbeat': {'last_heartbeat': None},
            'health': {'status': 'unknown'}
        }


def broadcast_log(log_data):
    """广播日志消息到所有连接的客户端"""
    global _socketio_app
    if _socketio_app:
        try:
            _socketio_app.emit('new_log', log_data, room='logs')
        except Exception as e:
            logger.error(f"广播日志失败: {e}")


def broadcast_status_update(status_data):
    """广播状态更新到所有连接的客户端"""
    global _socketio_app
    if _socketio_app:
        try:
            _socketio_app.emit('status_update', {
                'type': 'broadcast',
                'data': status_data,
                'timestamp': time.time()
            }, room='status')
        except Exception as e:
            logger.error(f"广播状态更新失败: {e}")


def send_heartbeat():
    """发送心跳信号"""
    global _socketio_app
    if _socketio_app:
        try:
            from datetime import datetime
            import pytz
            
            # 更新Web管理器的心跳时间
            from web.manager import WebManager
            web_manager = WebManager()
            
            BEIJING_TZ = pytz.timezone('Asia/Shanghai')
            current_time = datetime.now(BEIJING_TZ)
            
            # 检查main.py进程是否在运行，如果是则更新心跳时间
            if web_manager._is_process_running():
                web_manager.last_heartbeat_time = current_time
                logger.debug(f"检测到main.py进程活跃，更新检查时间: {current_time.strftime('%H:%M:%S')}")
            
            # 发送WebSocket心跳
            _socketio_app.emit('heartbeat', {
                'timestamp': time.time(),
                'server_time': current_time.strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'active' if web_manager._is_process_running() else 'inactive'
            }, room='status')
            
            logger.debug(f"WebSocket心跳已发送: {current_time.strftime('%H:%M:%S')}")
            
        except Exception as e:
            logger.error(f"发送心跳失败: {e}")


# 启动心跳线程
def start_heartbeat_thread():
    """启动心跳线程"""
    def heartbeat_worker():
        while True:
            try:
                send_heartbeat()
                time.sleep(30)  # 每30秒发送一次心跳
            except Exception as e:
                logger.error(f"心跳线程异常: {e}")
                time.sleep(60)
    
    heartbeat_thread = threading.Thread(target=heartbeat_worker, daemon=True)
    heartbeat_thread.start()
    logger.info("心跳线程已启动") 