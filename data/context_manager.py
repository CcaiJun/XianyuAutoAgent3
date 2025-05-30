"""
上下文管理器模块
负责整合数据库和缓存，提供统一的数据访问接口
"""

import asyncio
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from config.logger_config import get_logger
from config.config_manager import ConfigManager
from .database_manager import DatabaseManager
from .cache_manager import CacheManager
from .data_models import MessageModel, ItemModel, BargainModel, SessionModel

# 获取专用日志记录器
logger = get_logger("data", "context")


class ContextManager:
    """
    统一的上下文管理器
    整合数据库操作和缓存管理，提供高层数据访问接口
    """
    
    def __init__(self, max_history: int = 100):
        """
        初始化上下文管理器
        
        Args:
            max_history: 每个对话保留的最大消息数
        """
        self.max_history = max_history
        self.config_manager = ConfigManager()
        
        # 初始化数据管理器
        self.db_manager = DatabaseManager()
        self.cache_manager = CacheManager(
            max_size=1000,
            default_ttl=3600  # 1小时默认缓存时间
        )
        
        self._initialized = False
    
    async def initialize(self):
        """初始化上下文管理器"""
        try:
            if self._initialized:
                return
                
            await self.db_manager.initialize()
            await self.cache_manager.start()
            
            self._initialized = True
            logger.info("上下文管理器初始化完成")
            
        except Exception as e:
            logger.error(f"上下文管理器初始化失败: {e}")
            raise
    
    async def close(self):
        """关闭上下文管理器"""
        try:
            await self.cache_manager.stop()
            await self.db_manager.close()
            
            self._initialized = False
            logger.info("上下文管理器已关闭")
            
        except Exception as e:
            logger.error(f"关闭上下文管理器失败: {e}")
    
    # === 消息管理 ===
    
    async def add_message_by_chat(
        self, 
        chat_id: str, 
        user_id: str, 
        item_id: str, 
        role: str, 
        content: str
    ) -> bool:
        """
        添加消息到对话历史
        
        Args:
            chat_id: 会话ID
            user_id: 用户ID
            item_id: 商品ID
            role: 消息角色 (user/assistant/system)
            content: 消息内容
            
        Returns:
            是否添加成功
        """
        try:
            # 创建消息模型
            message = MessageModel(
                chat_id=chat_id,
                user_id=user_id,
                item_id=item_id,
                role=role,
                content=content
            )
            
            # 保存到数据库
            success = await self.db_manager.save_message(message.to_dict())
            
            if success:
                # 更新缓存中的消息列表
                cache_key = f"messages_{chat_id}"
                cached_messages = self.cache_manager.get('messages', cache_key) or []
                cached_messages.append({
                    "role": role,
                    "content": content,
                    "timestamp": message.timestamp
                })
                
                # 保持消息数量限制
                if len(cached_messages) > self.max_history:
                    cached_messages = cached_messages[-self.max_history:]
                
                self.cache_manager.set('messages', cache_key, cached_messages)
                
                # 更新会话活动
                await self._update_session_activity(chat_id, is_ai=(role == "assistant"))
                
                logger.debug(f"添加消息成功: {chat_id}/{role}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"添加消息失败: {e}")
            return False
    
    async def get_context_by_chat(self, chat_id: str) -> List[Dict[str, Any]]:
        """
        获取对话历史上下文
        
        Args:
            chat_id: 会话ID
            
        Returns:
            消息列表
        """
        try:
            # 先从缓存获取
            cache_key = f"messages_{chat_id}"
            cached_messages = self.cache_manager.get('messages', cache_key)
            
            if cached_messages is not None:
                logger.debug(f"从缓存获取对话历史: {chat_id}")
                return cached_messages
            
            # 从数据库获取
            messages = await self.db_manager.get_messages_by_chat(chat_id, self.max_history)
            
            # 转换格式
            context_messages = []
            for msg in messages:
                context_messages.append({
                    "role": msg['role'],
                    "content": msg['content'],
                    "timestamp": msg['timestamp']
                })
            
            # 添加议价信息
            bargain_info = await self.get_bargain_by_chat(chat_id)
            if bargain_info and bargain_info.count > 0:
                context_messages.append({
                    "role": "system",
                    "content": bargain_info.get_bargain_context(),
                    "timestamp": time.time()
                })
            
            # 缓存结果
            self.cache_manager.set('messages', cache_key, context_messages)
            
            logger.debug(f"从数据库获取对话历史: {chat_id}, 消息数: {len(context_messages)}")
            return context_messages
            
        except Exception as e:
            logger.error(f"获取对话历史失败: {e}")
            return []
    
    # === 商品管理 ===
    
    async def save_item_info(self, item_id: str, item_data: Dict[str, Any]) -> bool:
        """
        保存商品信息
        
        Args:
            item_id: 商品ID
            item_data: 商品数据
            
        Returns:
            是否保存成功
        """
        try:
            # 创建商品模型
            if 'item_id' not in item_data:
                item_data['item_id'] = item_id
                
            item = ItemModel.from_api_data(item_id, item_data)
            
            # 保存到数据库
            success = await self.db_manager.save_item(item.to_dict())
            
            if success:
                # 更新缓存
                self.cache_manager.set_item(item_id, item.to_dict())
                logger.debug(f"保存商品信息成功: {item_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"保存商品信息失败: {e}")
            return False
    
    async def get_item_info(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        获取商品信息
        
        Args:
            item_id: 商品ID
            
        Returns:
            商品信息字典
        """
        try:
            # 先从缓存获取
            cached_item = self.cache_manager.get_item(item_id)
            if cached_item:
                logger.debug(f"从缓存获取商品信息: {item_id}")
                return cached_item
            
            # 从数据库获取
            item_data = await self.db_manager.get_item(item_id)
            
            if item_data:
                # 缓存结果
                self.cache_manager.set_item(item_id, item_data)
                logger.debug(f"从数据库获取商品信息: {item_id}")
                return item_data
            
            return None
            
        except Exception as e:
            logger.error(f"获取商品信息失败: {e}")
            return None
    
    # === 议价管理 ===
    
    async def increment_bargain_count_by_chat(self, chat_id: str, content: str = "") -> bool:
        """
        增加议价次数
        
        Args:
            chat_id: 会话ID
            content: 议价内容
            
        Returns:
            是否增加成功
        """
        try:
            # 获取现有议价信息
            bargain = await self.get_bargain_by_chat(chat_id)
            
            if bargain is None:
                # 创建新的议价记录
                # 需要从会话信息获取用户ID和商品ID
                session_info = await self.get_session_by_chat(chat_id)
                if not session_info:
                    logger.warning(f"无法找到会话信息: {chat_id}")
                    return False
                
                bargain = BargainModel(
                    chat_id=chat_id,
                    item_id=session_info.item_id,
                    user_id=session_info.user_id
                )
            
            # 增加计数
            bargain.increment_count(content)
            
            # 保存到数据库
            success = await self.db_manager.save_bargain(bargain.to_dict())
            
            if success:
                # 更新缓存
                self.cache_manager.set_bargain(chat_id, bargain.to_dict())
                
                # 清除消息缓存，强制重新获取包含议价信息的上下文
                cache_key = f"messages_{chat_id}"
                self.cache_manager.delete('messages', cache_key)
                
                logger.debug(f"增加议价次数成功: {chat_id}, 当前次数: {bargain.count}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"增加议价次数失败: {e}")
            return False
    
    async def get_bargain_count_by_chat(self, chat_id: str) -> int:
        """
        获取议价次数
        
        Args:
            chat_id: 会话ID
            
        Returns:
            议价次数
        """
        try:
            bargain = await self.get_bargain_by_chat(chat_id)
            return bargain.count if bargain else 0
            
        except Exception as e:
            logger.error(f"获取议价次数失败: {e}")
            return 0
    
    async def get_bargain_by_chat(self, chat_id: str) -> Optional[BargainModel]:
        """
        获取议价信息
        
        Args:
            chat_id: 会话ID
            
        Returns:
            议价模型实例
        """
        try:
            # 先从缓存获取
            cached_bargain = self.cache_manager.get_bargain(chat_id)
            if cached_bargain:
                return BargainModel.from_dict(cached_bargain)
            
            # 从数据库获取
            bargain_data = await self.db_manager.get_bargain(chat_id)
            
            if bargain_data:
                bargain = BargainModel.from_dict(bargain_data)
                # 缓存结果
                self.cache_manager.set_bargain(chat_id, bargain.to_dict())
                return bargain
            
            return None
            
        except Exception as e:
            logger.error(f"获取议价信息失败: {e}")
            return None
    
    # === 会话管理 ===
    
    async def create_session(
        self, 
        chat_id: str, 
        user_id: str, 
        item_id: str
    ) -> bool:
        """
        创建新会话
        
        Args:
            chat_id: 会话ID
            user_id: 用户ID
            item_id: 商品ID
            
        Returns:
            是否创建成功
        """
        try:
            session = SessionModel(
                chat_id=chat_id,
                user_id=user_id,
                item_id=item_id
            )
            
            success = await self.db_manager.save_session(session.to_dict())
            
            if success:
                # 缓存会话信息
                self.cache_manager.set_session(chat_id, session.to_dict())
                logger.debug(f"创建会话成功: {chat_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"创建会话失败: {e}")
            return False
    
    async def get_session_by_chat(self, chat_id: str) -> Optional[SessionModel]:
        """
        获取会话信息
        
        Args:
            chat_id: 会话ID
            
        Returns:
            会话模型实例
        """
        try:
            # 先从缓存获取
            cached_session = self.cache_manager.get_session(chat_id)
            if cached_session:
                return SessionModel.from_dict(cached_session)
            
            # 从数据库获取
            session_data = await self.db_manager.get_session(chat_id)
            
            if session_data:
                session = SessionModel.from_dict(session_data)
                # 缓存结果
                self.cache_manager.set_session(chat_id, session.to_dict())
                return session
            
            return None
            
        except Exception as e:
            logger.error(f"获取会话信息失败: {e}")
            return None
    
    async def _update_session_activity(
        self, 
        chat_id: str, 
        is_manual: bool = False, 
        is_ai: bool = False
    ):
        """
        更新会话活动信息
        
        Args:
            chat_id: 会话ID
            is_manual: 是否为人工操作
            is_ai: 是否为AI响应
        """
        try:
            session = await self.get_session_by_chat(chat_id)
            if session:
                session.update_activity(is_manual=is_manual, is_ai=is_ai)
                
                # 保存更新
                await self.db_manager.save_session(session.to_dict())
                
                # 更新缓存
                self.cache_manager.set_session(chat_id, session.to_dict())
            
        except Exception as e:
            logger.error(f"更新会话活动失败: {e}")
    
    async def switch_session_mode(self, chat_id: str, new_mode: str) -> bool:
        """
        切换会话模式
        
        Args:
            chat_id: 会话ID
            new_mode: 新模式 (auto/manual)
            
        Returns:
            是否切换成功
        """
        try:
            session = await self.get_session_by_chat(chat_id)
            if not session:
                return False
            
            session.switch_mode(new_mode)
            
            # 保存更新
            success = await self.db_manager.save_session(session.to_dict())
            
            if success:
                # 更新缓存
                self.cache_manager.set_session(chat_id, session.to_dict())
                logger.info(f"会话模式切换成功: {chat_id} -> {new_mode}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"切换会话模式失败: {e}")
            return False
    
    # === 统计和健康检查 ===
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        try:
            # 获取数据库统计
            db_stats = await self.db_manager.get_statistics()
            
            # 获取缓存统计
            cache_stats = self.cache_manager.get_stats()
            
            return {
                "database": db_stats,
                "cache": cache_stats,
                "initialized": self._initialized
            }
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}
    
    def get_health_info(self) -> Dict[str, Any]:
        """
        获取健康状态信息
        
        Returns:
            健康状态字典
        """
        return {
            "status": "healthy" if self._initialized else "initializing",
            "database": self.db_manager.get_health_info(),
            "cache": self.cache_manager.get_health_info()
        }
    
    # === 数据清理 ===
    
    async def cleanup_old_data(self, days: int = 30) -> Dict[str, int]:
        """
        清理旧数据
        
        Args:
            days: 保留天数
            
        Returns:
            清理结果字典
        """
        try:
            # 清理数据库
            db_cleaned = await self.db_manager.cleanup_old_data(days)
            
            # 清理缓存
            cache_cleaned = self.cache_manager.clear_all()
            
            result = {
                "database_cleaned": db_cleaned,
                "cache_cleared": cache_cleaned
            }
            
            logger.info(f"数据清理完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"数据清理失败: {e}")
            return {"database_cleaned": 0, "cache_cleared": 0} 