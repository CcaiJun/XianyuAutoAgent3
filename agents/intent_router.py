"""
意图路由器模块
负责分析用户消息，识别用户意图，并将请求路由到合适的专家代理
"""

import re
from typing import Dict, List, Optional
from config.logger_config import get_logger
from utils.constants import TECH_PATTERNS, PRICE_PATTERNS, AGENT_CLASSIFY, AGENT_PRICE, AGENT_TECH, AGENT_DEFAULT

# 获取专用日志记录器
logger = get_logger("agent", "router")


class IntentRouter:
    """
    意图路由决策器
    使用规则优先 + 大模型兜底的三级路由策略
    """
    
    def __init__(self, classify_agent):
        """
        初始化意图路由器
        
        Args:
            classify_agent: 分类代理，用于复杂意图的LLM识别
        """
        self.classify_agent = classify_agent
        
        # 定义路由规则 - 技术类优先
        self.rules = {
            AGENT_TECH: {
                'keywords': ['参数', '规格', '型号', '连接', '对比', '配置', '尺寸', '重量', '材质', '兼容'],
                'patterns': TECH_PATTERNS
            },
            AGENT_PRICE: {
                'keywords': ['便宜', '价', '砍价', '少点', '打折', '优惠', '降价', '最低', '能便宜'],
                'patterns': PRICE_PATTERNS
            }
        }
        
        # 意图识别的优先级（数字越小优先级越高）
        self.intent_priority = {
            AGENT_TECH: 1,     # 技术问题优先级最高
            AGENT_PRICE: 2,    # 价格问题次之
            AGENT_DEFAULT: 3   # 默认客服最低
        }
        
        logger.info("意图路由器初始化完成")
    
    def detect(self, user_msg: str, item_desc: str, context: str) -> str:
        """
        检测用户意图并返回目标代理类型
        使用三级路由策略：规则优先 -> 关键词匹配 -> LLM兜底
        
        Args:
            user_msg: 用户消息
            item_desc: 商品描述
            context: 对话上下文
            
        Returns:
            目标代理类型 (tech/price/default)
        """
        logger.debug(f"开始意图识别，用户消息: {user_msg[:50]}...")
        
        # 预处理：清理消息文本
        clean_msg = self._preprocess_message(user_msg)
        
        # 第一级：技术类专用正则模式优先检查
        tech_intent = self._check_tech_patterns(clean_msg, context)
        if tech_intent:
            logger.info(f"规则匹配识别为技术意图: {tech_intent}")
            return AGENT_TECH
        
        # 第二级：关键词匹配检查
        keyword_intent = self._check_keywords(clean_msg, context)
        if keyword_intent:
            logger.info(f"关键词匹配识别为: {keyword_intent}")
            return keyword_intent
        
        # 第三级：价格类正则模式检查
        price_intent = self._check_price_patterns(clean_msg, context)
        if price_intent:
            logger.info(f"价格规则匹配识别为: {price_intent}")
            return AGENT_PRICE
        
        # 第四级：大模型兜底分类
        llm_intent = self._llm_classify(user_msg, item_desc, context)
        logger.info(f"大模型分类识别为: {llm_intent}")
        return llm_intent
    
    def _preprocess_message(self, message: str) -> str:
        """
        预处理用户消息，清理和标准化文本
        
        Args:
            message: 原始用户消息
            
        Returns:
            清理后的消息文本
        """
        if not message:
            return ""
        
        # 移除特殊字符，保留中文、英文、数字和常用标点
        clean_text = re.sub(r'[^\w\u4e00-\u9fa5\s。，？！.?!,]', '', message)
        
        # 标准化空白字符
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        logger.debug(f"消息预处理: {message} -> {clean_text}")
        return clean_text
    
    def _check_tech_patterns(self, message: str, context: str) -> Optional[str]:
        """
        检查技术类专用模式（最高优先级）
        
        Args:
            message: 清理后的用户消息
            context: 对话上下文
            
        Returns:
            如果匹配技术模式则返回匹配信息，否则返回None
        """
        # 检查技术类关键词
        tech_keywords = self.rules[AGENT_TECH]['keywords']
        for keyword in tech_keywords:
            if keyword in message:
                logger.debug(f"技术类关键词匹配: {keyword}")
                return f"关键词_{keyword}"
        
        # 检查技术类正则模式
        for pattern in self.rules[AGENT_TECH]['patterns']:
            if re.search(pattern, message):
                logger.debug(f"技术类正则匹配: {pattern}")
                return f"模式_{pattern}"
        
        # 检查上下文中的技术倾向
        if self._has_tech_context(context):
            logger.debug("上下文显示技术讨论倾向")
            return "上下文_技术"
        
        return None
    
    def _check_keywords(self, message: str, context: str) -> Optional[str]:
        """
        检查关键词匹配
        
        Args:
            message: 清理后的用户消息
            context: 对话上下文
            
        Returns:
            匹配的意图类型或None
        """
        intent_scores = {}
        
        # 为每个意图类型计算关键词匹配分数
        for intent_type, rules in self.rules.items():
            score = 0
            matched_keywords = []
            
            for keyword in rules['keywords']:
                if keyword in message:
                    score += 1
                    matched_keywords.append(keyword)
            
            if score > 0:
                intent_scores[intent_type] = {
                    'score': score,
                    'keywords': matched_keywords
                }
                logger.debug(f"{intent_type}意图关键词匹配分数: {score}, 匹配词: {matched_keywords}")
        
        # 如果有匹配的关键词，返回分数最高且优先级最高的意图
        if intent_scores:
            # 按分数降序，优先级升序排序
            sorted_intents = sorted(
                intent_scores.items(),
                key=lambda x: (-x[1]['score'], self.intent_priority.get(x[0], 999))
            )
            best_intent = sorted_intents[0][0]
            logger.debug(f"关键词匹配最佳意图: {best_intent}")
            return best_intent
        
        return None
    
    def _check_price_patterns(self, message: str, context: str) -> Optional[str]:
        """
        检查价格类正则模式
        
        Args:
            message: 清理后的用户消息
            context: 对话上下文
            
        Returns:
            如果匹配价格模式则返回匹配信息，否则返回None
        """
        for pattern in self.rules[AGENT_PRICE]['patterns']:
            if re.search(pattern, message):
                logger.debug(f"价格类正则匹配: {pattern}")
                return f"模式_{pattern}"
        
        return None
    
    def _has_tech_context(self, context: str) -> bool:
        """
        检查上下文是否显示技术讨论倾向
        
        Args:
            context: 对话上下文
            
        Returns:
            是否有技术讨论倾向
        """
        if not context:
            return False
        
        tech_indicators = ['参数', '规格', '型号', '配置', '性能', '兼容', '接口', '尺寸']
        tech_count = sum(1 for indicator in tech_indicators if indicator in context)
        
        return tech_count >= 2  # 至少出现2个技术相关词汇
    
    def _llm_classify(self, user_msg: str, item_desc: str, context: str) -> str:
        """
        使用大模型进行意图分类（兜底策略）
        
        Args:
            user_msg: 用户消息
            item_desc: 商品描述
            context: 对话上下文
            
        Returns:
            LLM分类的意图类型
        """
        try:
            # 调用分类代理进行意图识别
            if self.classify_agent:
                result = self.classify_agent.generate(
                    user_msg=user_msg,
                    item_desc=item_desc,
                    context=context
                )
                
                # 解析LLM返回的意图类型
                intent = self._parse_llm_result(result)
                logger.debug(f"LLM分类结果: {result} -> {intent}")
                return intent
            else:
                logger.warning("分类代理未初始化，返回默认意图")
                return AGENT_DEFAULT
                
        except Exception as e:
            logger.error(f"LLM意图分类失败: {e}")
            return AGENT_DEFAULT
    
    def _parse_llm_result(self, llm_result: str) -> str:
        """
        解析LLM返回的分类结果
        
        Args:
            llm_result: LLM返回的原始结果
            
        Returns:
            标准化的意图类型
        """
        if not llm_result:
            return AGENT_DEFAULT
        
        result_lower = llm_result.lower().strip()
        
        # 技术类关键词
        if any(word in result_lower for word in ['tech', '技术', 'technical', 'spec', '规格', '参数']):
            return AGENT_TECH
        
        # 价格类关键词
        if any(word in result_lower for word in ['price', '价格', 'pricing', '砍价', '议价', '便宜']):
            return AGENT_PRICE
        
        # 默认类关键词
        if any(word in result_lower for word in ['default', '默认', 'general', '客服', '通用']):
            return AGENT_DEFAULT
        
        # 如果无法识别，返回默认意图
        logger.warning(f"无法解析LLM分类结果: {llm_result}")
        return AGENT_DEFAULT
    
    def get_routing_stats(self) -> Dict[str, int]:
        """
        获取路由统计信息（用于监控和优化）
        
        Returns:
            包含路由统计的字典
        """
        # 这里可以添加统计逻辑，跟踪各种路由方式的使用频率
        return {
            "tech_routes": 0,
            "price_routes": 0, 
            "default_routes": 0,
            "llm_fallback_routes": 0
        }
    
    def update_rules(self, intent_type: str, keywords: List[str] = None, 
                    patterns: List[str] = None):
        """
        动态更新路由规则
        
        Args:
            intent_type: 意图类型
            keywords: 新的关键词列表
            patterns: 新的正则模式列表
        """
        if intent_type in self.rules:
            if keywords:
                self.rules[intent_type]['keywords'].extend(keywords)
                logger.info(f"为{intent_type}意图添加关键词: {keywords}")
            
            if patterns:
                self.rules[intent_type]['patterns'].extend(patterns)
                logger.info(f"为{intent_type}意图添加模式: {patterns}")
        else:
            logger.warning(f"未知的意图类型: {intent_type}")
    
    def __str__(self) -> str:
        """返回路由器的字符串表示"""
        return f"IntentRouter(rules={len(self.rules)}, priority={self.intent_priority})" 