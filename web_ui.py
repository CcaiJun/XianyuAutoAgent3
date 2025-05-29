from flask import Flask, render_template, request, jsonify, Response
from flask_socketio import SocketIO, emit
import os
import subprocess
import psutil
import threading
import time
import json
import re
from datetime import datetime
from collections import deque
import signal
import sys

app = Flask(__name__)
app.config['SECRET_KEY'] = 'xianyu_auto_agent_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

# 全局变量
main_process = None
log_buffer = deque(maxlen=1000)  # 保存最近1000条日志
last_heartbeat_time = None
process_status = "stopped"

class LogCapture:
    def __init__(self):
        self.capturing = False
        
    def start_capture(self):
        """开始捕获日志"""
        self.capturing = True
        
    def stop_capture(self):
        """停止捕获日志"""
        self.capturing = False
        
    def add_log(self, message):
        """添加日志到缓冲区"""
        if self.capturing:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = {
                "timestamp": timestamp,
                "message": message,
                "type": self.get_log_type(message)
            }
            log_buffer.append(log_entry)
            # 实时推送到前端
            socketio.emit('new_log', log_entry)
            
            # 检查心跳信息
            if "心跳包已发送" in message or "收到心跳响应" in message:
                global last_heartbeat_time
                last_heartbeat_time = datetime.now()
                socketio.emit('heartbeat_update', {
                    "status": "active",
                    "timestamp": timestamp
                })
    
    def get_log_type(self, message):
        """根据日志内容判断日志类型"""
        if "ERROR" in message or "错误" in message:
            return "error"
        elif "WARNING" in message or "警告" in message:
            return "warning"
        elif "INFO" in message or "成功" in message:
            return "info"
        elif "DEBUG" in message or "心跳" in message:
            return "debug"
        else:
            return "info"

log_capture = LogCapture()

@app.route('/')
def index():
    """主页面"""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """获取系统状态"""
    global main_process, last_heartbeat_time, process_status
    
    is_running = main_process and main_process.poll() is None
    if is_running:
        process_status = "running"
    else:
        process_status = "stopped"
        
    heartbeat_status = "inactive"
    heartbeat_time = None
    
    if last_heartbeat_time:
        time_diff = (datetime.now() - last_heartbeat_time).total_seconds()
        if time_diff < 60:  # 1分钟内有心跳
            heartbeat_status = "active"
        else:
            heartbeat_status = "timeout"
        heartbeat_time = last_heartbeat_time.strftime("%Y-%m-%d %H:%M:%S")
    
    return jsonify({
        "process_status": process_status,
        "heartbeat_status": heartbeat_status,
        "last_heartbeat": heartbeat_time,
        "pid": main_process.pid if is_running else None
    })

@app.route('/api/start', methods=['POST'])
def start_main():
    """启动主程序"""
    global main_process, process_status
    
    if main_process and main_process.poll() is None:
        return jsonify({"status": "error", "message": "程序已在运行中"})
    
    try:
        # 检查请求数据（可选）
        data = request.get_json() or {}
        app.logger.info(f"启动主程序请求: {data}")
        
        # 启动主程序
        main_process = subprocess.Popen(
            [sys.executable, "main.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        process_status = "starting"
        log_capture.start_capture()
        
        # 启动日志监控线程
        log_thread = threading.Thread(target=monitor_logs, args=(main_process,))
        log_thread.daemon = True
        log_thread.start()
        
        app.logger.info(f"主程序启动成功 (PID: {main_process.pid})")
        return jsonify({"status": "success", "message": "程序启动成功", "pid": main_process.pid})
        
    except Exception as e:
        app.logger.error(f"启动主程序失败: {e}")
        return jsonify({"status": "error", "message": f"启动失败: {str(e)}"})

@app.route('/api/stop', methods=['POST'])
def stop_main():
    """停止主程序"""
    global main_process, process_status
    
    if not main_process or main_process.poll() is not None:
        return jsonify({"status": "error", "message": "程序未在运行"})
    
    try:
        # 检查请求数据（可选）
        data = request.get_json() or {}
        app.logger.info(f"停止主程序请求: {data}")
        
        # 优雅停止进程
        main_process.terminate()
        
        # 等待进程结束，最多等待5秒
        try:
            main_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            # 强制结束
            main_process.kill()
            main_process.wait()
        
        process_status = "stopped"
        log_capture.stop_capture()
        
        app.logger.info("主程序已停止")
        return jsonify({"status": "success", "message": "程序已停止"})
        
    except Exception as e:
        app.logger.error(f"停止主程序失败: {e}")
        return jsonify({"status": "error", "message": f"停止失败: {str(e)}"})

@app.route('/api/logs')
def get_logs():
    """获取历史日志"""
    return jsonify(list(log_buffer))

@app.route('/api/prompts')
def get_prompts():
    """获取所有提示词文件"""
    prompts_dir = "prompts"
    files = []
    
    if os.path.exists(prompts_dir):
        for filename in os.listdir(prompts_dir):
            if filename.endswith('.txt'):
                filepath = os.path.join(prompts_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                files.append({
                    "name": filename,
                    "content": content
                })
    
    return jsonify(files)

@app.route('/api/prompts/<filename>', methods=['GET', 'POST'])
def manage_prompt(filename):
    """获取或更新提示词文件"""
    filepath = os.path.join("prompts", filename)
    
    if request.method == 'GET':
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            return jsonify({"content": content})
        else:
            return jsonify({"error": "文件不存在"}), 404
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            content = data.get('content', '')
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return jsonify({"status": "success", "message": "文件保存成功"})
        except Exception as e:
            return jsonify({"status": "error", "message": f"保存失败: {str(e)}"})

@app.route('/api/env', methods=['GET', 'POST'])
def manage_env():
    """获取或更新环境变量文件"""
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
        try:
            data = request.get_json()
            env_vars = data.get('env_vars', {})
            
            with open(env_file, 'w', encoding='utf-8') as f:
                for key, value in env_vars.items():
                    f.write(f"{key}={value}\n")
            
            return jsonify({"status": "success", "message": "环境变量保存成功"})
        except Exception as e:
            return jsonify({"status": "error", "message": f"保存失败: {str(e)}"})

def monitor_logs(process):
    """监控主程序日志输出"""
    try:
        for line in iter(process.stdout.readline, ''):
            if line:
                log_capture.add_log(line.strip())
            if process.poll() is not None:
                break
    except Exception as e:
        log_capture.add_log(f"日志监控错误: {str(e)}")

@socketio.on('connect')
def handle_connect():
    """WebSocket连接建立"""
    emit('connected', {'message': '连接成功'})

@socketio.on('disconnect')
def handle_disconnect():
    """WebSocket连接断开"""
    pass

def cleanup():
    """清理资源"""
    global main_process
    if main_process and main_process.poll() is None:
        main_process.terminate()
        try:
            main_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            main_process.kill()

# 注册清理函数
import atexit
atexit.register(cleanup)

if __name__ == '__main__':
    # 确保必要目录存在
    os.makedirs("prompts", exist_ok=True)
    os.makedirs("templates", exist_ok=True)
    os.makedirs("static/css", exist_ok=True)
    os.makedirs("static/js", exist_ok=True)
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True) 