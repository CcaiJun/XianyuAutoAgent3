"""
代理工厂模块
负责创建、管理和协调所有AI代理实例
实现代理的统一管理和路由分发
"""

from typing import Dict, Any, Optional
from openai import OpenAI

from .base_agent import BaseAgent
from .classify_agent import ClassifyAgent
from .intent_router import IntentRouter
from .price_agent import PriceAgent
from .tech_agent import TechAgent
from .default_agent import DefaultAgent

from config.settings import get_config
from config.logger_config import get_logger
from utils.constants import AGENT_CLASSIFY, AGENT_PRICE, AGENT_TECH, AGENT_DEFAULT

# 获取专用日志记录器
logger = get_logger("agent", "factory")


class AgentFactory:
    """
    代理工厂
    统一管理所有AI代理的创建、配置和生命周期
    提供代理路由和消息分发功能
    """
    
    def __init__(self):
        """初始化代理工厂"""
        self.config = get_config()
        self.openai_client = None
        self.agents = {}
        self.intent_router = None
        
        # 统计信息
        self.stats = {
            "total_requests": 0,
            "agent_usage": {
                AGENT_CLASSIFY: 0,
                AGENT_PRICE: 0,
                AGENT_TECH: 0,
                AGENT_DEFAULT: 0
            },
            "error_count": 0
        }
        
        logger.info("代理工厂初始化完成")
    
    def initialize(self) -> bool:
        """
        初始化所有代理和相关组件
        
        Returns:
            初始化是否成功
        """
        try:
            logger.info("开始初始化代理工厂...")
            
            # 1. 初始化OpenAI客户端
            self._initialize_openai_client()
            
            # 2. 创建所有代理实例
            self._create_agents()
            
            # 3. 初始化意图路由器
            self._initialize_intent_router()
            
            logger.info("代理工厂初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"代理工厂初始化失败: {e}")
            return False
    
    def _initialize_openai_client(self):
        """初始化OpenAI客户端"""
        openai_config = self.config.get_openai_config()
        
        self.openai_client = OpenAI(
            api_key=openai_config['api_key'],
            base_url=openai_config['base_url']
        )
        
        logger.info(f"OpenAI客户端初始化完成，base_url: {openai_config['base_url']}")
    
    def _create_agents(self):
        """创建所有代理实例"""
        logger.info("开始创建代理实例...")
        
        # 创建分类代理
        classify_prompt = self.config.get_prompt(AGENT_CLASSIFY)
        self.agents[AGENT_CLASSIFY] = ClassifyAgent(
            client=self.openai_client,
            system_prompt=classify_prompt
        )
        
        # 创建价格代理
        price_prompt = self.config.get_prompt(AGENT_PRICE)
        self.agents[AGENT_PRICE] = PriceAgent(
            client=self.openai_client,
            system_prompt=price_prompt
        )
        
        # 创建技术代理
        tech_prompt = self.config.get_prompt(AGENT_TECH)
        self.agents[AGENT_TECH] = TechAgent(
            client=self.openai_client,
            system_prompt=tech_prompt
        )
        
        # 创建默认代理
        default_prompt = self.config.get_prompt(AGENT_DEFAULT)
        self.agents[AGENT_DEFAULT] = DefaultAgent(
            client=self.openai_client,
            system_prompt=default_prompt
        )
        
        logger.info(f"成功创建 {len(self.agents)} 个代理实例")
    
    def _initialize_intent_router(self):
        """初始化意图路由器"""
        classify_agent = self.agents.get(AGENT_CLASSIFY)
        if classify_agent:
            self.intent_router = IntentRouter(classify_agent)
            logger.info("意图路由器初始化完成")
        else:
            raise ValueError("分类代理未初始化，无法创建意图路由器")
    
    def process_message(self, user_msg: str, item_desc: str = "", context: str = "", 
                       bargain_count: int = 0, **kwargs) -> Dict[str, Any]:
        """
        处理用户消息的主入口
        
        Args:
            user_msg: 用户消息
            item_desc: 商品描述
            context: 对话上下文
            bargain_count: 议价次数
            **kwargs: 其他参数
            
        Returns:
            包含处理结果的字典
        """
        self.stats["total_requests"] += 1
        
        try:
            logger.info(f"开始处理消息: {user_msg[:50]}...")
            
            # 1. 意图识别和路由
            target_agent_type = self._route_message(user_msg, item_desc, context)
            
            # 2. 获取目标代理
            target_agent = self._get_agent(target_agent_type)
            
            # 3. 生成回复
            reply = self._generate_reply(target_agent, user_msg, item_desc, context, bargain_count, **kwargs)
            
            # 4. 更新统计信息
            self.stats["agent_usage"][target_agent_type] += 1
            
            result = {
                "success": True,
                "reply": reply,
                "agent_type": target_agent_type,
                "message_id": kwargs.get("message_id", ""),
                "processing_time": 0  # 可以添加计时功能
            }
            
            logger.info(f"消息处理完成，使用代理: {target_agent_type}")
            return result
            
        except Exception as e:
            self.stats["error_count"] += 1
            logger.error(f"消息处理失败: {e}")
            
            # 返回错误处理结果
            return {
                "success": False,
                "reply": "抱歉，我遇到了一些技术问题，请稍后再试或联系人工客服。",
                "agent_type": AGENT_DEFAULT,
                "error": str(e),
                "message_id": kwargs.get("message_id", "")
            }
    
    def _route_message(self, user_msg: str, item_desc: str, context: str) -> str:
        """
        路由消息到合适的代理
        
        Args:
            user_msg: 用户消息
            item_desc: 商品描述
            context: 对话上下文
            
        Returns:
            目标代理类型
        """
        if not self.intent_router:
            logger.warning("意图路由器未初始化，使用默认代理")
            return AGENT_DEFAULT
        
        try:
            agent_type = self.intent_router.detect(user_msg, item_desc, context)
            logger.debug(f"消息路由结果: {user_msg[:30]}... -> {agent_type}")
            return agent_type
        except Exception as e:
            logger.error(f"消息路由失败: {e}，使用默认代理")
            return AGENT_DEFAULT
    
    def _get_agent(self, agent_type: str) -> BaseAgent:
        """
        获取指定类型的代理实例
        
        Args:
            agent_type: 代理类型
            
        Returns:
            代理实例
        """
        agent = self.agents.get(agent_type)
        if not agent:
            logger.warning(f"未找到代理类型 {agent_type}，使用默认代理")
            agent = self.agents.get(AGENT_DEFAULT)
        
        return agent
    
    def _generate_reply(self, agent: BaseAgent, user_msg: str, item_desc: str, 
                       context: str, bargain_count: int, **kwargs) -> str:
        """
        使用指定代理生成回复
        
        Args:
            agent: 代理实例
            user_msg: 用户消息
            item_desc: 商品描述
            context: 对话上下文
            bargain_count: 议价次数
            **kwargs: 其他参数
            
        Returns:
            生成的回复
        """
        if not agent:
            return "抱歉，系统暂时无法处理您的请求，请稍后再试。"
        
        try:
            reply = agent.generate(
                user_msg=user_msg,
                item_desc=item_desc,
                context=context,
                bargain_count=bargain_count,
                **kwargs
            )
            return reply
        except Exception as e:
            logger.error(f"代理 {agent.agent_name} 生成回复失败: {e}")
            # 如果当前代理失败，尝试使用默认代理
            if agent.agent_name != AGENT_DEFAULT:
                default_agent = self.agents.get(AGENT_DEFAULT)
                if default_agent:
                    return default_agent.generate(user_msg, item_desc, context, bargain_count)
            
            return "抱歉，我暂时无法理解您的问题，请重新描述或联系人工客服。"
    
    def get_agent_info(self, agent_type: str = None) -> Dict[str, Any]:
        """
        获取代理信息
        
        Args:
            agent_type: 代理类型，None表示获取所有代理信息
            
        Returns:
            代理信息字典
        """
        if agent_type:
            agent = self.agents.get(agent_type)
            return agent.get_agent_info() if agent else {}
        else:
            return {
                agent_type: agent.get_agent_info() 
                for agent_type, agent in self.agents.items()
            }
    
    def get_factory_statistics(self) -> Dict[str, Any]:
        """
        获取工厂统计信息
        
        Returns:
            统计信息字典
        """
        return {
            "stats": self.stats.copy(),
            "agents_count": len(self.agents),
            "available_agents": list(self.agents.keys()),
            "router_initialized": self.intent_router is not None,
            "client_initialized": self.openai_client is not None
        }
    
    def reload_prompts(self):
        """重新加载所有代理的提示词"""
        try:
            logger.info("开始重新加载提示词...")
            
            # 重新加载配置
            self.config.reload_prompts()
            
            # 更新各个代理的提示词
            for agent_type, agent in self.agents.items():
                new_prompt = self.config.get_prompt(agent_type)
                agent.system_prompt = new_prompt
                logger.debug(f"已更新 {agent_type} 代理的提示词")
            
            logger.info("提示词重新加载完成")
            return True
            
        except Exception as e:
            logger.error(f"重新加载提示词失败: {e}")
            return False
    
    def update_agent_config(self, agent_type: str, config: Dict[str, Any]):
        """
        更新代理配置
        
        Args:
            agent_type: 代理类型
            config: 新的配置参数
        """
        agent = self.agents.get(agent_type)
        if agent:
            agent.set_model_config(
                model_name=config.get('model_name'),
                max_tokens=config.get('max_tokens'),
                temperature=config.get('temperature')
            )
            logger.info(f"已更新 {agent_type} 代理配置")
        else:
            logger.warning(f"未找到代理类型: {agent_type}")
    
    def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            健康状态信息
        """
        health = {
            "factory_status": "healthy",
            "openai_client": self.openai_client is not None,
            "intent_router": self.intent_router is not None,
            "agents": {},
            "issues": []
        }
        
        # 检查各个代理状态
        for agent_type, agent in self.agents.items():
            try:
                agent_info = agent.get_agent_info()
                health["agents"][agent_type] = {
                    "status": "healthy",
                    "name": agent_info.get("name", "unknown"),
                    "model": agent_info.get("model_name", "unknown")
                }
            except Exception as e:
                health["agents"][agent_type] = {
                    "status": "error",
                    "error": str(e)
                }
                health["issues"].append(f"代理 {agent_type} 存在问题: {e}")
        
        # 如果有问题，更新整体状态
        if health["issues"]:
            health["factory_status"] = "degraded"
        
        return health
    
    def shutdown(self):
        """关闭工厂，清理资源"""
        logger.info("开始关闭代理工厂...")
        
        # 清理代理实例
        self.agents.clear()
        
        # 清理路由器
        self.intent_router = None
        
        # 清理OpenAI客户端
        self.openai_client = None
        
        logger.info("代理工厂已关闭")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.shutdown()


# 全局代理工厂实例
_agent_factory = None


def get_agent_factory() -> AgentFactory:
    """
    获取全局代理工厂实例（单例模式）
    
    Returns:
        代理工厂实例
    """
    global _agent_factory
    
    if _agent_factory is None:
        _agent_factory = AgentFactory()
        if not _agent_factory.initialize():
            logger.error("代理工厂初始化失败")
            raise RuntimeError("代理工厂初始化失败")
    
    return _agent_factory


def process_user_message(user_msg: str, **kwargs) -> Dict[str, Any]:
    """
    处理用户消息的便捷函数
    
    Args:
        user_msg: 用户消息
        **kwargs: 其他参数
        
    Returns:
        处理结果
    """
    factory = get_agent_factory()
    return factory.process_message(user_msg, **kwargs) 