"""
Web管理器模块
负责管理Flask应用和主程序的交互
"""

import os
import sys
import subprocess
import psutil
import threading
import time
import json
from typing import Dict, Any, Optional
from collections import deque
from config.logger_config import get_logger
from config.config_manager import ConfigManager

# 获取专用日志记录器
logger = get_logger("web", "manager")


class WebManager:
    """
    Web管理器
    负责管理主程序的启动、停止、监控等功能
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super(WebManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化Web管理器"""
        # 避免重复初始化
        if self._initialized:
            return
            
        self.config_manager = ConfigManager()
        self.main_process: Optional[subprocess.Popen] = None
        self.main_process_pid: Optional[int] = None  # 添加进程PID跟踪
        self.log_buffer = deque(maxlen=1000)  # 保存最近1000条日志
        self.last_heartbeat_time = None
        self.process_status = "stopped"
        self.log_monitor_thread = None
        self.capturing_logs = False
        
        # 在启动时检查是否有已运行的主程序进程
        self._find_existing_process()
        
        self._initialized = True
    
    def _find_existing_process(self):
        """查找已经运行的main.py进程"""
        try:
            current_dir = os.getcwd()
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cwd']):
                try:
                    if proc.info['name'] and 'python' in proc.info['name'].lower():
                        if proc.info['cmdline'] and len(proc.info['cmdline']) >= 2:
                            # 检查是否是python main.py命令
                            if ('main.py' in ' '.join(proc.info['cmdline']) and 
                                proc.info['cwd'] == current_dir):
                                
                                # 找到已运行的进程，记录PID但不直接赋值给main_process
                                self.main_process_pid = proc.pid
                                self.process_status = "running"
                                logger.info(f"找到已运行的main.py进程 (PID: {proc.pid})")
                                
                                # 开始日志监控
                                self._start_log_monitoring()
                                return True
                                
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            logger.info("未发现运行中的main.py进程")
            return False
            
        except Exception as e:
            logger.error(f"查找已运行进程失败: {e}")
            return False
    
    def start_main_program(self) -> Dict[str, Any]:
        """启动主程序"""
        try:
            # 检查是否已有进程在运行
            if self._is_process_running():
                pid = self.main_process.pid if self.main_process else self.main_process_pid
                return {
                    "status": "error", 
                    "message": f"程序已在运行中 (PID: {pid})"
                }
            
            # 加载环境变量
            from dotenv import load_dotenv
            load_dotenv()
            
            # 创建包含当前环境变量的字典
            env = os.environ.copy()
            
            # 启动主程序
            self.main_process = subprocess.Popen(
                [sys.executable, "main.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
                env=env,
                cwd=os.getcwd()
            )
            
            self.main_process_pid = self.main_process.pid
            self.process_status = "starting"
            self._start_log_monitoring()
            
            logger.info(f"主程序启动成功 (PID: {self.main_process.pid})")
            return {
                "status": "success", 
                "message": "程序启动成功", 
                "pid": self.main_process.pid
            }
            
        except Exception as e:
            logger.error(f"启动主程序失败: {e}")
            return {
                "status": "error", 
                "message": f"启动失败: {str(e)}"
            }
    
    def stop_main_program(self) -> Dict[str, Any]:
        """停止主程序"""
        try:
            if not self._is_process_running():
                return {
                    "status": "error", 
                    "message": "程序未在运行"
                }
            
            if self.main_process:
                # 如果是通过Web管理器启动的进程，使用subprocess方法停止
                self.main_process.terminate()
                try:
                    self.main_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.main_process.kill()
                    self.main_process.wait()
            elif self.main_process_pid:
                # 如果是外部启动的进程，使用psutil方法停止
                try:
                    proc = psutil.Process(self.main_process_pid)
                    proc.terminate()
                    proc.wait(timeout=5)
                except psutil.TimeoutExpired:
                    proc.kill()
                except psutil.NoSuchProcess:
                    pass  # 进程已经不存在了
            
            # 清理状态
            self.main_process = None
            self.main_process_pid = None
            self.process_status = "stopped"
            self._stop_log_monitoring()
            
            logger.info("主程序已停止")
            return {
                "status": "success", 
                "message": "程序已停止"
            }
            
        except Exception as e:
            logger.error(f"停止主程序失败: {e}")
            return {
                "status": "error", 
                "message": f"停止失败: {str(e)}"
            }
    
    def _is_process_running(self) -> bool:
        """检查进程是否还在运行"""
        try:
            if self.main_process:
                # subprocess.Popen对象
                return self.main_process.poll() is None
            elif self.main_process_pid:
                # 通过PID检查进程是否存在
                try:
                    proc = psutil.Process(self.main_process_pid)
                    return proc.is_running()
                except psutil.NoSuchProcess:
                    self.main_process_pid = None
                    return False
            return False
        except Exception:
            return False
    
    def get_process_status(self) -> Dict[str, Any]:
        """获取进程状态"""
        try:
            if not self._is_process_running():
                # 清理无效的进程引用
                self.main_process = None
                self.main_process_pid = None
                self.process_status = "stopped"
                return {
                    "status": "stopped",
                    "pid": None,
                    "running": False
                }
            
            # 进程正在运行
            pid = self.main_process.pid if self.main_process else self.main_process_pid
            return {
                "status": "running",
                "pid": pid,
                "running": True
            }
                
        except Exception as e:
            logger.error(f"获取进程状态失败: {e}")
            return {
                "status": "error",
                "pid": None,
                "running": False,
                "error": str(e)
            }
    
    def _start_log_monitoring(self):
        """开始日志监控"""
        try:
            self.capturing_logs = True
            
            # 如果主程序是subprocess.Popen对象，启动日志监控线程
            if hasattr(self.main_process, 'stdout') and self.main_process.stdout:
                self.log_monitor_thread = threading.Thread(
                    target=self._monitor_logs, 
                    args=(self.main_process,)
                )
                self.log_monitor_thread.daemon = True
                self.log_monitor_thread.start()
                logger.info("日志监控线程已启动")
            else:
                # 如果无法直接监控进程输出，尝试监控日志文件
                logger.info("连接到已运行的进程，启动日志文件监控")
                self.log_monitor_thread = threading.Thread(
                    target=self._monitor_log_file,
                    args=()
                )
                self.log_monitor_thread.daemon = True
                self.log_monitor_thread.start()
                logger.info("日志文件监控线程已启动")
                
        except Exception as e:
            logger.error(f"启动日志监控失败: {e}")
    
    def _stop_log_monitoring(self):
        """停止日志监控"""
        self.capturing_logs = False
        if self.log_monitor_thread and self.log_monitor_thread.is_alive():
            self.log_monitor_thread.join(timeout=1)
        logger.info("日志监控已停止")
    
    def _monitor_logs(self, process):
        """监控主程序日志输出"""
        try:
            for line in iter(process.stdout.readline, ''):
                if not self.capturing_logs:
                    break
                    
                if line:
                    self._add_log_entry(line.strip())
                    
                if process.poll() is not None:
                    break
                    
        except Exception as e:
            self._add_log_entry(f"日志监控错误: {str(e)}")
    
    def _add_log_entry(self, message: str):
        """添加日志条目"""
        try:
            # 转换消息中的时间戳为北京时间
            from datetime import datetime
            import pytz
            
            BEIJING_TZ = pytz.timezone('Asia/Shanghai')
            timestamp = datetime.now(BEIJING_TZ).strftime("%Y-%m-%d %H:%M:%S")
            
            log_entry = {
                "timestamp": timestamp,
                "message": message,
                "type": self._get_log_type(message)
            }
            
            self.log_buffer.append(log_entry)
            
            # 检查心跳信息 - 更新检测逻辑
            if ("心跳包已发送" in message or 
                "收到心跳响应" in message or 
                "执行业务逻辑检查" in message):
                self.last_heartbeat_time = datetime.now(BEIJING_TZ)
                logger.debug(f"检测到业务检查信号，更新心跳时间: {self.last_heartbeat_time.strftime('%H:%M:%S')}")
            
            # 实时广播日志到WebSocket客户端
            self._broadcast_log(log_entry)
            
        except Exception as e:
            logger.error(f"添加日志条目失败: {e}")
    
    def _broadcast_log(self, log_entry: Dict[str, Any]):
        """广播日志到WebSocket客户端"""
        try:
            from .routes.websocket_routes import broadcast_log
            broadcast_log(log_entry)
        except Exception as e:
            # 静默处理广播错误，避免影响日志记录
            pass
    
    def _get_log_type(self, message: str) -> str:
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
    
    def get_logs(self) -> list:
        """获取历史日志"""
        return list(self.log_buffer)
    
    def get_heartbeat_status(self) -> Dict[str, Any]:
        """获取心跳状态"""
        if self.last_heartbeat_time:
            from datetime import datetime
            import pytz
            
            BEIJING_TZ = pytz.timezone('Asia/Shanghai')
            now = datetime.now(BEIJING_TZ)
            time_diff = (now - self.last_heartbeat_time).total_seconds()
            
            return {
                "status": "active" if time_diff < 60 else "inactive",  # 60秒内有心跳为活跃
                "last_check": self.last_heartbeat_time.strftime("%Y-%m-%d %H:%M:%S"),
                "last_heartbeat": self.last_heartbeat_time.strftime("%Y-%m-%d %H:%M:%S"),  # 保持兼容性
                "seconds_ago": int(time_diff)
            }
        else:
            return {
                "status": "unknown",
                "last_check": None,
                "last_heartbeat": None,
                "seconds_ago": None
            }
    
    def get_health_info(self) -> Dict[str, Any]:
        """获取健康状态信息"""
        process_status = self.get_process_status()
        heartbeat_status = self.get_heartbeat_status()
        
        return {
            "web_manager": "healthy",
            "main_process": process_status,
            "heartbeat": heartbeat_status,
            "log_buffer_size": len(self.log_buffer),
            "log_monitoring": self.capturing_logs
        }
    
    def _monitor_log_file(self):
        """监控主程序日志文件"""
        try:
            import os
            
            # 主程序日志文件路径
            log_file_path = "logs/main.log"
            
            if not os.path.exists(log_file_path):
                logger.warning(f"日志文件不存在: {log_file_path}")
                return
            
            # 获取文件初始大小（从文件末尾开始读取）
            with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(0, 2)  # 移动到文件末尾
                last_position = f.tell()
            
            logger.info(f"开始监控日志文件: {log_file_path}, 起始位置: {last_position}")
            
            while self.capturing_logs:
                try:
                    # 检查文件大小是否发生变化
                    current_size = os.path.getsize(log_file_path)
                    
                    if current_size > last_position:
                        # 文件有新内容，读取新增的部分
                        with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            f.seek(last_position)
                            new_lines = f.readlines()
                            last_position = f.tell()
                        
                        # 处理新日志行
                        for line in new_lines:
                            line = line.strip()
                            if line:  # 忽略空行
                                self._add_log_entry(line)
                    
                    # 短暂休眠避免过度CPU使用
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"读取日志文件异常: {e}")
                    time.sleep(5)  # 出错时延长等待时间
                    
        except Exception as e:
            logger.error(f"日志文件监控异常: {e}") 