#!/usr/bin/env python3
"""
XianyuAutoAgent2 主程序
这是一个简化版的主程序，用于演示Web管理器的功能
实际使用时，这里应该包含完整的闲鱼自动代理逻辑
"""

import asyncio
import time
import signal
import sys
from datetime import datetime
from config.logger_config import get_logger
from config.config_manager import ConfigManager
from agents import AgentFactory
from apis import APIManager
from core import BusinessLogic
from data import ContextManager

# 获取专用日志记录器
logger = get_logger("app", "main")


class XianyuAutoAgent:
    """
    闲鱼自动代理主程序
    """
    
    def __init__(self):
        """初始化主程序"""
        self.config_manager = ConfigManager()
        self.context_manager = ContextManager()
        self.api_manager = APIManager()
        self.agent_factory = AgentFactory()
        self.business_logic = None
        self._running = False
        self._heartbeat_task = None
        
        # 设置信号处理
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """设置信号处理器"""
        def signal_handler(signum, frame):
            logger.info(f"收到信号 {signum}，准备优雅关闭...")
            asyncio.create_task(self.shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def initialize(self):
        """初始化所有组件"""
        try:
            logger.info("开始初始化XianyuAutoAgent...")
            
            # 初始化数据管理器
            await self.context_manager.initialize()
            
            # 初始化API管理器 - 这是同步方法，不需要await
            if not self.api_manager.initialize():
                logger.error("API管理器初始化失败")
                return False
            
            # 初始化业务逻辑
            from core.business_logic import BusinessLogic
            self.business_logic = BusinessLogic()
            if not await self.business_logic.initialize():
                logger.error("业务逻辑初始化失败")
                return False
            
            logger.info("XianyuAutoAgent初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            return False
    
    async def start_heartbeat(self):
        """启动心跳任务"""
        async def heartbeat_loop():
            while self._running:
                try:
                    logger.debug("心跳包已发送")
                    await asyncio.sleep(30)  # 每30秒发送一次心跳
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"心跳异常: {e}")
                    await asyncio.sleep(60)
        
        self._heartbeat_task = asyncio.create_task(heartbeat_loop())
    
    async def run(self):
        """运行主程序"""
        try:
            if not await self.initialize():
                logger.error("初始化失败，退出")
                return False
            
            self._running = True
            logger.info("XianyuAutoAgent已启动")
            
            # 启动心跳
            await self.start_heartbeat()
            
            # 模拟主要业务循环
            await self._main_loop()
            
        except Exception as e:
            logger.error(f"运行异常: {e}")
            return False
        finally:
            await self.shutdown()
    
    async def _main_loop(self):
        """主要业务循环"""
        logger.info("开始主要业务循环...")
        
        while self._running:
            try:
                # 这里应该包含实际的业务逻辑
                # 目前只是一个演示循环
                
                logger.info("执行业务逻辑检查...")
                
                # 模拟一些工作
                await asyncio.sleep(10)
                
                # 检查系统健康状态
                if self.business_logic:
                    health_info = self.business_logic.get_health_info()
                    logger.debug(f"系统健康状态: {health_info}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"业务循环异常: {e}")
                await asyncio.sleep(30)  # 出错时延迟重试
    
    async def shutdown(self):
        """关闭主程序"""
        if not self._running:
            return
            
        try:
            logger.info("开始关闭主程序...")
            self._running = False
            
            # 取消心跳任务
            if self._heartbeat_task:
                self._heartbeat_task.cancel()
                try:
                    await self._heartbeat_task
                except asyncio.CancelledError:
                    pass
            
            # 关闭业务逻辑
            if self.business_logic:
                await self.business_logic.close()
            
            # 关闭API管理器
            await self.api_manager.close()
            
            # 关闭数据管理器
            await self.context_manager.close()
            
            logger.info("主程序已关闭")
            
        except Exception as e:
            logger.error(f"关闭主程序时出错: {e}")


async def main():
    """主函数"""
    try:
        # 检查Python版本
        if sys.version_info < (3, 8):
            print("错误: 需要Python 3.8或更高版本")
            sys.exit(1)
        
        # 创建主程序实例
        agent = XianyuAutoAgent()
        
        # 运行主程序
        success = await agent.run()
        
        if not success:
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("收到键盘中断，退出程序")
        sys.exit(0)
    except Exception as e:
        logger.error(f"程序运行异常: {e}")
        sys.exit(1)


if __name__ == '__main__':
    # 运行异步主函数
    asyncio.run(main())
