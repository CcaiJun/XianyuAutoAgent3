"""
认证管理器模块
统一管理项目中所有的认证信息、会话状态和安全验证
"""

import time
import hashlib
import secrets
from typing import Dict, Any, Optional, Tuple
from config.logger_config import get_logger
from config.settings import get_config
from utils.validation_utils import validate_cookies
from utils.constants import SESSION_LIFETIME_HOURS

# 获取专用日志记录器
logger = get_logger("api", "auth")


class AuthManager:
    """
    认证管理器
    统一管理API认证、会话状态、权限验证等安全相关功能
    """
    
    def __init__(self):
        """初始化认证管理器"""
        self.config = get_config()
        
        # 会话管理
        self.active_sessions = {}  # 存储活跃会话
        self.session_lifetime = SESSION_LIFETIME_HOURS * 3600  # 会话生命周期（秒）
        
        # 认证状态
        self.auth_status = {
            "xianyu_authenticated": False,
            "openai_authenticated": False,
            "last_auth_check": 0,
            "auth_errors": []
        }
        
        # 安全配置
        self.security_config = {
            "max_login_attempts": 5,
            "lockout_duration": 300,  # 5分钟锁定时间
            "failed_attempts": {},
            "locked_accounts": {}
        }
        
        logger.info("认证管理器初始化完成")
    
    def validate_xianyu_auth(self) -> Dict[str, Any]:
        """
        验证闲鱼认证状态
        
        Returns:
            验证结果字典
        """
        try:
            xianyu_config = self.config.get_xianyu_config()
            cookies_str = xianyu_config.get('cookies_str', '')
            
            # 验证cookies格式
            validation_result = validate_cookies(cookies_str)
            
            if not validation_result["valid"]:
                self.auth_status["xianyu_authenticated"] = False
                self.auth_status["auth_errors"].append(f"闲鱼Cookies验证失败: {validation_result['warnings']}")
                logger.warning("闲鱼认证验证失败")
                return {
                    "authenticated": False,
                    "error": "Cookies格式无效",
                    "details": validation_result["warnings"]
                }
            
            # 检查必要字段
            required_fields = ['unb']  # 闲鱼必需的字段
            cookies_dict = {}
            for cookie in cookies_str.split("; "):
                if "=" in cookie:
                    key, value = cookie.split('=', 1)
                    cookies_dict[key.strip()] = value.strip()
            
            missing_fields = [field for field in required_fields if field not in cookies_dict]
            if missing_fields:
                self.auth_status["xianyu_authenticated"] = False
                error_msg = f"缺少必需的cookie字段: {missing_fields}"
                self.auth_status["auth_errors"].append(error_msg)
                logger.warning(f"闲鱼认证验证失败: {error_msg}")
                return {
                    "authenticated": False,
                    "error": error_msg,
                    "missing_fields": missing_fields
                }
            
            # 验证成功
            self.auth_status["xianyu_authenticated"] = True
            self.auth_status["last_auth_check"] = time.time()
            logger.debug("闲鱼认证验证成功")
            
            return {
                "authenticated": True,
                "user_id": cookies_dict.get('unb', ''),
                "cookies_count": validation_result["parsed_count"]
            }
            
        except Exception as e:
            error_msg = f"闲鱼认证验证异常: {e}"
            self.auth_status["auth_errors"].append(error_msg)
            logger.error(error_msg)
            return {
                "authenticated": False,
                "error": error_msg
            }
    
    def validate_openai_auth(self) -> Dict[str, Any]:
        """
        验证OpenAI认证状态
        
        Returns:
            验证结果字典
        """
        try:
            openai_config = self.config.get_openai_config()
            api_key = openai_config.get('api_key', '')
            base_url = openai_config.get('base_url', '')
            
            # 检查API密钥格式
            if not api_key:
                self.auth_status["openai_authenticated"] = False
                error_msg = "OpenAI API密钥未设置"
                self.auth_status["auth_errors"].append(error_msg)
                logger.warning(error_msg)
                return {
                    "authenticated": False,
                    "error": error_msg
                }
            
            # 检查API密钥格式（简单验证）
            if len(api_key) < 20:
                self.auth_status["openai_authenticated"] = False
                error_msg = "OpenAI API密钥格式无效"
                self.auth_status["auth_errors"].append(error_msg)
                logger.warning(error_msg)
                return {
                    "authenticated": False,
                    "error": error_msg
                }
            
            # 检查base_url
            if not base_url:
                self.auth_status["openai_authenticated"] = False
                error_msg = "OpenAI base_url未设置"
                self.auth_status["auth_errors"].append(error_msg)
                logger.warning(error_msg)
                return {
                    "authenticated": False,
                    "error": error_msg
                }
            
            # 验证成功
            self.auth_status["openai_authenticated"] = True
            self.auth_status["last_auth_check"] = time.time()
            logger.debug("OpenAI认证验证成功")
            
            return {
                "authenticated": True,
                "api_key_length": len(api_key),
                "base_url": base_url,
                "model_name": openai_config.get('model_name', 'unknown')
            }
            
        except Exception as e:
            error_msg = f"OpenAI认证验证异常: {e}"
            self.auth_status["auth_errors"].append(error_msg)
            logger.error(error_msg)
            return {
                "authenticated": False,
                "error": error_msg
            }
    
    def create_session(self, user_id: str, session_data: Dict[str, Any] = None) -> str:
        """
        创建新的会话
        
        Args:
            user_id: 用户ID
            session_data: 会话数据
            
        Returns:
            会话ID
        """
        try:
            # 生成会话ID
            session_id = self._generate_session_id(user_id)
            
            # 准备会话数据
            session_info = {
                "user_id": user_id,
                "created_time": time.time(),
                "last_activity": time.time(),
                "data": session_data or {},
                "ip_address": None,  # 可以后续添加IP跟踪
                "user_agent": None   # 可以后续添加用户代理跟踪
            }
            
            # 存储会话
            self.active_sessions[session_id] = session_info
            
            logger.info(f"创建新会话: {session_id[:8]}..., 用户: {user_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"创建会话失败: {e}")
            raise
    
    def validate_session(self, session_id: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        验证会话有效性
        
        Args:
            session_id: 会话ID
            
        Returns:
            (是否有效, 会话信息)
        """
        try:
            if not session_id or session_id not in self.active_sessions:
                return False, None
            
            session_info = self.active_sessions[session_id]
            current_time = time.time()
            
            # 检查会话是否过期
            if current_time - session_info["created_time"] > self.session_lifetime:
                logger.debug(f"会话已过期: {session_id[:8]}...")
                self.destroy_session(session_id)
                return False, None
            
            # 更新最后活动时间
            session_info["last_activity"] = current_time
            
            logger.debug(f"会话验证成功: {session_id[:8]}...")
            return True, session_info
            
        except Exception as e:
            logger.error(f"会话验证失败: {e}")
            return False, None
    
    def destroy_session(self, session_id: str) -> bool:
        """
        销毁会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否成功销毁
        """
        try:
            if session_id in self.active_sessions:
                user_id = self.active_sessions[session_id].get("user_id", "unknown")
                del self.active_sessions[session_id]
                logger.info(f"销毁会话: {session_id[:8]}..., 用户: {user_id}")
                return True
            else:
                logger.warning(f"尝试销毁不存在的会话: {session_id}")
                return False
                
        except Exception as e:
            logger.error(f"销毁会话失败: {e}")
            return False
    
    def cleanup_expired_sessions(self) -> int:
        """
        清理过期的会话
        
        Returns:
            清理的会话数量
        """
        try:
            current_time = time.time()
            expired_sessions = []
            
            for session_id, session_info in self.active_sessions.items():
                if current_time - session_info["created_time"] > self.session_lifetime:
                    expired_sessions.append(session_id)
            
            # 删除过期会话
            for session_id in expired_sessions:
                del self.active_sessions[session_id]
            
            if expired_sessions:
                logger.info(f"清理了 {len(expired_sessions)} 个过期会话")
            
            return len(expired_sessions)
            
        except Exception as e:
            logger.error(f"清理过期会话失败: {e}")
            return 0
    
    def check_rate_limit(self, identifier: str, max_requests: int = 100, window_seconds: int = 3600) -> bool:
        """
        检查请求频率限制
        
        Args:
            identifier: 标识符（IP、用户ID等）
            max_requests: 最大请求数
            window_seconds: 时间窗口（秒）
            
        Returns:
            是否允许请求
        """
        try:
            current_time = time.time()
            window_start = current_time - window_seconds
            
            # 如果没有请求记录，初始化
            if not hasattr(self, 'rate_limits'):
                self.rate_limits = {}
            
            if identifier not in self.rate_limits:
                self.rate_limits[identifier] = []
            
            # 清理过期的请求记录
            self.rate_limits[identifier] = [
                timestamp for timestamp in self.rate_limits[identifier]
                if timestamp > window_start
            ]
            
            # 检查是否超出限制
            if len(self.rate_limits[identifier]) >= max_requests:
                logger.warning(f"请求频率超限: {identifier}, 当前请求数: {len(self.rate_limits[identifier])}")
                return False
            
            # 记录当前请求
            self.rate_limits[identifier].append(current_time)
            return True
            
        except Exception as e:
            logger.error(f"频率限制检查失败: {e}")
            return True  # 出错时允许请求
    
    def _generate_session_id(self, user_id: str) -> str:
        """
        生成会话ID
        
        Args:
            user_id: 用户ID
            
        Returns:
            会话ID
        """
        # 结合用户ID、时间戳和随机数生成会话ID
        timestamp = str(int(time.time() * 1000))
        random_bytes = secrets.token_bytes(16)
        
        # 创建哈希
        hasher = hashlib.sha256()
        hasher.update(user_id.encode('utf-8'))
        hasher.update(timestamp.encode('utf-8'))
        hasher.update(random_bytes)
        
        return hasher.hexdigest()
    
    def get_auth_status(self) -> Dict[str, Any]:
        """
        获取认证状态
        
        Returns:
            认证状态信息
        """
        return {
            "xianyu_authenticated": self.auth_status["xianyu_authenticated"],
            "openai_authenticated": self.auth_status["openai_authenticated"],
            "last_auth_check": self.auth_status["last_auth_check"],
            "active_sessions": len(self.active_sessions),
            "auth_errors": self.auth_status["auth_errors"][-5:],  # 只返回最近5个错误
            "time_since_last_check": time.time() - self.auth_status["last_auth_check"]
        }
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """
        获取会话统计信息
        
        Returns:
            会话统计数据
        """
        current_time = time.time()
        
        # 统计会话活跃度
        active_sessions = 0
        recent_activities = 0
        
        for session_info in self.active_sessions.values():
            active_sessions += 1
            if current_time - session_info["last_activity"] < 300:  # 5分钟内活跃
                recent_activities += 1
        
        return {
            "total_active_sessions": active_sessions,
            "recent_active_sessions": recent_activities,
            "session_lifetime_hours": self.session_lifetime / 3600,
            "rate_limit_records": len(getattr(self, 'rate_limits', {}))
        }
    
    def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            健康状态信息
        """
        health = {
            "status": "healthy",
            "checks": {
                "xianyu_auth": self.auth_status["xianyu_authenticated"],
                "openai_auth": self.auth_status["openai_authenticated"],
                "recent_auth_check": (time.time() - self.auth_status["last_auth_check"]) < 3600,
                "session_manager": True,
                "rate_limiter": True
            },
            "issues": []
        }
        
        # 检查认证状态
        if not health["checks"]["xianyu_auth"]:
            health["issues"].append("闲鱼认证失败")
        
        if not health["checks"]["openai_auth"]:
            health["issues"].append("OpenAI认证失败")
        
        if not health["checks"]["recent_auth_check"]:
            health["issues"].append("认证检查过期")
        
        # 检查是否有过多的认证错误
        if len(self.auth_status["auth_errors"]) > 10:
            health["issues"].append("认证错误过多")
        
        # 如果有问题，更新整体状态
        if health["issues"]:
            health["status"] = "degraded" if len(health["issues"]) <= 2 else "unhealthy"
        
        return health
    
    def reset_auth_errors(self):
        """重置认证错误记录"""
        self.auth_status["auth_errors"] = []
        logger.info("认证错误记录已重置") 