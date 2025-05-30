"""
API管理器模块
统一协调和管理所有API客户端，提供统一的API调用接口
"""

import time
from typing import Dict, Any, Optional
from config.logger_config import get_logger
from .xianyu_apis import XianyuAPIClient
from .openai_client import OpenAIClientManager
from .auth_manager import AuthManager

# 获取专用日志记录器
logger = get_logger("api", "manager")


class APIManager:
    """
    API管理器
    统一管理和协调所有API客户端，提供统一的接口和健康监控
    """
    
    def __init__(self):
        """初始化API管理器"""
        # 初始化各个组件
        self.auth_manager = AuthManager()
        self.xianyu_client = None
        self.openai_manager = None
        
        # 初始化状态
        self.initialized = False
        self.last_health_check = 0
        self.health_check_interval = 300  # 5分钟检查一次
        
        # 统计信息
        self.stats = {
            "total_api_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "last_call_time": 0
        }
        
        logger.info("API管理器初始化开始")
    
    def initialize(self) -> bool:
        """
        初始化所有API客户端
        
        Returns:
            初始化是否成功
        """
        try:
            logger.info("开始初始化API客户端...")
            
            # 1. 验证认证信息
            xianyu_auth = self.auth_manager.validate_xianyu_auth()
            openai_auth = self.auth_manager.validate_openai_auth()
            
            if not xianyu_auth["authenticated"]:
                logger.error(f"闲鱼认证失败: {xianyu_auth.get('error', '未知错误')}")
                return False
            
            if not openai_auth["authenticated"]:
                logger.error(f"OpenAI认证失败: {openai_auth.get('error', '未知错误')}")
                return False
            
            # 2. 初始化闲鱼客户端
            try:
                self.xianyu_client = XianyuAPIClient()
                logger.info("闲鱼API客户端初始化成功")
            except Exception as e:
                logger.error(f"闲鱼API客户端初始化失败: {e}")
                return False
            
            # 3. 初始化OpenAI客户端
            try:
                self.openai_manager = OpenAIClientManager()
                logger.info("OpenAI客户端管理器初始化成功")
            except Exception as e:
                logger.error(f"OpenAI客户端管理器初始化失败: {e}")
                return False
            
            # 4. 验证连接
            if not self._validate_all_connections():
                logger.error("API连接验证失败")
                return False
            
            self.initialized = True
            logger.info("API管理器初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"API管理器初始化异常: {e}")
            return False
    
    def _validate_all_connections(self) -> bool:
        """
        验证所有API连接
        
        Returns:
            所有连接是否有效
        """
        try:
            # 验证闲鱼连接
            if not self.xianyu_client.validate_login_status():
                logger.error("闲鱼API连接验证失败")
                return False
            
            # 验证OpenAI连接
            if not self.openai_manager.validate_connection():
                logger.error("OpenAI API连接验证失败")
                return False
            
            logger.debug("所有API连接验证成功")
            return True
            
        except Exception as e:
            logger.error(f"API连接验证异常: {e}")
            return False
    
    def get_xianyu_item_info(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        获取闲鱼商品信息
        
        Args:
            item_id: 商品ID
            
        Returns:
            商品信息字典
        """
        if not self._check_initialized():
            return None
        
        self.stats["total_api_calls"] += 1
        self.stats["last_call_time"] = time.time()
        
        try:
            result = self.xianyu_client.get_item_info(item_id)
            
            if result and "error" not in result:
                self.stats["successful_calls"] += 1
                logger.debug(f"成功获取商品信息: {item_id}")
            else:
                self.stats["failed_calls"] += 1
                logger.warning(f"获取商品信息失败: {item_id}")
            
            return result
            
        except Exception as e:
            self.stats["failed_calls"] += 1
            logger.error(f"获取商品信息异常: {e}")
            return None
    
    def get_xianyu_token(self) -> Optional[str]:
        """
        获取闲鱼访问令牌
        
        Returns:
            访问令牌
        """
        if not self._check_initialized():
            return None
        
        try:
            return self.xianyu_client.get_current_token()
        except Exception as e:
            logger.error(f"获取闲鱼token异常: {e}")
            return None
    
    def create_ai_completion(self, messages, **kwargs) -> Optional[str]:
        """
        创建AI完成请求
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
            
        Returns:
            AI生成的内容
        """
        if not self._check_initialized():
            return None
        
        self.stats["total_api_calls"] += 1
        self.stats["last_call_time"] = time.time()
        
        try:
            response = self.openai_manager.create_chat_completion(messages, **kwargs)
            
            if response and response.choices:
                self.stats["successful_calls"] += 1
                logger.debug("AI完成请求成功")
                return response.choices[0].message.content
            else:
                self.stats["failed_calls"] += 1
                logger.warning("AI完成请求失败")
                return None
                
        except Exception as e:
            self.stats["failed_calls"] += 1
            logger.error(f"AI完成请求异常: {e}")
            return None
    
    def create_session(self, user_id: str, session_data: Dict[str, Any] = None) -> Optional[str]:
        """
        创建用户会话
        
        Args:
            user_id: 用户ID
            session_data: 会话数据
            
        Returns:
            会话ID
        """
        try:
            return self.auth_manager.create_session(user_id, session_data)
        except Exception as e:
            logger.error(f"创建会话异常: {e}")
            return None
    
    def validate_session(self, session_id: str) -> bool:
        """
        验证会话有效性
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话是否有效
        """
        try:
            valid, _ = self.auth_manager.validate_session(session_id)
            return valid
        except Exception as e:
            logger.error(f"验证会话异常: {e}")
            return False
    
    def _check_initialized(self) -> bool:
        """
        检查是否已正确初始化
        
        Returns:
            是否已初始化
        """
        if not self.initialized:
            logger.error("API管理器未初始化")
            return False
        
        if not self.xianyu_client or not self.openai_manager:
            logger.error("API客户端未正确初始化")
            return False
        
        return True
    
    def periodic_health_check(self) -> Dict[str, Any]:
        """
        定期健康检查
        
        Returns:
            健康检查结果
        """
        current_time = time.time()
        
        # 检查是否需要进行健康检查
        if current_time - self.last_health_check < self.health_check_interval:
            return {"skipped": True, "reason": "未到检查时间"}
        
        self.last_health_check = current_time
        return self.health_check()
    
    def health_check(self) -> Dict[str, Any]:
        """
        完整的健康检查
        
        Returns:
            健康状态信息
        """
        health = {
            "status": "healthy",
            "timestamp": time.time(),
            "components": {},
            "overall_issues": []
        }
        
        try:
            # 检查认证管理器
            auth_health = self.auth_manager.health_check()
            health["components"]["auth_manager"] = auth_health
            
            # 检查闲鱼客户端
            if self.xianyu_client:
                xianyu_health = self.xianyu_client.health_check()
                health["components"]["xianyu_client"] = xianyu_health
            else:
                health["components"]["xianyu_client"] = {"status": "not_initialized"}
                health["overall_issues"].append("闲鱼客户端未初始化")
            
            # 检查OpenAI客户端
            if self.openai_manager:
                openai_health = self.openai_manager.health_check()
                health["components"]["openai_manager"] = openai_health
            else:
                health["components"]["openai_manager"] = {"status": "not_initialized"}
                health["overall_issues"].append("OpenAI客户端未初始化")
            
            # 汇总状态
            component_statuses = [comp.get("status", "unknown") for comp in health["components"].values()]
            
            if "unhealthy" in component_statuses:
                health["status"] = "unhealthy"
            elif "degraded" in component_statuses:
                health["status"] = "degraded"
            
            # 汇总问题
            for component_name, component_health in health["components"].items():
                if "issues" in component_health and component_health["issues"]:
                    health["overall_issues"].extend([
                        f"{component_name}: {issue}" for issue in component_health["issues"]
                    ])
            
            logger.debug(f"健康检查完成，状态: {health['status']}")
            
        except Exception as e:
            health["status"] = "error"
            health["overall_issues"].append(f"健康检查异常: {e}")
            logger.error(f"健康检查异常: {e}")
        
        return health
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取API使用统计信息
        
        Returns:
            统计信息字典
        """
        stats = {
            "api_manager": {
                "initialized": self.initialized,
                "total_api_calls": self.stats["total_api_calls"],
                "successful_calls": self.stats["successful_calls"],
                "failed_calls": self.stats["failed_calls"],
                "success_rate": (
                    self.stats["successful_calls"] / self.stats["total_api_calls"]
                    if self.stats["total_api_calls"] > 0 else 0
                ),
                "last_call_time": self.stats["last_call_time"],
                "last_health_check": self.last_health_check
            },
            "components": {}
        }
        
        # 获取各组件统计信息
        if self.auth_manager:
            stats["components"]["auth_manager"] = self.auth_manager.get_session_statistics()
        
        if self.xianyu_client:
            stats["components"]["xianyu_client"] = self.xianyu_client.get_api_statistics()
        
        if self.openai_manager:
            stats["components"]["openai_manager"] = self.openai_manager.get_statistics()
        
        return stats
    
    def refresh_connections(self) -> bool:
        """
        刷新所有API连接
        
        Returns:
            刷新是否成功
        """
        try:
            logger.info("开始刷新API连接...")
            
            # 刷新闲鱼token
            if self.xianyu_client:
                if not self.xianyu_client.refresh_token():
                    logger.warning("闲鱼token刷新失败")
            
            # 验证OpenAI连接
            if self.openai_manager:
                if not self.openai_manager.validate_connection():
                    logger.warning("OpenAI连接验证失败")
            
            # 清理过期会话
            if self.auth_manager:
                cleaned_sessions = self.auth_manager.cleanup_expired_sessions()
                if cleaned_sessions > 0:
                    logger.info(f"清理了 {cleaned_sessions} 个过期会话")
            
            logger.info("API连接刷新完成")
            return True
            
        except Exception as e:
            logger.error(f"API连接刷新异常: {e}")
            return False
    
    def shutdown(self):
        """关闭API管理器，清理资源"""
        logger.info("开始关闭API管理器...")
        
        # 清理各个组件
        if self.xianyu_client:
            # 闲鱼客户端的清理
            self.xianyu_client = None
        
        if self.openai_manager:
            # OpenAI客户端的清理
            self.openai_manager = None
        
        if self.auth_manager:
            # 清理所有会话
            self.auth_manager.cleanup_expired_sessions()
            self.auth_manager = None
        
        self.initialized = False
        logger.info("API管理器已关闭")


# 全局API管理器实例
_api_manager = None


def get_api_manager() -> APIManager:
    """
    获取全局API管理器实例（单例模式）
    
    Returns:
        API管理器实例
    """
    global _api_manager
    
    if _api_manager is None:
        _api_manager = APIManager()
        if not _api_manager.initialize():
            logger.error("API管理器初始化失败")
            raise RuntimeError("API管理器初始化失败")
    
    return _api_manager 