"""
AI代理基类模块
定义所有代理的通用接口和基础功能，确保代理间的一致性
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from openai import OpenAI
from config.logger_config import get_logger
from utils.constants import BLOCKED_PHRASES, SECURITY_WARNING_MESSAGE

# 获取专用日志记录器
logger = get_logger("agent", "base")


class BaseAgent(ABC):
    """
    AI代理基类
    定义所有专业代理的通用接口和基础功能
    """
    
    def __init__(self, client: OpenAI, system_prompt: str, agent_name: str):
        """
        初始化代理基类
        
        Args:
            client: OpenAI客户端实例
            system_prompt: 系统提示词
            agent_name: 代理名称
        """
        self.client = client
        self.system_prompt = system_prompt
        self.agent_name = agent_name
        
        # 代理特定配置
        self.max_tokens = 2000
        self.temperature = 0.7
        self.model_name = "qwen-plus"
        
        logger.info(f"{self.agent_name}代理初始化完成")
    
    def _build_messages(self, user_msg: str, item_desc: str, context: str, 
                       bargain_count: int = 0, **kwargs) -> list:
        """
        构建发送给LLM的消息列表
        
        Args:
            user_msg: 用户消息
            item_desc: 商品描述
            context: 对话上下文
            bargain_count: 议价次数
            **kwargs: 其他参数
            
        Returns:
            格式化的消息列表
        """
        # 构建系统消息
        system_content = self.system_prompt
        
        # 添加商品信息
        if item_desc:
            system_content += f"\n\n【商品信息】\n{item_desc}"
        
        # 添加议价次数信息（对价格代理特别重要）
        if bargain_count > 0:
            system_content += f"\n\n【议价信息】\n当前议价次数: {bargain_count}"
        
        # 添加额外的上下文信息
        for key, value in kwargs.items():
            if value:
                system_content += f"\n\n【{key}】\n{value}"
        
        messages = [
            {
                "role": "system",
                "content": system_content
            }
        ]
        
        # 添加历史对话上下文
        if context:
            messages.append({
                "role": "user", 
                "content": f"【对话历史】\n{context}\n\n【当前用户消息】\n{user_msg}"
            })
        else:
            messages.append({
                "role": "user",
                "content": user_msg
            })
        
        logger.debug(f"{self.agent_name}代理构建消息完成，系统提示词长度: {len(system_content)}")
        return messages
    
    def _call_llm(self, messages: list) -> str:
        """
        调用大语言模型生成回复
        
        Args:
            messages: 发送给LLM的消息列表
            
        Returns:
            LLM生成的回复文本
        """
        try:
            logger.debug(f"{self.agent_name}代理开始调用LLM，消息数量: {len(messages)}")
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                timeout=30
            )
            
            reply = response.choices[0].message.content.strip()
            
            logger.info(f"{self.agent_name}代理LLM调用成功，回复长度: {len(reply)} 字符")
            return reply
            
        except Exception as e:
            error_msg = f"{self.agent_name}代理LLM调用失败: {str(e)}"
            logger.error(error_msg)
            
            # 返回友好的错误提示
            return f"抱歉，{self.agent_name}暂时无法回复，请稍后再试。如需紧急帮助，请联系人工客服。"
    
    def _safety_filter(self, text: str) -> str:
        """
        安全过滤模块，检查和过滤潜在的敏感内容
        
        Args:
            text: 待过滤的文本
            
        Returns:
            过滤后的安全文本
        """
        if not text:
            return text
        
        # 检查是否包含敏感词汇
        for phrase in BLOCKED_PHRASES:
            if phrase in text:
                logger.warning(f"{self.agent_name}代理检测到敏感词汇: {phrase}")
                return SECURITY_WARNING_MESSAGE
        
        # 检查是否包含联系方式（简单正则检查）
        import re
        
        # 检查手机号码模式
        phone_patterns = [
            r'1[3-9]\d{9}',  # 中国手机号
            r'\d{3}-\d{4}-\d{4}',  # 格式化手机号
        ]
        
        for pattern in phone_patterns:
            if re.search(pattern, text):
                logger.warning(f"{self.agent_name}代理检测到疑似手机号码")
                return SECURITY_WARNING_MESSAGE
        
        # 检查QQ号码模式
        qq_pattern = r'\b[1-9]\d{4,11}\b'
        if re.search(qq_pattern, text):
            logger.warning(f"{self.agent_name}代理检测到疑似QQ号码")
            return SECURITY_WARNING_MESSAGE
        
        return text
    
    def _post_process(self, text: str) -> str:
        """
        后处理回复文本，进行格式化和优化
        
        Args:
            text: 原始回复文本
            
        Returns:
            处理后的文本
        """
        if not text:
            return "抱歉，我没有理解您的问题，能否重新描述一下？"
        
        # 移除多余的空白字符
        text = ' '.join(text.split())
        
        # 确保文本以合适的标点结尾
        if text and not text[-1] in '。！？.!?':
            text += '。'
        
        # 限制回复长度
        if len(text) > 500:
            text = text[:497] + "..."
            logger.debug(f"{self.agent_name}代理回复被截断，原长度超过500字符")
        
        return text
    
    def set_model_config(self, model_name: str = None, max_tokens: int = None, 
                        temperature: float = None):
        """
        设置模型配置参数
        
        Args:
            model_name: 模型名称
            max_tokens: 最大token数
            temperature: 温度参数
        """
        if model_name:
            self.model_name = model_name
        if max_tokens:
            self.max_tokens = max_tokens
        if temperature is not None:
            self.temperature = temperature
            
        logger.info(f"{self.agent_name}代理模型配置已更新")
    
    @abstractmethod
    def generate(self, user_msg: str, item_desc: str, context: str, 
                bargain_count: int = 0, **kwargs) -> str:
        """
        生成回复的抽象方法，由具体代理子类实现
        
        Args:
            user_msg: 用户消息
            item_desc: 商品描述
            context: 对话上下文
            bargain_count: 议价次数
            **kwargs: 其他参数
            
        Returns:
            生成的回复文本
        """
        pass
    
    def get_agent_info(self) -> Dict[str, Any]:
        """
        获取代理信息
        
        Returns:
            包含代理信息的字典
        """
        return {
            "name": self.agent_name,
            "model_name": self.model_name,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "prompt_length": len(self.system_prompt)
        }
    
    def __str__(self) -> str:
        """返回代理的字符串表示"""
        return f"{self.agent_name}Agent(model={self.model_name})"
    
    def __repr__(self) -> str:
        """返回代理的详细表示"""
        return f"{self.agent_name}Agent(model={self.model_name}, max_tokens={self.max_tokens}, temperature={self.temperature})" 