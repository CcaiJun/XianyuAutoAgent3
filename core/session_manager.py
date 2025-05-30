"""
会话管理器模块
负责管理用户会话状态、人工接管模式、会话切换等功能
"""

import time
from typing import Dict, Any, Set, Optional
from config.logger_config import get_logger
from config.settings import get_config
from utils.constants import MANUAL_MODE_TIMEOUT_DEFAULT

# 获取专用日志记录器
logger = get_logger("core", "session")


class SessionManager:
    """
    会话管理器
    管理用户会话状态、人工接管模式、会话切换等功能
    """
    
    def __init__(self, seller_id: str):
        """
        初始化会话管理器
        
        Args:
            seller_id: 卖家用户ID
        """
        self.config = get_config()
        self.xianyu_config = self.config.get_xianyu_config()
        
        self.seller_id = seller_id
        
        # 人工接管配置
        self.toggle_keywords = self.xianyu_config.get('toggle_keywords', '。')
        self.manual_mode_timeout = self.xianyu_config.get('manual_mode_timeout', MANUAL_MODE_TIMEOUT_DEFAULT)
        
        # 会话状态管理
        self.manual_mode_conversations = set()  # 处于人工接管模式的会话ID
        self.manual_mode_timestamps = {}  # 进入人工模式的时间戳
        self.session_data = {}  # 会话数据存储
        
        # 统计信息
        self.stats = {
            "total_sessions": 0,
            "manual_sessions": 0,
            "auto_sessions": 0,
            "mode_switches": 0,
            "timeout_exits": 0,
            "manual_exits": 0
        }
        
        logger.info(f"会话管理器初始化完成，卖家ID: {self.seller_id}")
        logger.info(f"人工接管切换关键词: {self.toggle_keywords}")
        logger.info(f"人工接管超时时间: {self.manual_mode_timeout}秒")
    
    def is_manual_mode(self, chat_id: str) -> bool:
        """
        检查指定会话是否处于人工接管模式
        
        Args:
            chat_id: 会话ID
            
        Returns:
            是否处于人工接管模式
        """
        if chat_id not in self.manual_mode_conversations:
            return False
        
        # 检查是否超时
        current_time = time.time()
        if chat_id in self.manual_mode_timestamps:
            if current_time - self.manual_mode_timestamps[chat_id] > self.manual_mode_timeout:
                # 超时，自动退出人工模式
                self._exit_manual_mode_internal(chat_id, reason="超时")
                self.stats["timeout_exits"] += 1
                return False
        
        return True
    
    def enter_manual_mode(self, chat_id: str, reason: str = "手动切换") -> bool:
        """
        进入人工接管模式
        
        Args:
            chat_id: 会话ID
            reason: 进入原因
            
        Returns:
            是否成功进入
        """
        try:
            if chat_id not in self.manual_mode_conversations:
                self.stats["total_sessions"] += 1
            
            self.manual_mode_conversations.add(chat_id)
            self.manual_mode_timestamps[chat_id] = time.time()
            self.stats["manual_sessions"] += 1
            self.stats["mode_switches"] += 1
            
            # 更新会话数据
            self._update_session_data(chat_id, {
                "mode": "manual",
                "mode_changed_time": time.time(),
                "mode_change_reason": reason
            })
            
            logger.info(f"🔴 会话 {chat_id} 进入人工接管模式，原因: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"进入人工接管模式失败: {e}")
            return False
    
    def exit_manual_mode(self, chat_id: str, reason: str = "手动切换") -> bool:
        """
        退出人工接管模式
        
        Args:
            chat_id: 会话ID
            reason: 退出原因
            
        Returns:
            是否成功退出
        """
        try:
            result = self._exit_manual_mode_internal(chat_id, reason)
            if result:
                self.stats["manual_exits"] += 1
                self.stats["mode_switches"] += 1
            return result
            
        except Exception as e:
            logger.error(f"退出人工接管模式失败: {e}")
            return False
    
    def _exit_manual_mode_internal(self, chat_id: str, reason: str) -> bool:
        """
        内部退出人工接管模式方法
        
        Args:
            chat_id: 会话ID
            reason: 退出原因
            
        Returns:
            是否成功退出
        """
        was_in_manual = chat_id in self.manual_mode_conversations
        
        self.manual_mode_conversations.discard(chat_id)
        if chat_id in self.manual_mode_timestamps:
            del self.manual_mode_timestamps[chat_id]
        
        if was_in_manual:
            self.stats["auto_sessions"] += 1
            
            # 更新会话数据
            self._update_session_data(chat_id, {
                "mode": "auto",
                "mode_changed_time": time.time(),
                "mode_change_reason": reason
            })
            
            logger.info(f"🟢 会话 {chat_id} 退出人工接管模式，原因: {reason}")
            return True
        
        return False
    
    def toggle_manual_mode(self, chat_id: str) -> str:
        """
        切换会话的人工接管模式
        
        Args:
            chat_id: 会话ID
            
        Returns:
            切换后的模式 ("manual" 或 "auto")
        """
        if self.is_manual_mode(chat_id):
            self.exit_manual_mode(chat_id, "切换命令")
            return "auto"
        else:
            self.enter_manual_mode(chat_id, "切换命令")
            return "manual"
    
    def check_toggle_keywords(self, message: str) -> bool:
        """
        检查消息是否包含切换关键词
        
        Args:
            message: 消息内容
            
        Returns:
            是否包含切换关键词
        """
        message_stripped = message.strip()
        return message_stripped in self.toggle_keywords
    
    def handle_seller_message(self, chat_id: str, item_id: str, message: str) -> Dict[str, Any]:
        """
        处理卖家发送的消息
        
        Args:
            chat_id: 会话ID
            item_id: 商品ID
            message: 消息内容
            
        Returns:
            处理结果
        """
        result = {
            "is_toggle_command": False,
            "is_manual_reply": False,
            "mode_changed": False,
            "current_mode": "auto"
        }
        
        try:
            # 检查是否为切换命令
            if self.check_toggle_keywords(message):
                old_mode = "manual" if self.is_manual_mode(chat_id) else "auto"
                new_mode = self.toggle_manual_mode(chat_id)
                
                result["is_toggle_command"] = True
                result["mode_changed"] = True
                result["current_mode"] = new_mode
                result["old_mode"] = old_mode
                
                logger.info(f"检测到模式切换命令 - 会话 {chat_id}: {old_mode} -> {new_mode}")
            else:
                # 记录为人工回复
                result["is_manual_reply"] = True
                result["current_mode"] = "manual" if self.is_manual_mode(chat_id) else "auto"
                
                # 更新会话活动时间
                self._update_session_activity(chat_id)
                
                logger.info(f"卖家人工回复 - 会话 {chat_id}, 商品 {item_id}: {message}")
            
            return result
            
        except Exception as e:
            logger.error(f"处理卖家消息异常: {e}")
            return result
    
    def get_session_info(self, chat_id: str) -> Dict[str, Any]:
        """
        获取会话信息
        
        Args:
            chat_id: 会话ID
            
        Returns:
            会话信息字典
        """
        is_manual = self.is_manual_mode(chat_id)
        current_time = time.time()
        
        session_info = {
            "chat_id": chat_id,
            "mode": "manual" if is_manual else "auto",
            "is_manual_mode": is_manual,
            "manual_start_time": self.manual_mode_timestamps.get(chat_id),
            "manual_duration": 0,
            "time_until_timeout": 0
        }
        
        # 计算人工模式持续时间和剩余时间
        if is_manual and chat_id in self.manual_mode_timestamps:
            start_time = self.manual_mode_timestamps[chat_id]
            session_info["manual_duration"] = current_time - start_time
            session_info["time_until_timeout"] = max(0, self.manual_mode_timeout - session_info["manual_duration"])
        
        # 添加会话数据
        if chat_id in self.session_data:
            session_info.update(self.session_data[chat_id])
        
        return session_info
    
    def cleanup_expired_sessions(self) -> int:
        """
        清理过期的会话
        
        Returns:
            清理的会话数量
        """
        current_time = time.time()
        expired_sessions = []
        
        # 查找过期的人工模式会话
        for chat_id, start_time in self.manual_mode_timestamps.items():
            if current_time - start_time > self.manual_mode_timeout:
                expired_sessions.append(chat_id)
        
        # 清理过期会话
        cleaned_count = 0
        for chat_id in expired_sessions:
            if self._exit_manual_mode_internal(chat_id, "超时清理"):
                cleaned_count += 1
                self.stats["timeout_exits"] += 1
        
        # 清理长时间未活动的会话数据
        session_timeout = 24 * 3600  # 24小时
        inactive_sessions = []
        
        for chat_id, data in self.session_data.items():
            last_activity = data.get("last_activity", 0)
            if current_time - last_activity > session_timeout:
                inactive_sessions.append(chat_id)
        
        for chat_id in inactive_sessions:
            del self.session_data[chat_id]
            cleaned_count += 1
        
        if cleaned_count > 0:
            logger.info(f"清理了 {cleaned_count} 个过期会话")
        
        return cleaned_count
    
    def _update_session_data(self, chat_id: str, data: Dict[str, Any]):
        """
        更新会话数据
        
        Args:
            chat_id: 会话ID
            data: 要更新的数据
        """
        if chat_id not in self.session_data:
            self.session_data[chat_id] = {}
        
        self.session_data[chat_id].update(data)
        self.session_data[chat_id]["last_activity"] = time.time()
    
    def _update_session_activity(self, chat_id: str):
        """
        更新会话活动时间
        
        Args:
            chat_id: 会话ID
        """
        self._update_session_data(chat_id, {"last_activity": time.time()})
    
    def get_all_manual_sessions(self) -> Set[str]:
        """
        获取所有处于人工接管模式的会话ID
        
        Returns:
            人工接管会话ID集合
        """
        # 先清理过期会话
        self.cleanup_expired_sessions()
        return self.manual_mode_conversations.copy()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取会话管理统计信息
        
        Returns:
            统计信息字典
        """
        current_manual_sessions = len(self.manual_mode_conversations)
        
        return {
            "current_sessions": {
                "total_active": len(self.session_data),
                "manual_mode": current_manual_sessions,
                "auto_mode": len(self.session_data) - current_manual_sessions
            },
            "historical_stats": {
                "total_sessions": self.stats["total_sessions"],
                "manual_sessions": self.stats["manual_sessions"],
                "auto_sessions": self.stats["auto_sessions"],
                "mode_switches": self.stats["mode_switches"]
            },
            "mode_exits": {
                "timeout_exits": self.stats["timeout_exits"],
                "manual_exits": self.stats["manual_exits"]
            },
            "configuration": {
                "toggle_keywords": self.toggle_keywords,
                "manual_mode_timeout": self.manual_mode_timeout,
                "seller_id": self.seller_id
            }
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        获取会话管理器健康状态
        
        Returns:
            健康状态信息
        """
        current_time = time.time()
        health = {
            "status": "healthy",
            "checks": {
                "session_data_normal": True,
                "manual_sessions_normal": True,
                "timeout_rate_normal": True,
                "configuration_valid": True
            },
            "issues": []
        }
        
        # 检查会话数据一致性
        try:
            manual_count = len(self.manual_mode_conversations)
            timestamp_count = len(self.manual_mode_timestamps)
            
            if manual_count != timestamp_count:
                health["checks"]["session_data_normal"] = False
                health["issues"].append(f"会话数据不一致: {manual_count} vs {timestamp_count}")
                
        except Exception as e:
            health["checks"]["session_data_normal"] = False
            health["issues"].append(f"会话数据检查异常: {e}")
        
        # 检查人工模式会话数量
        if len(self.manual_mode_conversations) > 100:  # 假设阈值为100
            health["checks"]["manual_sessions_normal"] = False
            health["issues"].append("人工模式会话过多")
        
        # 检查超时退出率
        if self.stats["mode_switches"] > 0:
            timeout_rate = self.stats["timeout_exits"] / self.stats["mode_switches"]
            if timeout_rate > 0.5:  # 超时退出率超过50%
                health["checks"]["timeout_rate_normal"] = False
                health["issues"].append(f"超时退出率过高: {timeout_rate:.2%}")
        
        # 检查配置有效性
        if not self.toggle_keywords or not isinstance(self.manual_mode_timeout, (int, float)):
            health["checks"]["configuration_valid"] = False
            health["issues"].append("配置无效")
        
        # 计算整体状态
        if health["issues"]:
            if len(health["issues"]) >= 3:
                health["status"] = "unhealthy"
            else:
                health["status"] = "degraded"
        
        return health
    
    def reset_statistics(self):
        """重置统计信息"""
        self.stats = {
            "total_sessions": 0,
            "manual_sessions": 0,
            "auto_sessions": 0,
            "mode_switches": 0,
            "timeout_exits": 0,
            "manual_exits": 0
        }
        logger.info("会话管理器统计信息已重置")
    
    def force_exit_all_manual_modes(self) -> int:
        """
        强制退出所有人工接管模式
        
        Returns:
            退出的会话数量
        """
        manual_sessions = self.manual_mode_conversations.copy()
        count = 0
        
        for chat_id in manual_sessions:
            if self.exit_manual_mode(chat_id, "强制退出"):
                count += 1
        
        logger.info(f"强制退出了 {count} 个人工接管会话")
        return count 