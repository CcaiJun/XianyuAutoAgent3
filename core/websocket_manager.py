"""
WebSocket连接管理器
负责WebSocket连接的建立、维护、心跳检测和重连机制
"""

import json
import time
import asyncio
import websockets
from typing import Dict, Any, Optional, Callable
from config.logger_config import get_logger
from config.settings import get_config
from utils.device_utils import generate_mid
from utils.constants import (
    WEBSOCKET_BASE_URL, WEBSOCKET_TIMEOUT, WEBSOCKET_PING_INTERVAL,
    DEFAULT_USER_AGENT, HEARTBEAT_INTERVAL_DEFAULT, HEARTBEAT_TIMEOUT_DEFAULT
)

# 获取专用日志记录器
logger = get_logger("core", "websocket")


class WebSocketManager:
    """
    WebSocket连接管理器
    负责与闲鱼WebSocket服务的连接管理、心跳维护和消息收发
    """
    
    def __init__(self, user_id: str, device_id: str, cookies_str: str):
        """
        初始化WebSocket管理器
        
        Args:
            user_id: 用户ID
            device_id: 设备ID
            cookies_str: Cookie字符串
        """
        self.config = get_config()
        self.xianyu_config = self.config.get_xianyu_config()
        
        # 连接信息
        self.user_id = user_id
        self.device_id = device_id
        self.cookies_str = cookies_str
        self.base_url = WEBSOCKET_BASE_URL
        
        # 连接状态
        self.websocket = None
        self.connected = False
        self.connection_task = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        self.reconnect_delay = 5  # 重连延迟（秒）
        
        # 心跳管理
        self.heartbeat_interval = self.xianyu_config.get('heartbeat_interval', HEARTBEAT_INTERVAL_DEFAULT)
        self.heartbeat_timeout = self.xianyu_config.get('heartbeat_timeout', HEARTBEAT_TIMEOUT_DEFAULT)
        self.last_heartbeat_time = 0
        self.last_heartbeat_response = 0
        self.heartbeat_task = None
        
        # 消息处理
        self.message_handler = None
        self.connection_restart_flag = False
        
        # 统计信息
        self.stats = {
            "total_connections": 0,
            "successful_connections": 0,
            "failed_connections": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "heartbeats_sent": 0,
            "heartbeats_received": 0,
            "reconnections": 0
        }
        
        logger.info(f"WebSocket管理器初始化完成，用户ID: {self.user_id}")
    
    def set_message_handler(self, handler: Callable):
        """
        设置消息处理回调函数
        
        Args:
            handler: 消息处理函数，接收(message_data, websocket)参数
        """
        self.message_handler = handler
        logger.debug("消息处理器已设置")
    
    async def connect(self) -> bool:
        """
        建立WebSocket连接
        
        Returns:
            连接是否成功
        """
        try:
            self.stats["total_connections"] += 1
            logger.info("开始建立WebSocket连接...")
            
            # 准备连接头部
            headers = self._prepare_headers()
            
            # 建立连接
            self.websocket = await websockets.connect(
                self.base_url,
                extra_headers=headers,
                timeout=WEBSOCKET_TIMEOUT,
                ping_interval=WEBSOCKET_PING_INTERVAL
            )
            
            # 初始化连接
            if await self._initialize_connection():
                self.connected = True
                self.reconnect_attempts = 0
                self.stats["successful_connections"] += 1
                
                # 启动心跳任务
                await self._start_heartbeat()
                
                logger.info("WebSocket连接建立成功")
                return True
            else:
                await self._close_connection()
                self.stats["failed_connections"] += 1
                logger.error("WebSocket连接初始化失败")
                return False
                
        except Exception as e:
            self.stats["failed_connections"] += 1
            logger.error(f"WebSocket连接失败: {e}")
            return False
    
    def _prepare_headers(self) -> Dict[str, str]:
        """准备WebSocket连接头部"""
        return {
            "Cookie": self.cookies_str,
            "Host": "wss-goofish.dingtalk.com",
            "Connection": "Upgrade",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
            "User-Agent": DEFAULT_USER_AGENT,
            "Origin": "https://www.goofish.com",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
    
    async def _initialize_connection(self) -> bool:
        """
        初始化WebSocket连接
        
        Returns:
            初始化是否成功
        """
        try:
            # 发送注册消息
            register_msg = {
                "lwp": "/reg",
                "headers": {
                    "cache-header": "app-key token ua wv",
                    "app-key": "444e9908a51d1cb236a27862abc769c9",
                    "token": "",  # Token将在需要时更新
                    "ua": DEFAULT_USER_AGENT,
                    "dt": "j",
                    "wv": "im:3,au:3,sy:6",
                    "sync": "0,0;0;0;",
                    "did": self.device_id,
                    "mid": generate_mid()
                }
            }
            
            await self._send_message(register_msg)
            
            # 等待注册完成
            await asyncio.sleep(1)
            
            # 发送同步状态消息
            sync_msg = {
                "lwp": "/r/SyncStatus/ackDiff",
                "headers": {"mid": "5701741704675979 0"},
                "body": [{
                    "pipeline": "sync",
                    "tooLong2Tag": "PNM,1",
                    "channel": "sync",
                    "topic": "sync",
                    "highPts": 0,
                    "pts": int(time.time() * 1000) * 1000,
                    "seq": 0,
                    "timestamp": int(time.time() * 1000)
                }]
            }
            
            await self._send_message(sync_msg)
            
            logger.info("WebSocket连接初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"WebSocket连接初始化异常: {e}")
            return False
    
    async def _send_message(self, message: Dict[str, Any]):
        """
        发送消息到WebSocket
        
        Args:
            message: 要发送的消息字典
        """
        if not self.websocket:
            raise RuntimeError("WebSocket连接未建立")
        
        try:
            message_json = json.dumps(message, separators=(',', ':'))
            await self.websocket.send(message_json)
            self.stats["messages_sent"] += 1
            logger.debug(f"消息已发送: {message.get('lwp', 'unknown')}")
            
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            raise
    
    async def send_chat_message(self, chat_id: str, to_user_id: str, content: str):
        """
        发送聊天消息
        
        Args:
            chat_id: 会话ID
            to_user_id: 接收用户ID
            content: 消息内容
        """
        try:
            import base64
            from utils.device_utils import generate_uuid
            
            # 构建消息内容
            text_data = {
                "contentType": 1,
                "text": {"text": content}
            }
            
            text_base64 = base64.b64encode(
                json.dumps(text_data, separators=(',', ':')).encode('utf-8')
            ).decode('utf-8')
            
            # 构建发送消息
            message = {
                "lwp": "/r/MessageSend/sendByReceiverScope",
                "headers": {"mid": generate_mid()},
                "body": [
                    {
                        "uuid": generate_uuid(),
                        "cid": f"{chat_id}@goofish",
                        "conversationType": 1,
                        "content": {
                            "contentType": 101,
                            "custom": {
                                "type": 1,
                                "data": text_base64
                            }
                        },
                        "redPointPolicy": 0,
                        "extension": {"extJson": "{}"},
                        "ctx": {
                            "appVersion": "1.0",
                            "platform": "web"
                        },
                        "mtags": {},
                        "msgReadStatusSetting": 1
                    },
                    {
                        "actualReceivers": [
                            f"{to_user_id}@goofish",
                            f"{self.user_id}@goofish"
                        ]
                    }
                ]
            }
            
            await self._send_message(message)
            logger.info(f"聊天消息已发送到用户 {to_user_id}: {content}")
            
        except Exception as e:
            logger.error(f"发送聊天消息失败: {e}")
            raise
    
    async def _start_heartbeat(self):
        """启动心跳任务"""
        if self.heartbeat_task and not self.heartbeat_task.done():
            self.heartbeat_task.cancel()
        
        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self.last_heartbeat_time = time.time()
        self.last_heartbeat_response = time.time()
        logger.debug("心跳任务已启动")
    
    async def _heartbeat_loop(self):
        """心跳循环"""
        while self.connected:
            try:
                current_time = time.time()
                
                # 检查是否需要发送心跳
                if current_time - self.last_heartbeat_time >= self.heartbeat_interval:
                    await self._send_heartbeat()
                
                # 检查心跳响应超时
                if (current_time - self.last_heartbeat_response) > (self.heartbeat_interval + self.heartbeat_timeout):
                    logger.warning("心跳响应超时，连接可能已断开")
                    break
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"心跳循环异常: {e}")
                break
        
        logger.debug("心跳循环已停止")
    
    async def _send_heartbeat(self):
        """发送心跳包"""
        try:
            heartbeat_msg = {
                "lwp": "/!",
                "headers": {"mid": generate_mid()}
            }
            
            await self._send_message(heartbeat_msg)
            self.last_heartbeat_time = time.time()
            self.stats["heartbeats_sent"] += 1
            logger.debug("心跳包已发送")
            
        except Exception as e:
            logger.error(f"发送心跳包失败: {e}")
            raise
    
    def _handle_heartbeat_response(self, message_data: Dict[str, Any]) -> bool:
        """
        处理心跳响应
        
        Args:
            message_data: 收到的消息数据
            
        Returns:
            是否为心跳响应
        """
        try:
            if (isinstance(message_data, dict) and
                "headers" in message_data and
                "mid" in message_data["headers"] and
                "code" in message_data and
                message_data["code"] == 200):
                
                self.last_heartbeat_response = time.time()
                self.stats["heartbeats_received"] += 1
                logger.debug("收到心跳响应")
                return True
                
        except Exception as e:
            logger.error(f"处理心跳响应失败: {e}")
        
        return False
    
    async def listen(self):
        """
        监听WebSocket消息
        """
        if not self.websocket or not self.connected:
            raise RuntimeError("WebSocket未连接")
        
        logger.info("开始监听WebSocket消息...")
        
        try:
            async for message in self.websocket:
                try:
                    # 检查连接重启标志
                    if self.connection_restart_flag:
                        logger.info("检测到连接重启标志，准备重新建立连接...")
                        break
                    
                    message_data = json.loads(message)
                    self.stats["messages_received"] += 1
                    
                    # 处理心跳响应
                    if self._handle_heartbeat_response(message_data):
                        continue
                    
                    # 发送通用ACK响应
                    await self._send_ack_response(message_data)
                    
                    # 调用消息处理器
                    if self.message_handler:
                        await self.message_handler(message_data, self.websocket)
                    
                except json.JSONDecodeError:
                    logger.error("消息JSON解析失败")
                except Exception as e:
                    logger.error(f"处理消息异常: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket连接已关闭")
            self.connected = False
        except Exception as e:
            logger.error(f"WebSocket监听异常: {e}")
            self.connected = False
    
    async def _send_ack_response(self, message_data: Dict[str, Any]):
        """
        发送ACK响应
        
        Args:
            message_data: 收到的消息数据
        """
        try:
            if "headers" in message_data and "mid" in message_data["headers"]:
                ack = {
                    "code": 200,
                    "headers": {
                        "mid": message_data["headers"]["mid"],
                        "sid": message_data["headers"].get("sid", "")
                    }
                }
                
                # 复制其他必要的header字段
                for key in ["app-key", "ua", "dt"]:
                    if key in message_data["headers"]:
                        ack["headers"][key] = message_data["headers"][key]
                
                await self._send_message(ack)
                
        except Exception as e:
            logger.debug(f"发送ACK响应失败: {e}")
    
    async def reconnect(self) -> bool:
        """
        重新连接WebSocket
        
        Returns:
            重连是否成功
        """
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error(f"重连次数超过最大限制 {self.max_reconnect_attempts}")
            return False
        
        self.reconnect_attempts += 1
        self.stats["reconnections"] += 1
        
        logger.info(f"开始第 {self.reconnect_attempts} 次重连...")
        
        # 关闭现有连接
        await self._close_connection()
        
        # 等待重连延迟
        await asyncio.sleep(self.reconnect_delay)
        
        # 尝试重新连接
        return await self.connect()
    
    async def _close_connection(self):
        """关闭WebSocket连接"""
        self.connected = False
        
        # 停止心跳任务
        if self.heartbeat_task and not self.heartbeat_task.done():
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass
        
        # 关闭WebSocket连接
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception as e:
                logger.debug(f"关闭WebSocket连接时出错: {e}")
            finally:
                self.websocket = None
        
        logger.debug("WebSocket连接已关闭")
    
    def set_restart_flag(self):
        """设置连接重启标志"""
        self.connection_restart_flag = True
        logger.info("连接重启标志已设置")
    
    def clear_restart_flag(self):
        """清除连接重启标志"""
        self.connection_restart_flag = False
        logger.debug("连接重启标志已清除")
    
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self.connected and self.websocket is not None
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """
        获取连接统计信息
        
        Returns:
            连接统计数据
        """
        return {
            "connected": self.connected,
            "reconnect_attempts": self.reconnect_attempts,
            "connection_restart_flag": self.connection_restart_flag,
            "stats": self.stats.copy(),
            "heartbeat": {
                "interval": self.heartbeat_interval,
                "timeout": self.heartbeat_timeout,
                "last_heartbeat_time": self.last_heartbeat_time,
                "last_heartbeat_response": self.last_heartbeat_response,
                "time_since_last_heartbeat": time.time() - self.last_heartbeat_response
            }
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        获取连接健康状态
        
        Returns:
            健康状态信息
        """
        current_time = time.time()
        health = {
            "status": "healthy",
            "checks": {
                "connected": self.is_connected(),
                "heartbeat_normal": (current_time - self.last_heartbeat_response) < (self.heartbeat_interval + self.heartbeat_timeout),
                "reconnect_limit_ok": self.reconnect_attempts < self.max_reconnect_attempts,
                "message_handler_set": self.message_handler is not None
            },
            "issues": []
        }
        
        # 检查各项状态
        if not health["checks"]["connected"]:
            health["issues"].append("WebSocket未连接")
        
        if not health["checks"]["heartbeat_normal"]:
            health["issues"].append("心跳异常")
        
        if not health["checks"]["reconnect_limit_ok"]:
            health["issues"].append("重连次数过多")
        
        if not health["checks"]["message_handler_set"]:
            health["issues"].append("消息处理器未设置")
        
        # 计算整体状态
        if health["issues"]:
            if len(health["issues"]) >= 3:
                health["status"] = "unhealthy"
            else:
                health["status"] = "degraded"
        
        return health
    
    async def shutdown(self):
        """关闭WebSocket管理器"""
        logger.info("开始关闭WebSocket管理器...")
        await self._close_connection()
        logger.info("WebSocket管理器已关闭") 