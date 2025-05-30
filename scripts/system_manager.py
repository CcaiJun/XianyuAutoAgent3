#!/usr/bin/env python3
"""
闲鱼自动代理系统管理器
综合管理脚本，提供系统启动、监控、Cookie管理等功能
"""

import os
import sys
import time
import psutil
import signal
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import argparse

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.cookie_utils import get_cookie_status_report, update_env_cookies_safely
from config.logger_config import get_logger

# 获取专用日志记录器
logger = get_logger("script", "system_manager")

class SystemManager:
    """系统管理器类"""
    
    def __init__(self):
        """初始化系统管理器"""
        self.project_root = project_root
        self.main_script = self.project_root / "main.py"
        self.web_script = self.project_root / "web_ui.py"
        self.pid_dir = self.project_root / "pids"
        self.log_dir = self.project_root / "logs"
        
        # 确保PID目录存在
        self.pid_dir.mkdir(exist_ok=True)
        
        # PID文件路径
        self.main_pid_file = self.pid_dir / "main.pid"
        self.web_pid_file = self.pid_dir / "web_ui.pid"
    
    def print_banner(self):
        """打印横幅"""
        banner = """
╔══════════════════════════════════════════════════════════════╗
║              🚀 闲鱼自动代理系统管理器                          ║
║        智能闲鱼客服机器人系统 - 一站式管理控制台                 ║
╚══════════════════════════════════════════════════════════════╝
"""
        print(banner)
    
    def get_process_status(self, pid_file: Path, process_name: str) -> Dict[str, any]:
        """获取进程状态"""
        status = {
            "name": process_name,
            "running": False,
            "pid": None,
            "cpu_percent": 0.0,
            "memory_mb": 0.0,
            "uptime": "0分钟",
            "status": "已停止"
        }
        
        if not pid_file.exists():
            return status
        
        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            if psutil.pid_exists(pid):
                process = psutil.Process(pid)
                
                # 检查进程是否还是我们启动的进程
                if process_name.lower() in process.name().lower() or \
                   any(process_name.lower() in arg.lower() for arg in process.cmdline()):
                    
                    status.update({
                        "running": True,
                        "pid": pid,
                        "cpu_percent": process.cpu_percent(),
                        "memory_mb": process.memory_info().rss / 1024 / 1024,
                        "uptime": self._format_uptime(time.time() - process.create_time()),
                        "status": process.status()
                    })
                else:
                    # PID存在但不是我们的进程，清理PID文件
                    pid_file.unlink()
            else:
                # PID不存在，清理PID文件
                pid_file.unlink()
                
        except (ValueError, psutil.NoSuchProcess, PermissionError):
            # PID文件损坏或进程不存在
            if pid_file.exists():
                pid_file.unlink()
        
        return status
    
    def _format_uptime(self, seconds: float) -> str:
        """格式化运行时间"""
        if seconds < 60:
            return f"{int(seconds)}秒"
        elif seconds < 3600:
            return f"{int(seconds/60)}分钟"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}小时{minutes}分钟"
        else:
            days = int(seconds / 86400)
            hours = int((seconds % 86400) / 3600)
            return f"{days}天{hours}小时"
    
    def show_status(self):
        """显示系统状态"""
        print("📊 系统状态检查...")
        print("=" * 60)
        
        # 获取进程状态
        main_status = self.get_process_status(self.main_pid_file, "main")
        web_status = self.get_process_status(self.web_pid_file, "web_ui")
        
        # 显示主程序状态
        main_icon = "🟢" if main_status["running"] else "🔴"
        print(f"{main_icon} 主程序 (main.py):")
        print(f"    状态: {main_status['status']}")
        if main_status["running"]:
            print(f"    PID: {main_status['pid']}")
            print(f"    运行时间: {main_status['uptime']}")
            print(f"    CPU使用率: {main_status['cpu_percent']:.1f}%")
            print(f"    内存使用: {main_status['memory_mb']:.1f}MB")
        
        print()
        
        # 显示Web界面状态
        web_icon = "🟢" if web_status["running"] else "🔴"
        print(f"{web_icon} Web界面 (web_ui.py):")
        print(f"    状态: {web_status['status']}")
        if web_status["running"]:
            print(f"    PID: {web_status['pid']}")
            print(f"    运行时间: {web_status['uptime']}")
            print(f"    CPU使用率: {web_status['cpu_percent']:.1f}%")
            print(f"    内存使用: {web_status['memory_mb']:.1f}MB")
        
        print()
        
        # 系统资源状态
        self._show_system_resources()
        
        # Cookie状态
        self._show_cookie_status()
        
        # 整体健康度
        health_score = self._calculate_health_score(main_status, web_status)
        print(f"🎯 系统健康度: {health_score}/100")
        
        if health_score >= 80:
            print("✅ 系统运行良好")
        elif health_score >= 60:
            print("⚠️ 系统运行正常，但需要关注")
        else:
            print("❌ 系统存在问题，需要检查")
    
    def _show_system_resources(self):
        """显示系统资源状态"""
        print("💻 系统资源:")
        
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_icon = "🟢" if cpu_percent < 70 else "⚠️" if cpu_percent < 90 else "🔴"
        print(f"    {cpu_icon} CPU使用率: {cpu_percent:.1f}%")
        
        # 内存使用率
        memory = psutil.virtual_memory()
        mem_icon = "🟢" if memory.percent < 70 else "⚠️" if memory.percent < 90 else "🔴"
        print(f"    {mem_icon} 内存使用率: {memory.percent:.1f}% ({memory.used/1024/1024/1024:.1f}GB/{memory.total/1024/1024/1024:.1f}GB)")
        
        # 磁盘使用率
        disk = psutil.disk_usage('/')
        disk_icon = "🟢" if disk.percent < 80 else "⚠️" if disk.percent < 95 else "🔴"
        print(f"    {disk_icon} 磁盘使用率: {disk.percent:.1f}%")
        
        print()
    
    def _show_cookie_status(self):
        """显示Cookie状态"""
        print("🍪 Cookie状态:")
        
        try:
            # 读取当前Cookie
            env_path = self._find_env_file()
            if env_path:
                cookie_str = self._read_cookies_from_env(env_path)
                if cookie_str:
                    report = get_cookie_status_report(cookie_str)
                    
                    complete_icon = "✅" if report['is_complete'] else "❌"
                    fresh_icon = "✅" if report['is_fresh'] else "⚠️"
                    
                    print(f"    {complete_icon} 完整性: {'完整' if report['is_complete'] else '不完整'}")
                    print(f"    {fresh_icon} 新鲜度: {'新鲜' if report['is_fresh'] else '可能过期'}")
                    print(f"    🆔 用户ID: {report['user_id']}")
                    
                    if report['age_hours'] is not None:
                        print(f"    ⏰ Cookie年龄: {report['age_hours']:.1f}小时")
                else:
                    print("    ❌ 未找到Cookie配置")
            else:
                print("    ❌ 未找到.env文件")
        except Exception as e:
            print(f"    ❌ Cookie状态检查失败: {e}")
        
        print()
    
    def _calculate_health_score(self, main_status: Dict, web_status: Dict) -> int:
        """计算系统健康度评分"""
        score = 0
        
        # 主程序状态 (40分)
        if main_status["running"]:
            score += 40
        
        # Web界面状态 (20分)
        if web_status["running"]:
            score += 20
        
        # 系统资源 (30分)
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent
        
        if cpu_percent < 70:
            score += 15
        elif cpu_percent < 90:
            score += 10
        
        if memory_percent < 70:
            score += 15
        elif memory_percent < 90:
            score += 10
        
        # Cookie状态 (10分)
        try:
            env_path = self._find_env_file()
            if env_path:
                cookie_str = self._read_cookies_from_env(env_path)
                if cookie_str:
                    report = get_cookie_status_report(cookie_str)
                    if report['is_complete'] and report['is_fresh']:
                        score += 10
                    elif report['is_complete']:
                        score += 5
        except:
            pass
        
        return min(100, score)
    
    def start_service(self, service: str, background: bool = False):
        """启动服务"""
        if service == "main":
            script_path = self.main_script
            pid_file = self.main_pid_file
            service_name = "主程序"
        elif service == "web":
            script_path = self.web_script
            pid_file = self.web_pid_file
            service_name = "Web界面"
        else:
            print(f"❌ 未知服务: {service}")
            return False
        
        # 检查是否已经运行
        status = self.get_process_status(pid_file, service)
        if status["running"]:
            print(f"⚠️ {service_name}已经在运行中 (PID: {status['pid']})")
            return False
        
        print(f"🚀 启动{service_name}...")
        
        try:
            if background:
                # 后台启动
                process = subprocess.Popen(
                    [sys.executable, str(script_path)],
                    cwd=str(self.project_root),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
                
                # 等待一下确保进程启动
                time.sleep(2)
                
                if process.poll() is None:
                    # 保存PID
                    with open(pid_file, 'w') as f:
                        f.write(str(process.pid))
                    
                    print(f"✅ {service_name}已在后台启动 (PID: {process.pid})")
                    return True
                else:
                    print(f"❌ {service_name}启动失败")
                    return False
            else:
                # 前台启动
                print(f"▶️ 在前台启动{service_name}...")
                print("   按 Ctrl+C 停止")
                subprocess.run([sys.executable, str(script_path)], cwd=str(self.project_root))
                return True
                
        except KeyboardInterrupt:
            print(f"\n⏹️ {service_name}已停止")
            return True
        except Exception as e:
            print(f"❌ 启动{service_name}失败: {e}")
            return False
    
    def stop_service(self, service: str):
        """停止服务"""
        if service == "main":
            pid_file = self.main_pid_file
            service_name = "主程序"
        elif service == "web":
            pid_file = self.web_pid_file
            service_name = "Web界面"
        else:
            print(f"❌ 未知服务: {service}")
            return False
        
        status = self.get_process_status(pid_file, service)
        if not status["running"]:
            print(f"⚠️ {service_name}未运行")
            return False
        
        print(f"⏹️ 停止{service_name}...")
        
        try:
            pid = status["pid"]
            
            # 发送SIGTERM信号
            os.kill(pid, signal.SIGTERM)
            
            # 等待进程结束
            for _ in range(30):  # 等待最多30秒
                if not psutil.pid_exists(pid):
                    break
                time.sleep(1)
            
            # 如果进程还存在，强制结束
            if psutil.pid_exists(pid):
                print(f"⚠️ 进程未响应，强制结束...")
                os.kill(pid, signal.SIGKILL)
                time.sleep(2)
            
            # 清理PID文件
            if pid_file.exists():
                pid_file.unlink()
            
            print(f"✅ {service_name}已停止")
            return True
            
        except (ProcessLookupError, psutil.NoSuchProcess):
            print(f"✅ {service_name}已停止")
            if pid_file.exists():
                pid_file.unlink()
            return True
        except Exception as e:
            print(f"❌ 停止{service_name}失败: {e}")
            return False
    
    def restart_service(self, service: str, background: bool = False):
        """重启服务"""
        print(f"🔄 重启服务: {service}")
        
        # 先停止
        self.stop_service(service)
        
        # 等待一下
        time.sleep(2)
        
        # 再启动
        return self.start_service(service, background)
    
    def view_logs(self, service: str = "all", lines: int = 50):
        """查看日志"""
        if service == "main":
            log_files = [self.log_dir / "main.log"]
        elif service == "web":
            log_files = [self.log_dir / "web_ui.log"]
        elif service == "all":
            log_files = [
                self.log_dir / "main.log",
                self.log_dir / "web_ui.log"
            ]
        else:
            print(f"❌ 未知服务: {service}")
            return
        
        print(f"📄 查看日志 (最近 {lines} 行)...")
        print("=" * 60)
        
        for log_file in log_files:
            if log_file.exists():
                print(f"\n📁 {log_file.name}:")
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        all_lines = f.readlines()
                        recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                        for line in recent_lines:
                            print(line.rstrip())
                except Exception as e:
                    print(f"❌ 读取日志失败: {e}")
            else:
                print(f"⚠️ 日志文件不存在: {log_file}")
    
    def manage_cookies(self):
        """Cookie管理界面"""
        while True:
            print("\n🍪 Cookie管理")
            print("=" * 30)
            print("1. 查看Cookie状态")
            print("2. 更新Cookie")
            print("3. 验证Cookie")
            print("4. 备份.env文件")
            print("0. 返回主菜单")
            
            choice = input("\n请选择操作: ").strip()
            
            if choice == "1":
                self._cookie_status()
            elif choice == "2":
                self._cookie_update()
            elif choice == "3":
                self._cookie_validate()
            elif choice == "4":
                self._cookie_backup()
            elif choice == "0":
                break
            else:
                print("❌ 无效选择")
    
    def _cookie_status(self):
        """显示Cookie详细状态"""
        print("\n📊 Cookie详细状态...")
        
        # 调用cookie_manager脚本
        cookie_manager = self.project_root / "scripts" / "cookie_manager.py"
        subprocess.run([sys.executable, str(cookie_manager), "status"])
    
    def _cookie_update(self):
        """更新Cookie"""
        print("\n🔄 更新Cookie...")
        print("1. 交互式输入")
        print("2. 从文件读取")
        
        choice = input("请选择方式: ").strip()
        
        cookie_manager = self.project_root / "scripts" / "cookie_manager.py"
        
        if choice == "1":
            subprocess.run([sys.executable, str(cookie_manager), "update"])
        elif choice == "2":
            file_path = input("请输入文件路径: ").strip()
            if os.path.exists(file_path):
                subprocess.run([sys.executable, str(cookie_manager), "update", "-f", file_path])
            else:
                print("❌ 文件不存在")
        else:
            print("❌ 无效选择")
    
    def _cookie_validate(self):
        """验证Cookie"""
        print("\n🔍 验证Cookie...")
        cookie_manager = self.project_root / "scripts" / "cookie_manager.py"
        
        choice = input("输入Cookie字符串 (或按回车跳过): ").strip()
        if choice:
            subprocess.run([sys.executable, str(cookie_manager), "validate", "-c", choice])
        else:
            subprocess.run([sys.executable, str(cookie_manager), "validate"])
    
    def _cookie_backup(self):
        """备份.env文件"""
        print("\n📦 备份.env文件...")
        cookie_manager = self.project_root / "scripts" / "cookie_manager.py"
        subprocess.run([sys.executable, str(cookie_manager), "backup"])
    
    def _find_env_file(self) -> Optional[str]:
        """查找.env文件"""
        possible_paths = [
            self.project_root / ".env",
            Path.cwd() / ".env",
            Path.home() / ".env"
        ]
        
        for path in possible_paths:
            if path.exists():
                return str(path)
        
        return None
    
    def _read_cookies_from_env(self, env_path: str) -> str:
        """从.env文件读取Cookie"""
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('COOKIES_STR='):
                        return line[12:].strip()
            return ""
        except Exception:
            return ""
    
    def show_menu(self):
        """显示主菜单"""
        while True:
            self.print_banner()
            self.show_status()
            
            print("\n🛠️ 管理操作")
            print("=" * 30)
            print("1. 启动主程序 (前台)")
            print("2. 启动主程序 (后台)")
            print("3. 启动Web界面 (前台)")
            print("4. 启动Web界面 (后台)")
            print("5. 停止主程序")
            print("6. 停止Web界面")
            print("7. 重启主程序")
            print("8. 重启Web界面")
            print("9. 查看日志")
            print("10. Cookie管理")
            print("0. 退出")
            
            choice = input("\n请选择操作: ").strip()
            
            if choice == "1":
                self.start_service("main", background=False)
            elif choice == "2":
                self.start_service("main", background=True)
            elif choice == "3":
                self.start_service("web", background=False)
            elif choice == "4":
                self.start_service("web", background=True)
            elif choice == "5":
                self.stop_service("main")
            elif choice == "6":
                self.stop_service("web")
            elif choice == "7":
                self.restart_service("main", background=True)
            elif choice == "8":
                self.restart_service("web", background=True)
            elif choice == "9":
                self._log_menu()
            elif choice == "10":
                self.manage_cookies()
            elif choice == "0":
                print("👋 再见！")
                break
            else:
                print("❌ 无效选择")
            
            if choice != "0":
                input("\n按回车键继续...")
    
    def _log_menu(self):
        """日志查看菜单"""
        print("\n📄 日志查看")
        print("=" * 20)
        print("1. 查看主程序日志")
        print("2. 查看Web界面日志")
        print("3. 查看所有日志")
        
        choice = input("请选择: ").strip()
        lines = input("显示行数 (默认50): ").strip()
        lines = int(lines) if lines.isdigit() else 50
        
        if choice == "1":
            self.view_logs("main", lines)
        elif choice == "2":
            self.view_logs("web", lines)
        elif choice == "3":
            self.view_logs("all", lines)
        else:
            print("❌ 无效选择")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="闲鱼自动代理系统管理器")
    parser.add_argument("--status", action="store_true", help="只显示状态")
    parser.add_argument("--start", choices=["main", "web", "all"], help="启动服务")
    parser.add_argument("--stop", choices=["main", "web", "all"], help="停止服务")
    parser.add_argument("--restart", choices=["main", "web", "all"], help="重启服务")
    parser.add_argument("--background", action="store_true", help="在后台运行")
    parser.add_argument("--logs", choices=["main", "web", "all"], help="查看日志")
    
    args = parser.parse_args()
    
    manager = SystemManager()
    
    # 命令行模式
    if args.status:
        manager.print_banner()
        manager.show_status()
        return
    
    if args.start:
        if args.start == "all":
            manager.start_service("main", args.background)
            manager.start_service("web", args.background)
        else:
            manager.start_service(args.start, args.background)
        return
    
    if args.stop:
        if args.stop == "all":
            manager.stop_service("main")
            manager.stop_service("web")
        else:
            manager.stop_service(args.stop)
        return
    
    if args.restart:
        if args.restart == "all":
            manager.restart_service("main", args.background)
            manager.restart_service("web", args.background)
        else:
            manager.restart_service(args.restart, args.background)
        return
    
    if args.logs:
        manager.view_logs(args.logs)
        return
    
    # 交互模式
    try:
        manager.show_menu()
    except KeyboardInterrupt:
        print("\n👋 退出系统管理器")
    except Exception as e:
        print(f"❌ 系统管理器运行错误: {e}")


if __name__ == "__main__":
    main() 