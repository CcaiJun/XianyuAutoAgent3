"""
默认代理模块
处理通用客服问题、售后服务、一般咨询等场景
作为系统的兜底代理，提供友好的客服体验
"""

import re
from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent
from config.logger_config import get_logger
from utils.constants import AGENT_DEFAULT

# 获取专用日志记录器
logger = get_logger("agent", "default")


class DefaultAgent(BaseAgent):
    """
    默认代理 - 通用客服
    处理一般性客服咨询、售后服务、问候等通用场景
    确保所有用户问题都能得到友好的回复
    """
    
    def __init__(self, client, system_prompt):
        """
        初始化默认代理
        
        Args:
            client: OpenAI客户端实例
            system_prompt: 默认客服的系统提示词
        """
        super().__init__(client, system_prompt, AGENT_DEFAULT)
        
        # 默认代理特定配置
        self.max_tokens = 1000  # 一般客服回复相对简洁
        self.temperature = 0.8  # 较高温度保持友好亲切
        
        # 客服问题类别
        self.service_categories = {
            "greeting": {  # 问候打招呼
                "keywords": ["你好", "您好", "在吗", "有人吗", "打扰", "咨询"],
                "response_style": "friendly_greeting"
            },
            "shipping": {  # 物流发货
                "keywords": ["发货", "物流", "快递", "运费", "邮费", "包邮", "几天到"],
                "response_style": "informative"
            },
            "after_sales": {  # 售后服务
                "keywords": ["售后", "保修", "维修", "换货", "退货", "质量问题"],
                "response_style": "supportive"
            },
            "payment": {  # 支付相关
                "keywords": ["支付", "付款", "怎么买", "订单", "购买", "下单"],
                "response_style": "guidance"
            },
            "general_inquiry": {  # 一般咨询
                "keywords": ["怎么样", "好用吗", "推荐", "建议", "意见"],
                "response_style": "consultative"
            },
            "complaint": {  # 投诉抱怨
                "keywords": ["投诉", "不满意", "差评", "问题", "糟糕", "失望"],
                "response_style": "apologetic"
            },
            "praise": {  # 表扬好评
                "keywords": ["好评", "满意", "不错", "喜欢", "赞", "棒"],
                "response_style": "appreciative"
            }
        }
        
        # 常用的友好回复模板
        self.response_templates = {
            "greeting": [
                "您好！很高兴为您服务，有什么可以帮助您的吗？",
                "您好！欢迎咨询，我是您的专属客服，有什么问题尽管问我~",
                "您好！感谢您的关注，有任何疑问我都会耐心为您解答。"
            ],
            "thanks": [
                "不客气，这是我应该做的！",
                "很高兴能帮到您！",
                "为您服务是我的荣幸！"
            ],
            "apology": [
                "非常抱歉给您带来了困扰",
                "对于这个问题我深表歉意",
                "很抱歉让您有不好的体验"
            ]
        }
        
        # 情感识别模式
        self.emotion_patterns = {
            "positive": r'(好|棒|不错|满意|喜欢|赞|优秀|完美)',
            "negative": r'(差|糟|烂|失望|不满|讨厌|垃圾|问题)',
            "urgent": r'(急|赶紧|马上|立即|尽快|紧急)',
            "polite": r'(请|谢谢|麻烦|打扰|不好意思|劳烦)'
        }
        
        logger.info("默认代理初始化完成")
    
    def generate(self, user_msg: str, item_desc: str, context: str, 
                bargain_count: int = 0, **kwargs) -> str:
        """
        生成默认客服回复
        
        Args:
            user_msg: 用户消息
            item_desc: 商品描述
            context: 对话上下文
            bargain_count: 议价次数
            **kwargs: 其他参数
            
        Returns:
            默认代理的回复
        """
        logger.debug(f"默认代理开始处理消息: {user_msg[:50]}...")
        
        try:
            # 分析客服问题类型
            service_analysis = self._analyze_service_type(user_msg)
            
            # 识别用户情感
            emotion_analysis = self._analyze_emotion(user_msg)
            
            # 检查是否需要特殊处理
            special_handling = self._check_special_cases(user_msg, context)
            
            # 构建默认客服消息
            messages = self._build_default_messages(
                user_msg, item_desc, context, bargain_count,
                service_analysis=service_analysis,
                emotion_analysis=emotion_analysis,
                special_handling=special_handling
            )
            
            # 调用LLM生成回复
            raw_reply = self._call_llm(messages)
            
            # 客服回复的后处理
            processed_reply = self._post_process_service_reply(raw_reply, service_analysis, emotion_analysis)
            
            # 安全过滤
            safe_reply = self._safety_filter(processed_reply)
            
            logger.info(f"默认代理回复生成完成，问题类型: {service_analysis.get('category', 'unknown')}")
            return safe_reply
            
        except Exception as e:
            logger.error(f"默认代理处理失败: {e}")
            return self._get_fallback_service_reply(user_msg)
    
    def _analyze_service_type(self, user_msg: str) -> Dict[str, Any]:
        """
        分析客服问题类型
        
        Args:
            user_msg: 用户消息
            
        Returns:
            客服问题分析结果
        """
        analysis = {
            "category": "general_inquiry",
            "confidence": 0.5,
            "matched_keywords": [],
            "response_style": "consultative"
        }
        
        # 分析问题类别
        max_matches = 0
        for category, config in self.service_categories.items():
            matched_keywords = [kw for kw in config["keywords"] if kw in user_msg]
            if len(matched_keywords) > max_matches:
                max_matches = len(matched_keywords)
                analysis["category"] = category
                analysis["response_style"] = config["response_style"]
                analysis["matched_keywords"] = matched_keywords
                analysis["confidence"] = min(0.9, 0.3 + len(matched_keywords) * 0.2)
        
        logger.debug(f"客服问题分析: {analysis}")
        return analysis
    
    def _analyze_emotion(self, user_msg: str) -> Dict[str, Any]:
        """
        分析用户情感倾向
        
        Args:
            user_msg: 用户消息
            
        Returns:
            情感分析结果
        """
        emotion = {
            "dominant_emotion": "neutral",
            "emotions_detected": [],
            "sentiment_score": 0.0,
            "is_urgent": False,
            "is_polite": False
        }
        
        # 检测各种情感
        for emotion_type, pattern in self.emotion_patterns.items():
            if re.search(pattern, user_msg):
                emotion["emotions_detected"].append(emotion_type)
                
                if emotion_type == "positive":
                    emotion["sentiment_score"] += 0.3
                elif emotion_type == "negative":
                    emotion["sentiment_score"] -= 0.3
                elif emotion_type == "urgent":
                    emotion["is_urgent"] = True
                elif emotion_type == "polite":
                    emotion["is_polite"] = True
        
        # 确定主导情感
        if emotion["sentiment_score"] > 0.2:
            emotion["dominant_emotion"] = "positive"
        elif emotion["sentiment_score"] < -0.2:
            emotion["dominant_emotion"] = "negative"
        
        logger.debug(f"用户情感分析: {emotion}")
        return emotion
    
    def _check_special_cases(self, user_msg: str, context: str) -> Dict[str, Any]:
        """
        检查需要特殊处理的情况
        
        Args:
            user_msg: 用户消息
            context: 对话上下文
            
        Returns:
            特殊处理情况
        """
        special = {
            "is_repeat_question": False,
            "needs_human_transfer": False,
            "is_simple_thanks": False,
            "is_goodbye": False,
            "contains_personal_info": False
        }
        
        # 检查是否是重复问题
        if context and user_msg in context:
            special["is_repeat_question"] = True
        
        # 检查是否需要人工转接
        transfer_keywords = ["人工", "转人工", "真人", "客服", "经理"]
        if any(keyword in user_msg for keyword in transfer_keywords):
            special["needs_human_transfer"] = True
        
        # 检查是否是简单的感谢
        thanks_patterns = [r'^谢谢$', r'^感谢$', r'^多谢$', r'^thanks$']
        if any(re.match(pattern, user_msg.strip(), re.IGNORECASE) for pattern in thanks_patterns):
            special["is_simple_thanks"] = True
        
        # 检查是否是告别
        goodbye_keywords = ["再见", "拜拜", "88", "走了", "不买了", "goodbye", "bye"]
        if any(keyword in user_msg for keyword in goodbye_keywords):
            special["is_goodbye"] = True
        
        # 检查是否包含个人信息
        personal_patterns = [
            r'1[3-9]\d{9}',  # 手机号
            r'\d{15,18}',    # 身份证号
            r'\w+@\w+\.\w+', # 邮箱
        ]
        if any(re.search(pattern, user_msg) for pattern in personal_patterns):
            special["contains_personal_info"] = True
        
        logger.debug(f"特殊情况检查: {special}")
        return special
    
    def _build_default_messages(self, user_msg: str, item_desc: str, context: str,
                               bargain_count: int, **kwargs) -> list:
        """
        构建默认客服专用的消息格式
        
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
        
        # 添加客服分析信息
        service_analysis = kwargs.get('service_analysis', {})
        emotion_analysis = kwargs.get('emotion_analysis', {})
        special_handling = kwargs.get('special_handling', {})
        
        if service_analysis:
            system_content += f"""

【客服问题分析】
问题类别: {service_analysis.get('category', '一般咨询')}
回复风格: {service_analysis.get('response_style', '咨询式')}
置信度: {service_analysis.get('confidence', 0.5):.2f}
匹配关键词: {', '.join(service_analysis.get('matched_keywords', []))}

请采用{service_analysis.get('response_style', '咨询式')}的风格进行回复。
"""
        
        if emotion_analysis:
            system_content += f"""

【用户情感分析】
主导情感: {emotion_analysis.get('dominant_emotion', '中性')}
情感倾向: {', '.join(emotion_analysis.get('emotions_detected', []))}
是否紧急: {emotion_analysis.get('is_urgent', False)}
是否礼貌: {emotion_analysis.get('is_polite', False)}

请根据用户的情感状态调整回复的语气和内容。
"""
        
        if any(special_handling.values()):
            system_content += f"""

【特殊处理提醒】
重复问题: {special_handling.get('is_repeat_question', False)}
需要人工: {special_handling.get('needs_human_transfer', False)}
简单感谢: {special_handling.get('is_simple_thanks', False)}
告别意图: {special_handling.get('is_goodbye', False)}
个人信息: {special_handling.get('contains_personal_info', False)}

请根据特殊情况采取相应的处理方式。
"""
        
        # 使用基类的消息构建方法
        return self._build_messages(user_msg, item_desc, context, bargain_count, **kwargs)
    
    def _post_process_service_reply(self, reply: str, service_analysis: Dict, emotion_analysis: Dict) -> str:
        """
        对客服回复进行后处理
        
        Args:
            reply: 原始回复
            service_analysis: 客服问题分析
            emotion_analysis: 情感分析
            
        Returns:
            处理后的回复
        """
        if not reply:
            return reply
        
        # 根据情感调整语气
        dominant_emotion = emotion_analysis.get('dominant_emotion', 'neutral')
        if dominant_emotion == 'negative' and not any(word in reply for word in ['抱歉', '理解', '帮助']):
            reply = "我理解您的困扰，" + reply
        elif dominant_emotion == 'positive' and not any(word in reply for word in ['感谢', '高兴', '开心']):
            reply = reply + " 感谢您的认可！"
        
        # 根据紧急程度调整
        if emotion_analysis.get('is_urgent', False):
            reply = reply.replace('稍后', '立即').replace('等等', '马上')
        
        # 确保礼貌用语
        if emotion_analysis.get('is_polite', False) and not any(word in reply for word in ['请', '您']):
            reply = reply.replace('你', '您')
        
        # 客服专用的格式化
        reply = self._format_service_reply(reply, service_analysis.get('category', 'general_inquiry'))
        
        return self._post_process(reply)
    
    def _format_service_reply(self, reply: str, category: str) -> str:
        """
        根据问题类别格式化回复
        
        Args:
            reply: 原始回复
            category: 问题类别
            
        Returns:
            格式化后的回复
        """
        if category == "shipping" and "物流" not in reply and "发货" not in reply:
            reply = f"【物流信息】{reply}"
        elif category == "after_sales" and "售后" not in reply:
            reply = f"【售后服务】{reply}"
        elif category == "payment" and "支付" not in reply and "购买" not in reply:
            reply = f"【购买指南】{reply}"
        
        return reply
    
    def _get_fallback_service_reply(self, user_msg: str) -> str:
        """
        获取默认代理的兜底回复
        
        Args:
            user_msg: 用户消息
            
        Returns:
            兜底回复
        """
        # 根据消息内容选择合适的兜底回复
        if any(word in user_msg for word in ['你好', '您好', '在吗']):
            return "您好！很高兴为您服务，有什么可以帮助您的吗？"
        elif any(word in user_msg for word in ['谢谢', '感谢']):
            return "不客气！很高兴能帮到您，如果还有其他问题随时联系我~"
        elif any(word in user_msg for word in ['再见', '拜拜']):
            return "好的，祝您生活愉快！有任何问题欢迎随时回来咨询~"
        else:
            return "感谢您的咨询！我会尽力为您提供帮助。如果您的问题比较复杂，建议您提供更多详细信息，这样我能更好地为您服务。"
    
    def get_service_statistics(self) -> Dict[str, Any]:
        """
        获取客服统计信息
        
        Returns:
            客服统计数据
        """
        return {
            "supported_categories": len(self.service_categories),
            "response_templates": sum(len(templates) for templates in self.response_templates.values()),
            "emotion_patterns": len(self.emotion_patterns),
            "category_list": list(self.service_categories.keys())
        }
    
    def add_response_template(self, template_type: str, templates: List[str]):
        """
        添加回复模板
        
        Args:
            template_type: 模板类型
            templates: 模板列表
        """
        if template_type not in self.response_templates:
            self.response_templates[template_type] = []
        self.response_templates[template_type].extend(templates)
        logger.info(f"添加{template_type}类型模板 {len(templates)} 个")
    
    def update_service_category(self, category: str, keywords: List[str], response_style: str):
        """
        更新服务类别配置
        
        Args:
            category: 类别名称
            keywords: 关键词列表
            response_style: 回复风格
        """
        self.service_categories[category] = {
            "keywords": keywords,
            "response_style": response_style
        }
        logger.info(f"更新服务类别: {category}") 