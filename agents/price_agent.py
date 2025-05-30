"""
价格代理模块
专门负责处理议价、砍价、价格咨询等价格相关的对话
实现智能的阶梯式议价策略
"""

import re
from typing import Dict, Any, Optional
from .base_agent import BaseAgent
from config.logger_config import get_logger
from utils.constants import AGENT_PRICE

# 获取专用日志记录器
logger = get_logger("agent", "price")


class PriceAgent(BaseAgent):
    """
    价格代理 - 议价专家
    专门处理价格协商、砍价、优惠咨询等场景
    使用智能的阶梯式议价策略
    """
    
    def __init__(self, client, system_prompt):
        """
        初始化价格代理
        
        Args:
            client: OpenAI客户端实例
            system_prompt: 价格专用的系统提示词
        """
        super().__init__(client, system_prompt, AGENT_PRICE)
        
        # 价格代理特定配置
        self.max_tokens = 1500  # 议价对话可能需要更多解释
        self.temperature = 0.6  # 中等温度，保持友好但有策略性
        
        # 议价策略配置
        self.bargain_strategies = {
            1: {  # 第一次议价
                "discount_range": (0.05, 0.10),  # 5%-10%折扣
                "tone": "friendly_firm",
                "tactics": ["强调品质", "适度让步", "建立信任"]
            },
            2: {  # 第二次议价
                "discount_range": (0.10, 0.15),  # 10%-15%折扣
                "tone": "understanding",
                "tactics": ["展示灵活性", "强调诚意", "有限让步"]
            },
            3: {  # 第三次议价
                "discount_range": (0.15, 0.20),  # 15%-20%折扣
                "tone": "final_offer",
                "tactics": ["最终价格", "突出价值", "促成交易"]
            }
        }
        
        # 价格相关的正则模式
        self.price_patterns = {
            "specific_price": r'(\d+)元',           # 具体价格
            "discount_request": r'便宜(\d+)',       # 要求便宜多少
            "percentage_off": r'打(\d+)折',         # 打折要求
            "lowest_price": r'最低(\d+)',           # 最低价格
            "bulk_discount": r'多买.*便宜',         # 批量优惠
        }
        
        logger.info("价格代理初始化完成")
    
    def generate(self, user_msg: str, item_desc: str, context: str, 
                bargain_count: int = 0, **kwargs) -> str:
        """
        生成价格相关的回复
        
        Args:
            user_msg: 用户消息
            item_desc: 商品描述
            context: 对话上下文
            bargain_count: 议价次数
            **kwargs: 其他参数
            
        Returns:
            价格代理的回复
        """
        logger.debug(f"价格代理开始处理消息: {user_msg[:50]}..., 议价次数: {bargain_count}")
        
        try:
            # 分析价格意图
            price_intent = self._analyze_price_intent(user_msg)
            
            # 提取价格信息
            price_info = self._extract_price_info(user_msg, item_desc)
            
            # 确定议价策略
            strategy = self._get_bargain_strategy(bargain_count, price_intent)
            
            # 构建消息
            messages = self._build_price_messages(
                user_msg, item_desc, context, bargain_count, 
                price_intent=price_intent,
                price_info=price_info,
                strategy=strategy
            )
            
            # 调用LLM生成回复
            raw_reply = self._call_llm(messages)
            
            # 后处理回复
            processed_reply = self._post_process_price_reply(raw_reply, strategy)
            
            # 安全过滤
            safe_reply = self._safety_filter(processed_reply)
            
            logger.info(f"价格代理回复生成完成，策略: {strategy.get('tone', 'default')}")
            return safe_reply
            
        except Exception as e:
            logger.error(f"价格代理处理失败: {e}")
            return self._get_fallback_price_reply(bargain_count)
    
    def _analyze_price_intent(self, user_msg: str) -> Dict[str, Any]:
        """
        分析用户的价格意图
        
        Args:
            user_msg: 用户消息
            
        Returns:
            价格意图分析结果
        """
        intent = {
            "type": "general_inquiry",
            "urgency": "normal",
            "specific_request": None,
            "emotional_tone": "neutral"
        }
        
        # 分析意图类型
        if any(word in user_msg for word in ['砍价', '便宜', '降价', '打折']):
            intent["type"] = "bargain_request"
        elif any(word in user_msg for word in ['最低', '底价', '最便宜']):
            intent["type"] = "lowest_price_inquiry"
        elif any(word in user_msg for word in ['多买', '批量', '数量']):
            intent["type"] = "bulk_discount_inquiry"
        elif any(word in user_msg for word in ['优惠', '活动', '促销']):
            intent["type"] = "promotion_inquiry"
        
        # 分析紧急程度
        if any(word in user_msg for word in ['急', '马上', '立即', '赶紧']):
            intent["urgency"] = "high"
        elif any(word in user_msg for word in ['考虑', '看看', '比较']):
            intent["urgency"] = "low"
        
        # 分析情感倾向
        if any(word in user_msg for word in ['喜欢', '很想要', '非常需要']):
            intent["emotional_tone"] = "positive"
        elif any(word in user_msg for word in ['太贵', '贵了', '买不起']):
            intent["emotional_tone"] = "price_sensitive"
        
        logger.debug(f"价格意图分析: {intent}")
        return intent
    
    def _extract_price_info(self, user_msg: str, item_desc: str) -> Dict[str, Any]:
        """
        从消息中提取价格相关信息
        
        Args:
            user_msg: 用户消息
            item_desc: 商品描述
            
        Returns:
            提取的价格信息
        """
        price_info = {
            "mentioned_prices": [],
            "discount_requests": [],
            "original_price": None,
            "target_price": None
        }
        
        # 提取具体价格
        for pattern_name, pattern in self.price_patterns.items():
            matches = re.findall(pattern, user_msg)
            if matches:
                if pattern_name == "specific_price":
                    price_info["mentioned_prices"].extend([int(m) for m in matches])
                elif pattern_name == "discount_request":
                    price_info["discount_requests"].extend([int(m) for m in matches])
                elif pattern_name == "lowest_price":
                    price_info["target_price"] = int(matches[0])
        
        # 从商品描述中提取原价信息
        if item_desc:
            price_matches = re.findall(r'(\d+)元', item_desc)
            if price_matches:
                price_info["original_price"] = int(price_matches[0])
        
        logger.debug(f"提取的价格信息: {price_info}")
        return price_info
    
    def _get_bargain_strategy(self, bargain_count: int, price_intent: Dict) -> Dict[str, Any]:
        """
        根据议价次数和意图确定策略
        
        Args:
            bargain_count: 议价次数
            price_intent: 价格意图分析结果
            
        Returns:
            议价策略配置
        """
        # 获取基础策略
        base_strategy = self.bargain_strategies.get(min(bargain_count + 1, 3), self.bargain_strategies[3])
        
        # 根据意图调整策略
        strategy = base_strategy.copy()
        
        if price_intent.get("urgency") == "high":
            # 高紧急度，可以更积极让步
            strategy["tone"] = "accommodating"
            strategy["tactics"].append("紧急处理")
        elif price_intent.get("emotional_tone") == "price_sensitive":
            # 价格敏感，强调性价比
            strategy["tactics"].append("强调性价比")
        elif price_intent.get("type") == "bulk_discount_inquiry":
            # 批量询价，提供批量优惠
            strategy["tactics"].append("批量优惠")
        
        logger.debug(f"确定议价策略: {strategy}")
        return strategy
    
    def _build_price_messages(self, user_msg: str, item_desc: str, context: str,
                             bargain_count: int, **kwargs) -> list:
        """
        构建价格专用的消息格式
        
        Args:
            user_msg: 用户消息
            item_desc: 商品描述
            context: 对话上下文
            bargain_count: 议价次数
            **kwargs: 额外信息
            
        Returns:
            格式化的消息列表
        """
        # 基础系统提示词
        system_content = self.system_prompt
        
        # 添加议价策略指导
        strategy = kwargs.get('strategy', {})
        if strategy:
            system_content += f"""

【当前议价策略】
议价轮次: 第{bargain_count + 1}次
策略基调: {strategy.get('tone', '友好坚定')}
策略要点: {', '.join(strategy.get('tactics', []))}
建议折扣范围: {strategy.get('discount_range', (0.05, 0.10))}

请根据以上策略进行回复，保持专业友好的态度。
"""
        
        # 添加价格分析信息
        price_intent = kwargs.get('price_intent', {})
        price_info = kwargs.get('price_info', {})
        
        if price_intent or price_info:
            system_content += f"""

【价格分析信息】
用户意图类型: {price_intent.get('type', '一般咨询')}
情感倾向: {price_intent.get('emotional_tone', '中性')}
紧急程度: {price_intent.get('urgency', '正常')}
提及价格: {price_info.get('mentioned_prices', [])}
原始价格: {price_info.get('original_price', '未知')}
目标价格: {price_info.get('target_price', '未指定')}
"""
        
        # 使用基类的消息构建方法
        return self._build_messages(user_msg, item_desc, context, bargain_count, **kwargs)
    
    def _post_process_price_reply(self, reply: str, strategy: Dict) -> str:
        """
        对价格回复进行后处理
        
        Args:
            reply: 原始回复
            strategy: 议价策略
            
        Returns:
            处理后的回复
        """
        if not reply:
            return reply
        
        # 确保回复符合策略基调
        tone = strategy.get('tone', 'friendly_firm')
        
        if tone == "final_offer" and "最终" not in reply and "最后" not in reply:
            # 最终报价要明确表达
            reply = reply.rstrip('。！') + "，这是我们的最终价格。"
        elif tone == "accommodating" and "理解" not in reply:
            # 包容性回复要体现理解
            reply = "我理解您的需求，" + reply
        
        # 价格相关的格式化
        reply = self._format_price_in_reply(reply)
        
        return self._post_process(reply)
    
    def _format_price_in_reply(self, reply: str) -> str:
        """
        格式化回复中的价格显示
        
        Args:
            reply: 原始回复
            
        Returns:
            格式化后的回复
        """
        # 确保价格格式统一
        reply = re.sub(r'(\d+)块', r'\1元', reply)
        reply = re.sub(r'(\d+)钱', r'\1元', reply)
        
        # 添加价格符号
        reply = re.sub(r'(\d+)元', r'¥\1', reply)
        
        return reply
    
    def _get_fallback_price_reply(self, bargain_count: int) -> str:
        """
        获取价格代理的兜底回复
        
        Args:
            bargain_count: 议价次数
            
        Returns:
            兜底回复
        """
        fallback_replies = {
            0: "感谢您对我们商品的关注！关于价格，我们的定价都是经过市场调研的合理价格。如果您有特殊需求，我们可以详细沟通。",
            1: "我理解您希望获得更优惠价格的想法。让我看看能为您提供什么样的优惠方案。",
            2: "非常感谢您的耐心沟通。基于我们之前的讨论，我会尽力为您争取一个满意的价格。",
        }
        
        if bargain_count >= 3:
            return "经过我们多轮的沟通，我已经为您提供了最大的优惠。希望您能理解我们的诚意。"
        
        return fallback_replies.get(bargain_count, fallback_replies[0])
    
    def get_bargain_statistics(self) -> Dict[str, Any]:
        """
        获取议价统计信息
        
        Returns:
            议价统计数据
        """
        return {
            "total_strategies": len(self.bargain_strategies),
            "max_bargain_rounds": 3,
            "supported_intents": ["bargain_request", "lowest_price_inquiry", "bulk_discount_inquiry", "promotion_inquiry"],
            "price_patterns": list(self.price_patterns.keys())
        }
    
    def update_bargain_strategy(self, round_num: int, strategy_config: Dict):
        """
        更新议价策略配置
        
        Args:
            round_num: 议价轮次
            strategy_config: 新的策略配置
        """
        if round_num in self.bargain_strategies:
            self.bargain_strategies[round_num].update(strategy_config)
            logger.info(f"更新第{round_num}轮议价策略: {strategy_config}")
        else:
            logger.warning(f"无效的议价轮次: {round_num}") 