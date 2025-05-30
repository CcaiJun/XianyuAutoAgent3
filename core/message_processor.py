"""
消息处理器模块
负责处理WebSocket收到的各类消息，包括消息解密、类型判断、路由分发等
"""

import json
import base64
import time
from typing import Dict, Any, Optional, Callable
from config.logger_config import get_logger
from config.settings import get_config
from utils.crypto_utils import decrypt
from utils.constants import MESSAGE_EXPIRE_TIME_DEFAULT

# 获取专用日志记录器
logger = get_logger("core", "message_processor")


class MessageProcessor:
    """
    消息处理器
    负责解析WebSocket消息、判断消息类型、提取关键信息并路由到相应处理器
    """
    
    def __init__(self, user_id: str):
        """
        初始化消息处理器
        
        Args:
            user_id: 当前用户ID（卖家ID）
        """
        self.config = get_config()
        self.xianyu_config = self.config.get_xianyu_config()
        
        self.user_id = user_id
        self.message_expire_time = self.xianyu_config.get('message_expire_time', MESSAGE_EXPIRE_TIME_DEFAULT)
        
        # 消息处理器回调
        self.chat_message_handler = None
        self.order_message_handler = None
        self.system_message_handler = None
        
        # 统计信息
        self.stats = {
            "total_messages": 0,
            "chat_messages": 0,
            "order_messages": 0,
            "system_messages": 0,
            "expired_messages": 0,
            "typing_notifications": 0,
            "decryption_failures": 0,
            "parse_failures": 0
        }
        
        logger.info(f"消息处理器初始化完成，用户ID: {self.user_id}")
    
    def set_chat_message_handler(self, handler: Callable):
        """
        设置聊天消息处理器
        
        Args:
            handler: 聊天消息处理函数
        """
        self.chat_message_handler = handler
        logger.debug("聊天消息处理器已设置")
    
    def set_order_message_handler(self, handler: Callable):
        """
        设置订单消息处理器
        
        Args:
            handler: 订单消息处理函数
        """
        self.order_message_handler = handler
        logger.debug("订单消息处理器已设置")
    
    def set_system_message_handler(self, handler: Callable):
        """
        设置系统消息处理器
        
        Args:
            handler: 系统消息处理函数
        """
        self.system_message_handler = handler
        logger.debug("系统消息处理器已设置")
    
    async def process_message(self, message_data: Dict[str, Any], websocket) -> bool:
        """
        处理WebSocket消息
        
        Args:
            message_data: 消息数据
            websocket: WebSocket连接对象
            
        Returns:
            是否成功处理
        """
        try:
            self.stats["total_messages"] += 1
            
            # 检查是否为同步包消息
            if not self._is_sync_package(message_data):
                logger.debug("非同步包消息，跳过处理")
                return True
            
            # 解密消息
            decrypted_message = self._decrypt_message(message_data)
            if not decrypted_message:
                self.stats["decryption_failures"] += 1
                logger.debug("消息解密失败，跳过处理")
                return False
            
            # 检查消息类型并路由
            if self._is_order_message(decrypted_message):
                await self._handle_order_message(decrypted_message)
                self.stats["order_messages"] += 1
                
            elif self._is_typing_notification(decrypted_message):
                logger.debug("用户正在输入通知")
                self.stats["typing_notifications"] += 1
                
            elif self._is_chat_message(decrypted_message):
                await self._handle_chat_message(decrypted_message, websocket)
                self.stats["chat_messages"] += 1
                
            elif self._is_system_message(decrypted_message):
                await self._handle_system_message(decrypted_message)
                self.stats["system_messages"] += 1
                
            else:
                logger.debug("未识别的消息类型")
                logger.debug(f"原始消息: {decrypted_message}")
            
            return True
            
        except Exception as e:
            self.stats["parse_failures"] += 1
            logger.error(f"处理消息异常: {e}")
            logger.debug(f"原始消息数据: {message_data}")
            return False
    
    def _is_sync_package(self, message_data: Dict[str, Any]) -> bool:
        """
        判断是否为同步包消息
        
        Args:
            message_data: 消息数据
            
        Returns:
            是否为同步包消息
        """
        try:
            return (
                isinstance(message_data, dict) and
                "body" in message_data and
                "syncPushPackage" in message_data["body"] and
                "data" in message_data["body"]["syncPushPackage"] and
                len(message_data["body"]["syncPushPackage"]["data"]) > 0
            )
        except Exception:
            return False
    
    def _decrypt_message(self, message_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        解密消息数据
        
        Args:
            message_data: 原始消息数据
            
        Returns:
            解密后的消息字典，失败返回None
        """
        try:
            sync_data = message_data["body"]["syncPushPackage"]["data"][0]
            
            if "data" not in sync_data:
                logger.debug("同步包中无data字段")
                return None
            
            data = sync_data["data"]
            
            # 尝试直接解析（未加密）
            try:
                decoded_data = base64.b64decode(data).decode("utf-8")
                return json.loads(decoded_data)
            except Exception:
                pass
            
            # 尝试解密
            try:
                decrypted_data = decrypt(data)
                return json.loads(decrypted_data)
            except Exception as e:
                logger.debug(f"消息解密失败: {e}")
                return None
                
        except Exception as e:
            logger.error(f"消息数据处理失败: {e}")
            return None
    
    def _is_order_message(self, message: Dict[str, Any]) -> bool:
        """
        判断是否为订单相关消息
        
        Args:
            message: 解密后的消息
            
        Returns:
            是否为订单消息
        """
        try:
            return (
                isinstance(message, dict) and
                "3" in message and
                isinstance(message["3"], dict) and
                "redReminder" in message["3"] and
                message["3"]["redReminder"] in [
                    "等待买家付款", "交易关闭", "等待卖家发货"
                ]
            )
        except Exception:
            return False
    
    def _is_typing_notification(self, message: Dict[str, Any]) -> bool:
        """
        判断是否为用户正在输入通知
        
        Args:
            message: 解密后的消息
            
        Returns:
            是否为输入通知
        """
        try:
            return (
                isinstance(message, dict) and
                "1" in message and
                isinstance(message["1"], list) and
                len(message["1"]) > 0 and
                isinstance(message["1"][0], dict) and
                "1" in message["1"][0] and
                isinstance(message["1"][0]["1"], str) and
                "@goofish" in message["1"][0]["1"]
            )
        except Exception:
            return False
    
    def _is_chat_message(self, message: Dict[str, Any]) -> bool:
        """
        判断是否为聊天消息
        
        Args:
            message: 解密后的消息
            
        Returns:
            是否为聊天消息
        """
        try:
            return (
                isinstance(message, dict) and
                "1" in message and
                isinstance(message["1"], dict) and
                "10" in message["1"] and
                isinstance(message["1"]["10"], dict) and
                "reminderContent" in message["1"]["10"]
            )
        except Exception:
            return False
    
    def _is_system_message(self, message: Dict[str, Any]) -> bool:
        """
        判断是否为系统消息
        
        Args:
            message: 解密后的消息
            
        Returns:
            是否为系统消息
        """
        try:
            return (
                isinstance(message, dict) and
                "3" in message and
                isinstance(message["3"], dict) and
                "needPush" in message["3"] and
                message["3"]["needPush"] == "false"
            )
        except Exception:
            return False
    
    def _is_message_expired(self, create_time: int) -> bool:
        """
        检查消息是否过期
        
        Args:
            create_time: 消息创建时间（毫秒时间戳）
            
        Returns:
            消息是否过期
        """
        current_time_ms = int(time.time() * 1000)
        return (current_time_ms - create_time) > self.message_expire_time
    
    async def _handle_order_message(self, message: Dict[str, Any]):
        """
        处理订单消息
        
        Args:
            message: 订单消息
        """
        try:
            order_status = message["3"]["redReminder"]
            user_id = message["1"].split('@')[0]
            user_url = f'https://www.goofish.com/personal?userId={user_id}'
            
            order_info = {
                "status": order_status,
                "user_id": user_id,
                "user_url": user_url,
                "timestamp": time.time()
            }
            
            logger.info(f"订单状态更新: {order_status} - 用户: {user_url}")
            
            # 调用订单消息处理器
            if self.order_message_handler:
                await self.order_message_handler(order_info)
                
        except Exception as e:
            logger.error(f"处理订单消息异常: {e}")
    
    async def _handle_chat_message(self, message: Dict[str, Any], websocket):
        """
        处理聊天消息
        
        Args:
            message: 聊天消息
            websocket: WebSocket连接对象
        """
        try:
            # 提取消息基本信息
            create_time = int(message["1"]["5"])
            send_user_name = message["1"]["10"]["reminderTitle"]
            send_user_id = message["1"]["10"]["senderUserId"]
            send_message = message["1"]["10"]["reminderContent"]
            
            # 检查消息是否过期
            if self._is_message_expired(create_time):
                logger.debug("过期消息，跳过处理")
                self.stats["expired_messages"] += 1
                return
            
            # 提取商品和会话信息
            url_info = message["1"]["10"]["reminderUrl"]
            item_id = url_info.split("itemId=")[1].split("&")[0] if "itemId=" in url_info else None
            chat_id = message["1"]["2"].split('@')[0]
            
            if not item_id:
                logger.warning("无法提取商品ID，跳过处理")
                return
            
            # 构建聊天消息信息
            chat_info = {
                "chat_id": chat_id,
                "item_id": item_id,
                "send_user_id": send_user_id,
                "send_user_name": send_user_name,
                "message_content": send_message,
                "create_time": create_time,
                "timestamp": time.time(),
                "is_from_seller": send_user_id == self.user_id
            }
            
            logger.info(f"聊天消息: 用户{send_user_name}({send_user_id}) -> 商品{item_id} -> 会话{chat_id}: {send_message}")
            
            # 调用聊天消息处理器
            if self.chat_message_handler:
                await self.chat_message_handler(chat_info, websocket)
                
        except Exception as e:
            logger.error(f"处理聊天消息异常: {e}")
    
    async def _handle_system_message(self, message: Dict[str, Any]):
        """
        处理系统消息
        
        Args:
            message: 系统消息
        """
        try:
            logger.debug("收到系统消息")
            
            # 调用系统消息处理器
            if self.system_message_handler:
                await self.system_message_handler(message)
                
        except Exception as e:
            logger.error(f"处理系统消息异常: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取消息处理统计信息
        
        Returns:
            统计信息字典
        """
        total_processed = sum([
            self.stats["chat_messages"],
            self.stats["order_messages"], 
            self.stats["system_messages"],
            self.stats["typing_notifications"]
        ])
        
        return {
            "total_messages": self.stats["total_messages"],
            "processed_messages": total_processed,
            "processing_rate": (
                total_processed / self.stats["total_messages"]
                if self.stats["total_messages"] > 0 else 0
            ),
            "message_types": {
                "chat_messages": self.stats["chat_messages"],
                "order_messages": self.stats["order_messages"],
                "system_messages": self.stats["system_messages"],
                "typing_notifications": self.stats["typing_notifications"]
            },
            "failures": {
                "decryption_failures": self.stats["decryption_failures"],
                "parse_failures": self.stats["parse_failures"],
                "expired_messages": self.stats["expired_messages"]
            },
            "failure_rate": (
                (self.stats["decryption_failures"] + self.stats["parse_failures"]) /
                self.stats["total_messages"] if self.stats["total_messages"] > 0 else 0
            )
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        获取消息处理器健康状态
        
        Returns:
            健康状态信息
        """
        health = {
            "status": "healthy",
            "checks": {
                "chat_handler_set": self.chat_message_handler is not None,
                "order_handler_set": self.order_message_handler is not None,
                "system_handler_set": self.system_message_handler is not None,
                "low_failure_rate": True,
                "processing_normally": True
            },
            "issues": []
        }
        
        # 检查失败率
        if self.stats["total_messages"] > 0:
            failure_rate = (
                (self.stats["decryption_failures"] + self.stats["parse_failures"]) /
                self.stats["total_messages"]
            )
            if failure_rate > 0.1:  # 失败率超过10%
                health["checks"]["low_failure_rate"] = False
                health["issues"].append(f"消息处理失败率过高: {failure_rate:.2%}")
        
        # 检查处理器是否设置
        if not health["checks"]["chat_handler_set"]:
            health["issues"].append("聊天消息处理器未设置")
        
        # 计算整体健康状态
        if health["issues"]:
            if len(health["issues"]) >= 2:
                health["status"] = "unhealthy"
            else:
                health["status"] = "degraded"
        
        return health
    
    def reset_statistics(self):
        """重置统计信息"""
        self.stats = {
            "total_messages": 0,
            "chat_messages": 0,
            "order_messages": 0,
            "system_messages": 0,
            "expired_messages": 0,
            "typing_notifications": 0,
            "decryption_failures": 0,
            "parse_failures": 0
        }
        logger.info("消息处理器统计信息已重置") 