"""
分类代理模块
专门负责使用大语言模型进行复杂的用户意图识别和分类
"""

from typing import Dict, Any
from .base_agent import BaseAgent
from config.logger_config import get_logger
from utils.constants import AGENT_CLASSIFY, AGENT_TECH, AGENT_PRICE, AGENT_DEFAULT

# 获取专用日志记录器
logger = get_logger("agent", "classify")


class ClassifyAgent(BaseAgent):
    """
    分类代理
    使用大语言模型识别用户意图，为意图路由器提供兜底分类能力
    """
    
    def __init__(self, client, system_prompt):
        """
        初始化分类代理
        
        Args:
            client: OpenAI客户端实例
            system_prompt: 分类专用的系统提示词
        """
        super().__init__(client, system_prompt, AGENT_CLASSIFY)
        
        # 分类代理特定配置
        self.max_tokens = 500  # 分类结果通常较短
        self.temperature = 0.1  # 低温度确保分类结果的一致性
        
        # 分类标签映射
        self.classification_labels = {
            'tech': AGENT_TECH,
            'technical': AGENT_TECH,
            '技术': AGENT_TECH,
            '规格': AGENT_TECH,
            '参数': AGENT_TECH,
            
            'price': AGENT_PRICE,
            'pricing': AGENT_PRICE,
            '价格': AGENT_PRICE,
            '砍价': AGENT_PRICE,
            '议价': AGENT_PRICE,
            '便宜': AGENT_PRICE,
            
            'default': AGENT_DEFAULT,
            'general': AGENT_DEFAULT,
            '默认': AGENT_DEFAULT,
            '客服': AGENT_DEFAULT,
            '通用': AGENT_DEFAULT
        }
        
        logger.info("分类代理初始化完成")
    
    def generate(self, user_msg: str, item_desc: str, context: str, 
                bargain_count: int = 0, **kwargs) -> str:
        """
        执行意图分类任务
        
        Args:
            user_msg: 用户消息
            item_desc: 商品描述
            context: 对话上下文
            bargain_count: 议价次数（分类时可能有用）
            **kwargs: 其他参数
            
        Returns:
            分类结果（tech/price/default）
        """
        logger.debug(f"开始执行意图分类，用户消息: {user_msg[:100]}...")
        
        try:
            # 构建分类专用的消息
            messages = self._build_classification_messages(user_msg, item_desc, context, bargain_count)
            
            # 调用LLM进行分类
            classification_result = self._call_llm(messages)
            
            # 解析和标准化分类结果
            normalized_result = self._normalize_classification(classification_result)
            
            logger.info(f"意图分类完成: {user_msg[:30]}... -> {normalized_result}")
            return normalized_result
            
        except Exception as e:
            logger.error(f"意图分类过程出错: {e}")
            return AGENT_DEFAULT  # 出错时返回默认分类
    
    def _build_classification_messages(self, user_msg: str, item_desc: str, 
                                     context: str, bargain_count: int) -> list:
        """
        构建分类专用的消息格式
        
        Args:
            user_msg: 用户消息
            item_desc: 商品描述
            context: 对话上下文
            bargain_count: 议价次数
            
        Returns:
            格式化的消息列表
        """
        # 基础系统提示词
        system_content = self.system_prompt
        
        # 添加分类指导
        system_content += """

请根据用户消息的内容，准确判断用户的主要意图，并返回以下分类之一：

1. **tech** - 技术咨询类
   - 询问商品参数、规格、型号
   - 产品对比、兼容性问题
   - 技术细节、使用方法
   - 配置要求、性能指标

2. **price** - 价格议价类
   - 砍价、讨价还价
   - 询问优惠、打折
   - 希望降价、便宜点
   - 价格相关的任何讨论

3. **default** - 通用客服类
   - 一般性咨询、问候
   - 售后服务问题
   - 发货、物流相关
   - 其他非技术非价格的问题

**重要提示：**
- 只返回分类标签：tech、price 或 default
- 不要添加任何解释或其他内容
- 如果有多重意图，选择最主要的一个
- 技术问题优先级高于价格问题
"""
        
        # 添加商品信息
        if item_desc:
            system_content += f"\n\n【商品信息】\n{item_desc}"
        
        # 添加议价历史信息
        if bargain_count > 0:
            system_content += f"\n\n【议价信息】\n当前已议价次数: {bargain_count}"
        
        messages = [
            {
                "role": "system",
                "content": system_content
            }
        ]
        
        # 添加对话历史和当前消息
        if context:
            messages.append({
                "role": "user",
                "content": f"【对话历史】\n{context}\n\n【当前用户消息】\n{user_msg}\n\n请分类："
            })
        else:
            messages.append({
                "role": "user",
                "content": f"【用户消息】\n{user_msg}\n\n请分类："
            })
        
        return messages
    
    def _normalize_classification(self, raw_result: str) -> str:
        """
        标准化分类结果
        
        Args:
            raw_result: LLM返回的原始分类结果
            
        Returns:
            标准化的分类标签
        """
        if not raw_result:
            logger.warning("分类结果为空，返回默认分类")
            return AGENT_DEFAULT
        
        # 清理结果
        cleaned_result = raw_result.strip().lower()
        
        # 直接匹配标准标签
        if cleaned_result in [AGENT_TECH, AGENT_PRICE, AGENT_DEFAULT]:
            return cleaned_result
        
        # 通过分类标签映射查找
        for label, standard_label in self.classification_labels.items():
            if label in cleaned_result:
                logger.debug(f"通过标签映射找到分类: {label} -> {standard_label}")
                return standard_label
        
        # 模糊匹配
        if any(keyword in cleaned_result for keyword in ['技术', '参数', '规格', 'tech', 'spec']):
            logger.debug(f"模糊匹配为技术类: {cleaned_result}")
            return AGENT_TECH
        
        if any(keyword in cleaned_result for keyword in ['价格', '砍价', '便宜', 'price', 'cheap']):
            logger.debug(f"模糊匹配为价格类: {cleaned_result}")
            return AGENT_PRICE
        
        # 如果都不匹配，返回默认分类
        logger.warning(f"无法识别分类结果: {raw_result}，返回默认分类")
        return AGENT_DEFAULT
    
    def get_classification_confidence(self, user_msg: str, item_desc: str, 
                                    context: str) -> Dict[str, float]:
        """
        获取各个分类的置信度（可选功能，用于调试和优化）
        
        Args:
            user_msg: 用户消息
            item_desc: 商品描述
            context: 对话上下文
            
        Returns:
            包含各分类置信度的字典
        """
        # 这里可以实现更复杂的置信度计算
        # 目前返回简单的模拟数据
        return {
            AGENT_TECH: 0.33,
            AGENT_PRICE: 0.33,
            AGENT_DEFAULT: 0.34
        }
    
    def update_classification_rules(self, new_labels: Dict[str, str]):
        """
        更新分类标签映射规则
        
        Args:
            new_labels: 新的标签映射字典
        """
        self.classification_labels.update(new_labels)
        logger.info(f"分类标签映射已更新，新增 {len(new_labels)} 个映射")
    
    def get_classification_stats(self) -> Dict[str, Any]:
        """
        获取分类统计信息
        
        Returns:
            包含分类统计的字典
        """
        return {
            "total_labels": len(self.classification_labels),
            "supported_types": [AGENT_TECH, AGENT_PRICE, AGENT_DEFAULT],
            "model_config": self.get_agent_info()
        } 