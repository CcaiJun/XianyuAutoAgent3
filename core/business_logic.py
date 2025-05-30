"""
核心业务逻辑模块
统一管理和协调WebSocket连接、消息处理、会话管理等核心功能
"""

import asyncio
import time
from typing import Dict, Any, Optional
from config.logger_config import get_logger
from config.settings import get_config
from apis.api_manager import get_api_manager
from agents.agent_factory import get_agent_factory
from data.context_manager import ContextManager
from .websocket_manager import WebSocketManager
from .message_processor import MessageProcessor
from .session_manager import SessionManager
from utils.device_utils import trans_cookies, generate_device_id
from utils.constants import TOKEN_REFRESH_INTERVAL_DEFAULT, TOKEN_RETRY_INTERVAL_DEFAULT

# 获取专用日志记录器
logger = get_logger("core", "business")


class BusinessLogic:
    """
    核心业务逻辑
    统一管理和协调所有核心组件，提供完整的业务功能
    """
    
    def __init__(self):
        """初始化核心业务逻辑"""
        self.config = get_config()
        self.xianyu_config = self.config.get_xianyu_config()
        
        # 初始化基本信息
        self.cookies_str = self.xianyu_config['cookies_str']
        self.cookies = trans_cookies(self.cookies_str)
        self.user_id = self.cookies.get('unb', '')
        self.device_id = generate_device_id(self.user_id)
        
        # 核心组件
        self.api_manager = None
        self.agent_factory = None
        self.context_manager = None
        self.websocket_manager = None
        self.message_processor = None
        self.session_manager = None
        
        # 后台任务
        self.token_refresh_task = None
        self.connection_task = None
        self.running = False
        
        # Token管理
        self.token_refresh_interval = self.xianyu_config.get('token_refresh_interval', TOKEN_REFRESH_INTERVAL_DEFAULT)
        self.token_retry_interval = self.xianyu_config.get('token_retry_interval', TOKEN_RETRY_INTERVAL_DEFAULT)
        self.last_token_refresh_time = 0
        
        # 统计信息
        self.stats = {
            "start_time": 0,
            "total_uptime": 0,
            "connections": 0,
            "reconnections": 0,
            "messages_processed": 0,
            "auto_replies_sent": 0,
            "manual_interventions": 0,
            "token_refreshes": 0
        }
        
        logger.info(f"核心业务逻辑初始化完成，用户ID: {self.user_id}")
    
    async def initialize(self) -> bool:
        """
        初始化所有组件
        
        Returns:
            初始化是否成功
        """
        try:
            logger.info("开始初始化核心业务组件...")
            
            # 1. 初始化API管理器
            self.api_manager = get_api_manager()
            logger.info("API管理器初始化成功")
            
            # 2. 初始化代理工厂
            self.agent_factory = get_agent_factory()
            logger.info("代理工厂初始化成功")
            
            # 3. 初始化上下文管理器
            self.context_manager = ContextManager()
            logger.info("上下文管理器初始化成功")
            
            # 4. 初始化WebSocket管理器
            self.websocket_manager = WebSocketManager(
                user_id=self.user_id,
                device_id=self.device_id,
                cookies_str=self.cookies_str
            )
            logger.info("WebSocket管理器初始化成功")
            
            # 5. 初始化消息处理器
            self.message_processor = MessageProcessor(user_id=self.user_id)
            logger.info("消息处理器初始化成功")
            
            # 6. 初始化会话管理器
            self.session_manager = SessionManager(seller_id=self.user_id)
            logger.info("会话管理器初始化成功")
            
            # 7. 设置组件关联
            self._setup_component_connections()
            
            # 8. 验证初始状态
            if not await self._validate_initial_state():
                logger.error("初始状态验证失败")
                return False
            
            logger.info("核心业务组件初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"核心业务组件初始化失败: {e}")
            return False
    
    def _setup_component_connections(self):
        """设置组件之间的连接"""
        # 设置WebSocket消息处理器
        self.websocket_manager.set_message_handler(self.message_processor.process_message)
        
        # 设置消息处理器的回调
        self.message_processor.set_chat_message_handler(self._handle_chat_message)
        self.message_processor.set_order_message_handler(self._handle_order_message)
        self.message_processor.set_system_message_handler(self._handle_system_message)
        
        logger.debug("组件连接设置完成")
    
    async def _validate_initial_state(self) -> bool:
        """
        验证初始状态
        
        Returns:
            状态是否有效
        """
        try:
            # 验证登录状态
            if not self.api_manager.xianyu_client.validate_login_status():
                logger.error("闲鱼登录状态验证失败")
                return False
            
            # 验证AI连接
            if not self.api_manager.openai_manager.validate_connection():
                logger.error("AI连接验证失败")
                return False
            
            logger.info("初始状态验证通过")
            return True
            
        except Exception as e:
            logger.error(f"初始状态验证异常: {e}")
            return False
    
    async def start(self) -> bool:
        """
        启动业务逻辑
        
        Returns:
            启动是否成功
        """
        if self.running:
            logger.warning("业务逻辑已在运行中")
            return True
        
        try:
            logger.info("启动核心业务逻辑...")
            
            # 记录启动时间
            self.stats["start_time"] = time.time()
            self.running = True
            
            # 启动token刷新任务
            self.token_refresh_task = asyncio.create_task(self._token_refresh_loop())
            
            # 启动连接管理任务
            self.connection_task = asyncio.create_task(self._connection_loop())
            
            logger.info("核心业务逻辑启动成功")
            return True
            
        except Exception as e:
            logger.error(f"启动核心业务逻辑失败: {e}")
            self.running = False
            return False
    
    async def _connection_loop(self):
        """连接管理循环"""
        while self.running:
            try:
                # 清除重启标志
                self.websocket_manager.clear_restart_flag()
                
                # 建立WebSocket连接
                if await self.websocket_manager.connect():
                    self.stats["connections"] += 1
                    logger.info("WebSocket连接建立成功，开始监听消息...")
                    
                    # 监听消息
                    await self.websocket_manager.listen()
                    
                    # 连接断开后
                    if self.running:
                        self.stats["reconnections"] += 1
                        logger.warning("WebSocket连接断开，准备重连...")
                        
                        # 等待重连延迟
                        await asyncio.sleep(5)
                else:
                    logger.error("WebSocket连接失败，等待重试...")
                    await asyncio.sleep(10)
                    
            except Exception as e:
                logger.error(f"连接管理循环异常: {e}")
                await asyncio.sleep(10)
    
    async def _token_refresh_loop(self):
        """Token刷新循环"""
        while self.running:
            try:
                current_time = time.time()
                
                # 检查是否需要刷新token
                if current_time - self.last_token_refresh_time >= self.token_refresh_interval:
                    logger.info("Token即将过期，准备刷新...")
                    
                    if await self._refresh_token():
                        self.stats["token_refreshes"] += 1
                        self.last_token_refresh_time = current_time
                        
                        # 设置WebSocket重启标志
                        self.websocket_manager.set_restart_flag()
                        logger.info("Token刷新成功，WebSocket将重新连接")
                    else:
                        logger.error(f"Token刷新失败，将在{self.token_retry_interval}秒后重试")
                        await asyncio.sleep(self.token_retry_interval)
                        continue
                
                # 每分钟检查一次
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Token刷新循环异常: {e}")
                await asyncio.sleep(60)
    
    async def _refresh_token(self) -> bool:
        """
        刷新Token
        
        Returns:
            刷新是否成功
        """
        try:
            return self.api_manager.xianyu_client.refresh_token()
        except Exception as e:
            logger.error(f"Token刷新异常: {e}")
            return False
    
    async def _handle_chat_message(self, chat_info: Dict[str, Any], websocket):
        """
        处理聊天消息
        
        Args:
            chat_info: 聊天消息信息
            websocket: WebSocket连接对象
        """
        try:
            chat_id = chat_info["chat_id"]
            item_id = chat_info["item_id"]
            send_user_id = chat_info["send_user_id"]
            send_user_name = chat_info["send_user_name"]
            message_content = chat_info["message_content"]
            is_from_seller = chat_info["is_from_seller"]
            
            # 如果是卖家消息，交给会话管理器处理
            if is_from_seller:
                result = self.session_manager.handle_seller_message(chat_id, item_id, message_content)
                
                if result["is_toggle_command"]:
                    # 切换命令，不需要进一步处理
                    return
                else:
                    # 人工回复，记录到上下文
                    self.context_manager.add_message_by_chat(
                        chat_id, send_user_id, item_id, "assistant", message_content
                    )
                    self.stats["manual_interventions"] += 1
                    return
            
            # 用户消息处理
            # 添加用户消息到上下文
            self.context_manager.add_message_by_chat(
                chat_id, send_user_id, item_id, "user", message_content
            )
            
            # 检查是否处于人工接管模式
            if self.session_manager.is_manual_mode(chat_id):
                logger.info(f"🔴 会话 {chat_id} 处于人工接管模式，跳过自动回复")
                return
            
            # 获取商品信息
            item_info = await self._get_item_info(item_id)
            if not item_info:
                logger.warning(f"获取商品信息失败: {item_id}")
                return
            
            # 构建商品描述
            item_description = f"{item_info.get('desc', '')};当前商品售卖价格为:{item_info.get('soldPrice', '未知')}"
            
            # 获取对话上下文
            context = self.context_manager.get_context_by_chat(chat_id)
            
            # 生成AI回复
            ai_reply = await self._generate_ai_reply(message_content, item_description, context)
            if not ai_reply:
                logger.warning("AI回复生成失败")
                return
            
            # 检查是否为价格意图，更新议价次数
            # 这里需要从代理工厂获取最后的意图判断结果
            # 暂时简化处理，可以后续优化
            
            # 发送回复
            await self.websocket_manager.send_chat_message(chat_id, send_user_id, ai_reply)
            
            # 添加AI回复到上下文
            self.context_manager.add_message_by_chat(
                chat_id, self.user_id, item_id, "assistant", ai_reply
            )
            
            self.stats["auto_replies_sent"] += 1
            self.stats["messages_processed"] += 1
            
            logger.info(f"AI自动回复已发送: {ai_reply}")
            
        except Exception as e:
            logger.error(f"处理聊天消息异常: {e}")
    
    async def _handle_order_message(self, order_info: Dict[str, Any]):
        """
        处理订单消息
        
        Args:
            order_info: 订单信息
        """
        try:
            # 这里可以添加订单状态变化的业务逻辑
            # 比如通知、统计、自动发货等
            logger.info(f"订单状态更新: {order_info}")
            
        except Exception as e:
            logger.error(f"处理订单消息异常: {e}")
    
    async def _handle_system_message(self, message: Dict[str, Any]):
        """
        处理系统消息
        
        Args:
            message: 系统消息
        """
        try:
            # 系统消息处理逻辑
            logger.debug(f"收到系统消息: {message}")
            
        except Exception as e:
            logger.error(f"处理系统消息异常: {e}")
    
    async def _get_item_info(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        获取商品信息
        
        Args:
            item_id: 商品ID
            
        Returns:
            商品信息字典
        """
        try:
            # 先从缓存获取
            item_info = self.context_manager.get_item_info(item_id)
            if item_info:
                return item_info
            
            # 从API获取
            api_result = self.api_manager.get_xianyu_item_info(item_id)
            if api_result and 'data' in api_result and 'itemDO' in api_result['data']:
                item_info = api_result['data']['itemDO']
                # 保存到缓存
                self.context_manager.save_item_info(item_id, item_info)
                return item_info
            
            return None
            
        except Exception as e:
            logger.error(f"获取商品信息异常: {e}")
            return None
    
    async def _generate_ai_reply(self, user_message: str, item_description: str, context: list) -> Optional[str]:
        """
        生成AI回复
        
        Args:
            user_message: 用户消息
            item_description: 商品描述
            context: 对话上下文
            
        Returns:
            AI回复内容
        """
        try:
            # 使用代理工厂生成回复
            reply = await asyncio.to_thread(
                self.agent_factory.generate_reply,
                user_message=user_message,
                item_description=item_description,
                context=context
            )
            return reply
            
        except Exception as e:
            logger.error(f"生成AI回复异常: {e}")
            return None
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取业务逻辑状态
        
        Returns:
            状态信息字典
        """
        current_time = time.time()
        uptime = current_time - self.stats["start_time"] if self.stats["start_time"] > 0 else 0
        
        status = {
            "running": self.running,
            "uptime_seconds": uptime,
            "user_id": self.user_id,
            "device_id": self.device_id,
            "components": {
                "api_manager": self.api_manager is not None,
                "agent_factory": self.agent_factory is not None,
                "context_manager": self.context_manager is not None,
                "websocket_manager": self.websocket_manager is not None,
                "message_processor": self.message_processor is not None,
                "session_manager": self.session_manager is not None
            },
            "tasks": {
                "token_refresh_task": self.token_refresh_task is not None and not self.token_refresh_task.done(),
                "connection_task": self.connection_task is not None and not self.connection_task.done()
            },
            "statistics": self.stats.copy()
        }
        
        # 添加组件状态
        if self.websocket_manager:
            status["websocket"] = self.websocket_manager.get_connection_stats()
        
        if self.session_manager:
            status["sessions"] = self.session_manager.get_statistics()
        
        if self.message_processor:
            status["message_processing"] = self.message_processor.get_statistics()
        
        return status
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        获取健康状态
        
        Returns:
            健康状态信息
        """
        health = {
            "status": "healthy",
            "timestamp": time.time(),
            "components": {},
            "overall_issues": []
        }
        
        # 检查各组件健康状态
        if self.websocket_manager:
            health["components"]["websocket"] = self.websocket_manager.get_health_status()
        
        if self.message_processor:
            health["components"]["message_processor"] = self.message_processor.get_health_status()
        
        if self.session_manager:
            health["components"]["session_manager"] = self.session_manager.get_health_status()
        
        if self.api_manager:
            health["components"]["api_manager"] = self.api_manager.health_check()
        
        # 汇总状态
        component_statuses = []
        for component_name, component_health in health["components"].items():
            status = component_health.get("status", "unknown")
            component_statuses.append(status)
            
            # 收集问题
            if "issues" in component_health and component_health["issues"]:
                health["overall_issues"].extend([
                    f"{component_name}: {issue}" for issue in component_health["issues"]
                ])
        
        # 计算整体健康状态
        if "unhealthy" in component_statuses:
            health["status"] = "unhealthy"
        elif "degraded" in component_statuses:
            health["status"] = "degraded"
        
        # 检查运行状态
        if not self.running:
            health["status"] = "unhealthy"
            health["overall_issues"].append("业务逻辑未运行")
        
        return health
    
    def get_health_info(self) -> Dict[str, Any]:
        """
        获取健康信息（简化版本，兼容性方法）
        
        Returns:
            健康状态信息
        """
        current_time = time.time()
        uptime = current_time - self.stats["start_time"] if self.stats["start_time"] > 0 else 0
        
        return {
            "status": "healthy" if self.running else "stopped",
            "timestamp": current_time,
            "uptime_seconds": uptime,
            "user_id": self.user_id,
            "components_initialized": {
                "api_manager": self.api_manager is not None,
                "agent_factory": self.agent_factory is not None,
                "context_manager": self.context_manager is not None,
                "websocket_manager": self.websocket_manager is not None,
                "message_processor": self.message_processor is not None,
                "session_manager": self.session_manager is not None
            },
            "statistics": self.stats.copy(),
            "running_tasks": {
                "token_refresh_task": self.token_refresh_task is not None and not self.token_refresh_task.done(),
                "connection_task": self.connection_task is not None and not self.connection_task.done()
            }
        }
    
    async def stop(self):
        """停止业务逻辑"""
        logger.info("开始停止核心业务逻辑...")
        
        self.running = False
        
        # 停止后台任务
        if self.token_refresh_task and not self.token_refresh_task.done():
            self.token_refresh_task.cancel()
            try:
                await self.token_refresh_task
            except asyncio.CancelledError:
                pass
        
        if self.connection_task and not self.connection_task.done():
            self.connection_task.cancel()
            try:
                await self.connection_task
            except asyncio.CancelledError:
                pass
        
        # 关闭WebSocket连接
        if self.websocket_manager:
            await self.websocket_manager.shutdown()
        
        # 更新统计信息
        if self.stats["start_time"] > 0:
            self.stats["total_uptime"] += time.time() - self.stats["start_time"]
        
        logger.info("核心业务逻辑已停止")


# 全局业务逻辑实例
_business_logic = None


def get_business_logic() -> BusinessLogic:
    """
    获取全局业务逻辑实例（单例模式）
    
    Returns:
        业务逻辑实例
    """
    global _business_logic
    
    if _business_logic is None:
        _business_logic = BusinessLogic()
    
    return _business_logic 