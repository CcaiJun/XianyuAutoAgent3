#!/usr/bin/env python3
"""
XianyuAutoAgent2 重构版主启动文件
整合所有重构后的模块，提供统一的应用入口
"""

import os
import sys
import asyncio
import signal
from datetime import datetime
from config.logger_config import get_logger
from config.config_manager import ConfigManager
from web.app import create_app
from web.manager import WebManager

# 获取专用日志记录器
logger = get_logger("app", "main")


class XianyuAutoAgentApp:
    """
    闲鱼自动代理应用主类
    负责整合和管理所有模块
    """
    
    def __init__(self):
        """初始化应用"""
        self.config_manager = ConfigManager()
        self.web_manager = WebManager()
        self.flask_app = None
        self.socketio = None
        self._running = False
        
        # 设置信号处理
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """设置信号处理器"""
        def signal_handler(signum, frame):
            logger.info(f"收到信号 {signum}，准备优雅关闭...")
            self.shutdown()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def initialize(self):
        """初始化应用组件"""
        try:
            logger.info("开始初始化XianyuAutoAgent2应用...")
            
            # 检查必要的目录
            self._ensure_directories()
            
            # 检查环境变量
            self._check_environment()
            
            # 创建Flask应用
            self.flask_app, self.socketio = create_app()
            
            # 设置启动时间
            self.flask_app.config['START_TIME'] = datetime.now().isoformat()
            
            logger.info("XianyuAutoAgent2应用初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"应用初始化失败: {e}")
            return False
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        directories = [
            "config/prompts",
            "data",
            "logs",
            "web/templates",
            "web/static/css",
            "web/static/js"
        ]
        
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                logger.info(f"创建目录: {directory}")
    
    def _check_environment(self):
        """检查环境变量配置"""
        from dotenv import load_dotenv
        
        # 加载.env文件
        load_dotenv()
        
        # 检查关键环境变量
        required_env_vars = ['OPENAI_API_KEY']
        missing_vars = []
        
        for var in required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.warning(f"缺少环境变量: {missing_vars}")
            logger.warning("请检查.env文件配置")
        else:
            logger.info("环境变量检查通过")
    
    def run(self, host='0.0.0.0', port=8080, debug=False):
        """运行应用"""
        try:
            if not self.initialize():
                logger.error("应用初始化失败，退出")
                return False
            
            self._running = True
            
            logger.info(f"启动Web服务器: http://{host}:{port}")
            logger.info("Web管理界面访问地址: http://localhost:5000")
            logger.info("默认登录信息: admin/admin123")
            
            # 运行Flask应用
            self.socketio.run(
                self.flask_app,
                host=host,
                port=port,
                debug=debug,
                allow_unsafe_werkzeug=True
            )
            
        except Exception as e:
            logger.error(f"运行应用失败: {e}")
            return False
        finally:
            self.shutdown()
    
    def shutdown(self):
        """关闭应用"""
        if not self._running:
            return
            
        try:
            logger.info("开始关闭应用...")
            self._running = False
            
            # 关闭Web管理器
            if self.web_manager:
                try:
                    self.web_manager.stop_main_program()
                except:
                    pass
            
            logger.info("应用已关闭")
            
        except Exception as e:
            logger.error(f"关闭应用时出错: {e}")


def main():
    """主函数"""
    try:
        # 检查Python版本
        if sys.version_info < (3, 8):
            print("错误: 需要Python 3.8或更高版本")
            sys.exit(1)
        
        # 创建应用实例
        app = XianyuAutoAgentApp()
        
        # 运行应用
        success = app.run(
            host='0.0.0.0',
            port=8080,
            debug=False
        )
        
        if not success:
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("收到键盘中断，退出应用")
        sys.exit(0)
    except Exception as e:
        logger.error(f"应用运行异常: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main() 