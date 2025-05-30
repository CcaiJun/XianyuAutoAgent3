"""
OpenAI客户端管理器
负责OpenAI API的连接管理、配置和健康监控
"""

import time
from typing import Dict, Any, Optional, List
from openai import OpenAI
from openai.types.chat import ChatCompletion
from config.logger_config import get_logger
from config.settings import get_config
from utils.constants import DEFAULT_MODEL_NAME, MAX_TOKENS_DEFAULT, TEMPERATURE_DEFAULT

# 获取专用日志记录器
logger = get_logger("api", "openai")


class OpenAIClientManager:
    """
    OpenAI客户端管理器
    管理OpenAI API连接、配置和请求处理
    提供统一的AI模型调用接口
    """
    
    def __init__(self):
        """初始化OpenAI客户端管理器"""
        self.config = get_config()
        self.openai_config = self.config.get_openai_config()
        
        # 初始化客户端
        self.client = None
        self._initialize_client()
        
        # 统计信息
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_tokens_used": 0,
            "last_request_time": 0,
            "error_count_by_type": {}
        }
        
        logger.info(f"OpenAI客户端管理器初始化完成，模型: {self.openai_config['model_name']}")
    
    def _initialize_client(self):
        """初始化OpenAI客户端"""
        try:
            self.client = OpenAI(
                api_key=self.openai_config['api_key'],
                base_url=self.openai_config['base_url']
            )
            
            logger.info(f"OpenAI客户端初始化成功，base_url: {self.openai_config['base_url']}")
            
        except Exception as e:
            logger.error(f"OpenAI客户端初始化失败: {e}")
            raise
    
    def create_chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> Optional[ChatCompletion]:
        """
        创建聊天完成请求
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
            
        Returns:
            聊天完成响应，失败返回None
        """
        self.stats["total_requests"] += 1
        self.stats["last_request_time"] = time.time()
        
        try:
            # 准备请求参数
            request_params = {
                "model": kwargs.get("model", self.openai_config['model_name']),
                "messages": messages,
                "max_tokens": kwargs.get("max_tokens", self.openai_config.get('max_tokens', MAX_TOKENS_DEFAULT)),
                "temperature": kwargs.get("temperature", self.openai_config.get('temperature', TEMPERATURE_DEFAULT)),
                "stream": kwargs.get("stream", False)
            }
            
            # 添加其他可选参数
            if "top_p" in kwargs:
                request_params["top_p"] = kwargs["top_p"]
            if "frequency_penalty" in kwargs:
                request_params["frequency_penalty"] = kwargs["frequency_penalty"]
            if "presence_penalty" in kwargs:
                request_params["presence_penalty"] = kwargs["presence_penalty"]
            
            logger.debug(f"发起聊天完成请求，消息数量: {len(messages)}，模型: {request_params['model']}")
            
            # 发送请求
            response = self.client.chat.completions.create(**request_params)
            
            # 更新统计信息
            self.stats["successful_requests"] += 1
            if hasattr(response, 'usage') and response.usage:
                self.stats["total_tokens_used"] += response.usage.total_tokens
            
            logger.debug(f"聊天完成请求成功，使用token: {response.usage.total_tokens if response.usage else '未知'}")
            return response
            
        except Exception as e:
            self.stats["failed_requests"] += 1
            
            # 记录错误类型统计
            error_type = type(e).__name__
            self.stats["error_count_by_type"][error_type] = self.stats["error_count_by_type"].get(error_type, 0) + 1
            
            logger.error(f"聊天完成请求失败: {e}")
            return None
    
    def create_simple_completion(self, prompt: str, **kwargs) -> Optional[str]:
        """
        创建简单的文本完成请求
        
        Args:
            prompt: 提示词
            **kwargs: 其他参数
            
        Returns:
            生成的文本，失败返回None
        """
        messages = [{"role": "user", "content": prompt}]
        
        response = self.create_chat_completion(messages, **kwargs)
        
        if response and response.choices:
            return response.choices[0].message.content
        
        return None
    
    def validate_connection(self) -> bool:
        """
        验证与OpenAI API的连接
        
        Returns:
            连接是否有效
        """
        try:
            # 发送一个简单的测试请求
            test_messages = [{"role": "user", "content": "Hello"}]
            
            response = self.create_chat_completion(
                messages=test_messages,
                max_tokens=5,
                temperature=0.1
            )
            
            if response:
                logger.debug("OpenAI连接验证成功")
                return True
            else:
                logger.warning("OpenAI连接验证失败")
                return False
                
        except Exception as e:
            logger.error(f"OpenAI连接验证异常: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """
        获取可用的模型列表
        
        Returns:
            可用模型列表
        """
        try:
            models = self.client.models.list()
            model_names = [model.id for model in models.data]
            logger.debug(f"获取到 {len(model_names)} 个可用模型")
            return model_names
            
        except Exception as e:
            logger.error(f"获取模型列表失败: {e}")
            return []
    
    def update_config(self, new_config: Dict[str, Any]):
        """
        更新客户端配置
        
        Args:
            new_config: 新的配置参数
        """
        try:
            # 更新内部配置
            self.openai_config.update(new_config)
            
            # 如果API密钥或base_url发生变化，重新初始化客户端
            if "api_key" in new_config or "base_url" in new_config:
                self._initialize_client()
                logger.info("OpenAI客户端配置已更新并重新初始化")
            else:
                logger.info("OpenAI客户端配置已更新")
                
        except Exception as e:
            logger.error(f"更新OpenAI客户端配置失败: {e}")
    
    def estimate_tokens(self, text: str) -> int:
        """
        估算文本的token数量
        
        Args:
            text: 输入文本
            
        Returns:
            估算的token数量
        """
        # 简单的token估算，通常1个token约等于0.75个英文单词或0.5个中文字符
        chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
        english_words = len(text.replace(''.join([c for c in text if '\u4e00' <= c <= '\u9fff']), '').split())
        
        estimated_tokens = int(chinese_chars * 2 + english_words * 1.33)
        return estimated_tokens
    
    def get_client_info(self) -> Dict[str, Any]:
        """
        获取客户端信息
        
        Returns:
            客户端信息字典
        """
        return {
            "base_url": self.openai_config['base_url'],
            "model_name": self.openai_config['model_name'],
            "max_tokens": self.openai_config.get('max_tokens', MAX_TOKENS_DEFAULT),
            "temperature": self.openai_config.get('temperature', TEMPERATURE_DEFAULT),
            "client_initialized": bool(self.client),
            "last_request_time": self.stats["last_request_time"]
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取使用统计信息
        
        Returns:
            统计信息字典
        """
        success_rate = 0
        if self.stats["total_requests"] > 0:
            success_rate = self.stats["successful_requests"] / self.stats["total_requests"]
        
        return {
            "request_stats": {
                "total_requests": self.stats["total_requests"],
                "successful_requests": self.stats["successful_requests"],
                "failed_requests": self.stats["failed_requests"],
                "success_rate": f"{success_rate:.2%}"
            },
            "token_usage": {
                "total_tokens_used": self.stats["total_tokens_used"],
                "average_tokens_per_request": (
                    self.stats["total_tokens_used"] / self.stats["successful_requests"]
                    if self.stats["successful_requests"] > 0 else 0
                )
            },
            "error_analysis": {
                "total_errors": self.stats["failed_requests"],
                "error_count_by_type": self.stats["error_count_by_type"]
            },
            "timing": {
                "last_request_time": self.stats["last_request_time"],
                "time_since_last_request": time.time() - self.stats["last_request_time"] if self.stats["last_request_time"] > 0 else 0
            }
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
                "client_initialized": bool(self.client),
                "connection_valid": False,
                "config_loaded": bool(self.openai_config),
                "api_key_set": bool(self.openai_config.get('api_key')),
                "base_url_valid": bool(self.openai_config.get('base_url'))
            },
            "issues": []
        }
        
        # 检查连接
        try:
            health["checks"]["connection_valid"] = self.validate_connection()
        except Exception as e:
            health["issues"].append(f"连接验证失败: {e}")
        
        # 检查各项状态
        if not health["checks"]["client_initialized"]:
            health["issues"].append("OpenAI客户端未初始化")
        
        if not health["checks"]["api_key_set"]:
            health["issues"].append("API密钥未设置")
        
        if not health["checks"]["base_url_valid"]:
            health["issues"].append("Base URL未设置")
        
        if not health["checks"]["connection_valid"]:
            health["issues"].append("API连接无效")
        
        # 计算成功率
        if self.stats["total_requests"] > 0:
            success_rate = self.stats["successful_requests"] / self.stats["total_requests"]
            if success_rate < 0.8:
                health["issues"].append(f"请求成功率过低: {success_rate:.2%}")
        
        # 如果有问题，更新整体状态
        if health["issues"]:
            health["status"] = "degraded" if len(health["issues"]) <= 2 else "unhealthy"
        
        return health
    
    def reset_statistics(self):
        """重置统计信息"""
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_tokens_used": 0,
            "last_request_time": 0,
            "error_count_by_type": {}
        }
        logger.info("OpenAI客户端统计信息已重置")
    
    def get_current_client(self) -> Optional[OpenAI]:
        """
        获取当前的OpenAI客户端实例
        
        Returns:
            OpenAI客户端实例
        """
        return self.client 