from flask import Flask, render_template, request, jsonify, Response, session, redirect, url_for
from flask_socketio import SocketIO, emit
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
import subprocess
import psutil
import threading
import time
import json
import re
from datetime import datetime, timedelta
from collections import deque
import signal
import sys
from dotenv import load_dotenv
import pytz

# 北京时区
BEIJING_TZ = pytz.timezone('Asia/Shanghai')

def get_beijing_time():
    """获取当前北京时间"""
    return datetime.now(BEIJING_TZ)

def format_beijing_time(dt=None):
    """格式化北京时间为字符串"""
    if dt is None:
        dt = get_beijing_time()
    elif dt.tzinfo is None:
        # 如果传入的是naive datetime，假设是UTC时间
        dt = pytz.UTC.localize(dt).astimezone(BEIJING_TZ)
    elif dt.tzinfo != BEIJING_TZ:
        # 如果是其他时区，转换为北京时区
        dt = dt.astimezone(BEIJING_TZ)
    
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def convert_log_timestamp_to_beijing(message):
    """将日志消息中的服务器本地时间戳转换为北京时间"""
    import re
    
    # 匹配loguru格式的时间戳：YYYY-MM-DD HH:mm:ss.SSS
    timestamp_pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d{3})?)'
    
    def replace_timestamp(match):
        timestamp_str = match.group(1)
        try:
            # 解析时间戳
            if '.' in timestamp_str:
                # 包含毫秒
                dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S.%f")
            else:
                # 不包含毫秒
                dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            
            # 假设原始时间戳是服务器本地时间（naive datetime）
            # 服务器当前在英国，时区为BST（英国夏令时）= UTC+1
            # 北京时间 = UTC+8，所以北京时间比BST快7小时
            
            # 将服务器本地时间（BST）先转换为UTC，再转换为北京时间
            bst_tz = pytz.timezone('Europe/London')
            bst_dt = bst_tz.localize(dt)
            # 转换为北京时间
            beijing_dt = bst_dt.astimezone(BEIJING_TZ)
            
            # 返回格式化的北京时间（保留毫秒格式如果有的话）
            if '.' in timestamp_str:
                return beijing_dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # 保留3位毫秒
            else:
                return beijing_dt.strftime("%Y-%m-%d %H:%M:%S")
                
        except Exception as e:
            # 如果转换失败，返回原始时间戳
            return timestamp_str
    
    # 替换消息中的所有时间戳
    converted_message = re.sub(timestamp_pattern, replace_timestamp, message)
    return converted_message

# 加载Web UI配置
def load_web_ui_config():
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
            # 如果配置文件不存在，创建默认配置文件
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4, ensure_ascii=False)
            print(f"已创建默认配置文件: {config_file}")
            return default_config
    except Exception as e:
        print(f"读取配置文件失败，使用默认配置: {e}")
        return default_config

# 加载配置
web_ui_config = load_web_ui_config()

app = Flask(__name__)
app.config['SECRET_KEY'] = web_ui_config['auth']['secret_key']
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=web_ui_config['session']['permanent_session_lifetime_hours'])
socketio = SocketIO(app, cors_allowed_origins="*")

# 认证配置
ADMIN_USERNAME = web_ui_config['auth']['username']
ADMIN_PASSWORD_HASH = generate_password_hash(web_ui_config['auth']['password'])

# 认证装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            if request.is_json:
                return jsonify({'error': '需要登录', 'code': 401}), 401
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

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
            # 转换消息中的时间戳为北京时间
            converted_message = convert_log_timestamp_to_beijing(message)
            
            timestamp = format_beijing_time()
            log_entry = {
                "timestamp": timestamp,
                "message": converted_message,
                "type": self.get_log_type(converted_message)
            }
            log_buffer.append(log_entry)
            # 实时推送到前端
            socketio.emit('new_log', log_entry)
            
            # 检查心跳信息
            if "心跳包已发送" in converted_message or "收到心跳响应" in converted_message:
                global last_heartbeat_time
                last_heartbeat_time = get_beijing_time()
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

def find_existing_main_process():
    """查找已经运行的main.py进程"""
    try:
        current_dir = os.getcwd()
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cwd']):
            try:
                if proc.info['name'] and 'python' in proc.info['name'].lower():
                    if proc.info['cmdline'] and len(proc.info['cmdline']) >= 2:
                        # 检查是否是python main.py命令
                        cmdline = proc.info['cmdline']
                        if any('main.py' in arg for arg in cmdline):
                            # 进一步检查工作目录是否匹配
                            try:
                                if proc.info['cwd'] == current_dir:
                                    return proc
                            except (psutil.AccessDenied, KeyError):
                                # 如果无法获取工作目录，仍然返回找到的进程
                                return proc
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
    except Exception as e:
        print(f"查找进程时发生错误: {e}")
    return None

def attach_to_existing_process():
    """连接到已存在的main.py进程"""
    global main_process, process_status, last_heartbeat_time
    
    existing_proc = find_existing_main_process()
    if existing_proc:
        try:
            # 创建一个假的subprocess对象来兼容现有代码
            class ExistingProcess:
                def __init__(self, psutil_proc):
                    self.psutil_proc = psutil_proc
                    self.pid = psutil_proc.pid
                    self.stdout = None  # 无法获取已运行进程的输出
                
                def poll(self):
                    """检查进程是否还在运行"""
                    try:
                        return None if self.psutil_proc.is_running() else 0
                    except:
                        return 0
                
                def terminate(self):
                    """终止进程"""
                    self.psutil_proc.terminate()
                
                def kill(self):
                    """强制结束进程"""
                    self.psutil_proc.kill()
                
                def wait(self, timeout=None):
                    """等待进程结束"""
                    try:
                        self.psutil_proc.wait(timeout=timeout)
                    except psutil.TimeoutExpired:
                        raise subprocess.TimeoutExpired(cmd=None, timeout=timeout)
            
            main_process = ExistingProcess(existing_proc)
            process_status = "running"
            
            # 设置初始心跳时间为当前时间
            last_heartbeat_time = get_beijing_time()
            
            # 启动日志捕获
            log_capture.start_capture()
            
            # 启动监控线程，包括文件日志读取
            monitor_thread = threading.Thread(target=monitor_existing_process_with_logs, args=(existing_proc,))
            monitor_thread.daemon = True
            monitor_thread.start()
            
            print(f"已连接到现有main.py进程 (PID: {existing_proc.pid})")
            return True
        except Exception as e:
            print(f"连接到现有进程失败: {e}")
    return False

def monitor_existing_process_with_logs(psutil_proc):
    """监控已存在的进程并读取日志文件"""
    global process_status, last_heartbeat_time
    
    # 记录日志文件的最后读取位置
    log_file_path = "main.log"
    last_position = 0
    
    # 如果日志文件存在，先读取现有内容的最后位置
    if os.path.exists(log_file_path):
        try:
            with open(log_file_path, 'r', encoding='utf-8') as f:
                f.seek(0, 2)  # 移动到文件末尾
                last_position = f.tell()
        except Exception:
            pass
    
    while True:
        try:
            if not psutil_proc.is_running():
                process_status = "stopped"
                log_capture.stop_capture()
                break
            
            # 读取新的日志内容
            if os.path.exists(log_file_path):
                try:
                    with open(log_file_path, 'r', encoding='utf-8') as f:
                        f.seek(last_position)
                        new_lines = f.readlines()
                        if new_lines:
                            for line in new_lines:
                                line = line.strip()
                                if line:
                                    # 添加到日志缓冲区
                                    log_capture.add_log(line)
                                    # 检查是否为心跳相关日志
                                    if "心跳包已发送" in line or "收到心跳响应" in line:
                                        last_heartbeat_time = get_beijing_time()
                            last_position = f.tell()
                except Exception as e:
                    pass
            
            time.sleep(1)  # 每秒检查一次新日志
            
        except Exception as e:
            break

@app.route('/')
@login_required
def index():
    """主页面"""
    return render_template('index.html')

@app.route('/login')
def login_page():
    """登录页面"""
    if session.get('logged_in'):
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/api/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'status': 'error', 'message': '用户名和密码不能为空'}), 400
        
        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session['logged_in'] = True
            session['username'] = username
            session.permanent = True
            app.logger.info(f"用户 {username} 登录成功")
            return jsonify({'status': 'success', 'message': '登录成功'})
        else:
            app.logger.warning(f"用户 {username} 登录失败：用户名或密码错误")
            return jsonify({'status': 'error', 'message': '用户名或密码错误'}), 401
            
    except Exception as e:
        app.logger.error(f"登录过程中发生错误: {e}")
        return jsonify({'status': 'error', 'message': '登录过程中发生错误'}), 500

@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    """用户登出"""
    try:
        username = session.get('username', 'unknown')
        session.clear()
        app.logger.info(f"用户 {username} 已登出")
        return jsonify({'status': 'success', 'message': '已成功登出'})
    except Exception as e:
        app.logger.error(f"登出过程中发生错误: {e}")
        return jsonify({'status': 'error', 'message': '登出过程中发生错误'}), 500

@app.route('/api/check_auth')
def check_auth():
    """检查登录状态"""
    return jsonify({
        'logged_in': bool(session.get('logged_in')),
        'username': session.get('username', '')
    })

@app.route('/api/status')
@login_required
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
        current_beijing_time = get_beijing_time()
        # 确保last_heartbeat_time是带时区信息的datetime对象
        if last_heartbeat_time.tzinfo is None:
            last_heartbeat_beijing = BEIJING_TZ.localize(last_heartbeat_time)
        else:
            last_heartbeat_beijing = last_heartbeat_time.astimezone(BEIJING_TZ)
        
        time_diff = (current_beijing_time - last_heartbeat_beijing).total_seconds()
        if time_diff < 60:  # 1分钟内有心跳
            heartbeat_status = "active"
        else:
            heartbeat_status = "timeout"
        heartbeat_time = format_beijing_time(last_heartbeat_time)
    
    return jsonify({
        "process_status": process_status,
        "heartbeat_status": heartbeat_status,
        "last_heartbeat": heartbeat_time,
        "pid": main_process.pid if is_running else None
    })

@app.route('/api/start', methods=['POST'])
@login_required
def start_main():
    """启动主程序"""
    global main_process, process_status
    
    # 首先检查是否已经有main.py进程在运行
    if not main_process or main_process.poll() is not None:
        # 尝试连接到已存在的进程
        if attach_to_existing_process():
            return jsonify({"status": "success", "message": "已连接到运行中的程序", "pid": main_process.pid})
    
    if main_process and main_process.poll() is None:
        return jsonify({"status": "error", "message": "程序已在运行中"})
    
    try:
        # 检查请求数据（可选）
        data = request.get_json() or {}
        app.logger.info(f"启动主程序请求: {data}")
        
        # 先加载.env文件到当前环境
        load_dotenv()
        
        # 创建包含当前环境变量的字典
        env = os.environ.copy()
        
        # 启动主程序
        main_process = subprocess.Popen(
            [sys.executable, "main.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1,
            env=env,  # 传递环境变量给子进程
            cwd=os.getcwd()  # 确保工作目录正确
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
@login_required
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
@login_required
def get_logs():
    """获取历史日志"""
    return jsonify(list(log_buffer))

@app.route('/api/prompts')
@login_required
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
@login_required
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
@login_required
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

@app.route('/api/chats')
@login_required
def get_chats():
    """获取聊天数据"""
    try:
        # 从日志中解析聊天数据
        chat_data = parse_chat_from_logs()
        return jsonify(list(chat_data.values()))
    except Exception as e:
        return jsonify({"status": "error", "message": f"获取聊天数据失败: {str(e)}"})

@app.route('/api/chats/<session_id>')
@login_required
def get_chat_messages(session_id):
    """获取指定会话的聊天消息"""
    try:
        chat_data = parse_chat_from_logs()
        if session_id in chat_data:
            return jsonify(chat_data[session_id])
        else:
            return jsonify({"status": "error", "message": "会话不存在"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": f"获取聊天消息失败: {str(e)}"})

def parse_chat_from_logs():
    """从日志缓冲区中解析聊天数据"""
    chat_data = {}
    current_waiting_session = None
    
    for log_entry in log_buffer:
        message = log_entry.get('message', '')
        timestamp = log_entry.get('timestamp', '')
        
        # 解析用户消息
        user_pattern = r'用户:\s*([^(]+)\s*\(ID:\s*(\d+)\),\s*商品:\s*(\d+),\s*会话:\s*(\d+),\s*消息:\s*(.+)'
        user_match = re.match(user_pattern, message)
        
        if user_match:
            user_name, user_id, product_id, session_id, user_message = user_match.groups()
            user_name = user_name.strip()
            user_message = user_message.strip()
            
            # 初始化会话数据
            if session_id not in chat_data:
                chat_data[session_id] = {
                    'sessionId': session_id,
                    'userName': user_name,
                    'userId': user_id,
                    'productId': product_id,
                    'messages': [],
                    'lastMessage': '',
                    'lastTime': timestamp,
                    'unreadCount': 0
                }
            
            # 添加用户消息
            chat_data[session_id]['messages'].append({
                'type': 'user',
                'content': user_message,
                'timestamp': timestamp
            })
            chat_data[session_id]['lastMessage'] = user_message
            chat_data[session_id]['lastTime'] = timestamp
            current_waiting_session = session_id
            
        # 解析机器人回复
        bot_pattern = r'机器人回复:\s*(.+)'
        bot_match = re.match(bot_pattern, message)
        
        if bot_match and current_waiting_session:
            bot_message = bot_match.group(1).strip()
            
            # 添加机器人回复到最近的会话
            if current_waiting_session in chat_data:
                chat_data[current_waiting_session]['messages'].append({
                    'type': 'bot',
                    'content': bot_message,
                    'timestamp': timestamp
                })
                chat_data[current_waiting_session]['lastMessage'] = bot_message
                chat_data[current_waiting_session]['lastTime'] = timestamp
            
            current_waiting_session = None
    
    return chat_data

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
    
    # 在启动时检查是否有已运行的main.py进程
    print("检查是否有已运行的main.py进程...")
    if attach_to_existing_process():
        print("已自动连接到运行中的main.py进程")
    else:
        print("未发现运行中的main.py进程")
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True) 