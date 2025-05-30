"""
技术代理模块
专门负责处理商品参数、规格、技术问题等技术咨询
提供专业的技术支持和产品对比功能
"""

import re
from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent
from config.logger_config import get_logger
from utils.constants import AGENT_TECH

# 获取专用日志记录器
logger = get_logger("agent", "tech")


class TechAgent(BaseAgent):
    """
    技术代理 - 技术专家
    专门处理商品技术参数、规格咨询、产品对比等技术问题
    提供准确专业的技术支持
    """
    
    def __init__(self, client, system_prompt):
        """
        初始化技术代理
        
        Args:
            client: OpenAI客户端实例
            system_prompt: 技术专用的系统提示词
        """
        super().__init__(client, system_prompt, AGENT_TECH)
        
        # 技术代理特定配置
        self.max_tokens = 2000  # 技术解释通常需要更多详细信息
        self.temperature = 0.3  # 低温度确保技术信息的准确性
        
        # 技术问题分类
        self.tech_categories = {
            "specifications": {  # 规格参数
                "keywords": ["参数", "规格", "配置", "尺寸", "重量", "材质", "功率"],
                "approach": "detailed_specs"
            },
            "compatibility": {  # 兼容性问题
                "keywords": ["兼容", "支持", "适配", "匹配", "能否", "可以用"],
                "approach": "compatibility_check"
            },
            "comparison": {  # 产品对比
                "keywords": ["对比", "比较", "区别", "差异", "哪个好", "选择"],
                "approach": "comparative_analysis"
            },
            "usage": {  # 使用方法
                "keywords": ["怎么用", "如何", "使用方法", "操作", "设置", "安装"],
                "approach": "usage_guide"
            },
            "performance": {  # 性能相关
                "keywords": ["性能", "速度", "效果", "质量", "耐用", "寿命"],
                "approach": "performance_analysis"
            },
            "technical_issues": {  # 技术问题
                "keywords": ["问题", "故障", "不能", "无法", "错误", "异常"],
                "approach": "troubleshooting"
            }
        }
        
        # 常见技术参数模式
        self.spec_patterns = {
            "dimensions": r'(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)\s*[x×]?\s*(\d+(?:\.\d+)?)?',  # 尺寸
            "weight": r'(\d+(?:\.\d+)?)\s*(kg|g|公斤|克)',  # 重量
            "power": r'(\d+(?:\.\d+)?)\s*(w|瓦|功率)',  # 功率
            "voltage": r'(\d+(?:\.\d+)?)\s*(v|伏)',  # 电压
            "frequency": r'(\d+(?:\.\d+)?)\s*(hz|赫兹)',  # 频率
            "capacity": r'(\d+(?:\.\d+)?)\s*(l|ml|升|毫升)',  # 容量
        }
        
        logger.info("技术代理初始化完成")
    
    def generate(self, user_msg: str, item_desc: str, context: str, 
                bargain_count: int = 0, **kwargs) -> str:
        """
        生成技术相关的回复
        
        Args:
            user_msg: 用户消息
            item_desc: 商品描述
            context: 对话上下文
            bargain_count: 议价次数（技术代理较少使用）
            **kwargs: 其他参数
            
        Returns:
            技术代理的回复
        """
        logger.debug(f"技术代理开始处理消息: {user_msg[:50]}...")
        
        try:
            # 分析技术问题类型
            tech_analysis = self._analyze_tech_question(user_msg)
            
            # 提取商品技术信息
            tech_specs = self._extract_tech_specs(item_desc)
            
            # 构建技术专用消息
            messages = self._build_tech_messages(
                user_msg, item_desc, context, bargain_count,
                tech_analysis=tech_analysis,
                tech_specs=tech_specs
            )
            
            # 调用LLM生成回复
            raw_reply = self._call_llm(messages)
            
            # 技术回复的后处理
            processed_reply = self._post_process_tech_reply(raw_reply, tech_analysis)
            
            # 安全过滤
            safe_reply = self._safety_filter(processed_reply)
            
            logger.info(f"技术代理回复生成完成，问题类型: {tech_analysis.get('category', 'unknown')}")
            return safe_reply
            
        except Exception as e:
            logger.error(f"技术代理处理失败: {e}")
            return self._get_fallback_tech_reply(user_msg)
    
    def _analyze_tech_question(self, user_msg: str) -> Dict[str, Any]:
        """
        分析用户的技术问题类型和意图
        
        Args:
            user_msg: 用户消息
            
        Returns:
            技术问题分析结果
        """
        analysis = {
            "category": "general",
            "subcategory": None,
            "complexity": "medium",
            "requires_specs": False,
            "comparison_needed": False,
            "matched_keywords": []
        }
        
        # 分析问题类别
        for category, config in self.tech_categories.items():
            matched_keywords = [kw for kw in config["keywords"] if kw in user_msg]
            if matched_keywords:
                analysis["category"] = category
                analysis["approach"] = config["approach"]
                analysis["matched_keywords"] = matched_keywords
                break
        
        # 判断复杂度
        if any(word in user_msg for word in ["详细", "具体", "全面", "深入"]):
            analysis["complexity"] = "high"
        elif any(word in user_msg for word in ["简单", "大概", "基本"]):
            analysis["complexity"] = "low"
        
        # 判断是否需要规格参数
        if any(word in user_msg for word in ["参数", "规格", "配置", "尺寸", "重量"]):
            analysis["requires_specs"] = True
        
        # 判断是否需要对比
        if any(word in user_msg for word in ["对比", "比较", "区别", "哪个", "选择"]):
            analysis["comparison_needed"] = True
        
        logger.debug(f"技术问题分析: {analysis}")
        return analysis
    
    def _extract_tech_specs(self, item_desc: str) -> Dict[str, Any]:
        """
        从商品描述中提取技术规格参数
        
        Args:
            item_desc: 商品描述
            
        Returns:
            提取的技术规格信息
        """
        specs = {
            "extracted_specs": {},
            "structured_data": {},
            "missing_specs": []
        }
        
        if not item_desc:
            return specs
        
        # 使用正则模式提取具体参数
        for spec_type, pattern in self.spec_patterns.items():
            matches = re.findall(pattern, item_desc, re.IGNORECASE)
            if matches:
                specs["extracted_specs"][spec_type] = matches
        
        # 提取常见的结构化信息
        # 品牌信息
        brand_match = re.search(r'品牌[:：]\s*([^\s\n]+)', item_desc)
        if brand_match:
            specs["structured_data"]["brand"] = brand_match.group(1)
        
        # 型号信息
        model_match = re.search(r'型号[:：]\s*([^\s\n]+)', item_desc)
        if model_match:
            specs["structured_data"]["model"] = model_match.group(1)
        
        # 材质信息
        material_match = re.search(r'材质[:：]\s*([^\s\n]+)', item_desc)
        if material_match:
            specs["structured_data"]["material"] = material_match.group(1)
        
        # 颜色信息
        color_match = re.search(r'颜色[:：]\s*([^\s\n]+)', item_desc)
        if color_match:
            specs["structured_data"]["color"] = color_match.group(1)
        
        logger.debug(f"提取的技术规格: {specs}")
        return specs
    
    def _build_tech_messages(self, user_msg: str, item_desc: str, context: str,
                            bargain_count: int, **kwargs) -> list:
        """
        构建技术专用的消息格式
        
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
        
        # 添加技术分析信息
        tech_analysis = kwargs.get('tech_analysis', {})
        if tech_analysis:
            system_content += f"""

【技术问题分析】
问题类别: {tech_analysis.get('category', '一般技术问题')}
处理方式: {tech_analysis.get('approach', '标准回复')}
复杂程度: {tech_analysis.get('complexity', '中等')}
需要规格参数: {tech_analysis.get('requires_specs', False)}
需要产品对比: {tech_analysis.get('comparison_needed', False)}
匹配关键词: {', '.join(tech_analysis.get('matched_keywords', []))}

请根据以上分析提供准确专业的技术回复。
"""
        
        # 添加提取的技术规格
        tech_specs = kwargs.get('tech_specs', {})
        if tech_specs and tech_specs.get('structured_data'):
            system_content += f"""

【商品技术规格】
"""
            for key, value in tech_specs['structured_data'].items():
                system_content += f"{key}: {value}\n"
            
            if tech_specs.get('extracted_specs'):
                system_content += "\n【提取的参数信息】\n"
                for spec_type, values in tech_specs['extracted_specs'].items():
                    system_content += f"{spec_type}: {values}\n"
        
        # 使用基类的消息构建方法
        return self._build_messages(user_msg, item_desc, context, bargain_count, **kwargs)
    
    def _post_process_tech_reply(self, reply: str, tech_analysis: Dict) -> str:
        """
        对技术回复进行后处理
        
        Args:
            reply: 原始回复
            tech_analysis: 技术问题分析结果
            
        Returns:
            处理后的回复
        """
        if not reply:
            return reply
        
        category = tech_analysis.get('category', 'general')
        
        # 根据问题类别调整回复格式
        if category == "specifications" and not self._has_spec_format(reply):
            reply = self._format_specifications(reply)
        elif category == "comparison" and not self._has_comparison_format(reply):
            reply = self._format_comparison(reply)
        elif category == "troubleshooting":
            reply = self._format_troubleshooting(reply)
        
        # 技术术语的规范化
        reply = self._normalize_tech_terms(reply)
        
        return self._post_process(reply)
    
    def _has_spec_format(self, reply: str) -> bool:
        """检查回复是否已经包含规格格式"""
        return any(indicator in reply for indicator in ['参数：', '规格：', '配置：', '尺寸：'])
    
    def _has_comparison_format(self, reply: str) -> bool:
        """检查回复是否已经包含对比格式"""
        return any(indicator in reply for indicator in ['对比：', '区别：', '相比', '差异：'])
    
    def _format_specifications(self, reply: str) -> str:
        """格式化规格参数回复"""
        if "参数" in reply or "规格" in reply:
            return reply
        return f"【产品规格参数】\n{reply}"
    
    def _format_comparison(self, reply: str) -> str:
        """格式化对比回复"""
        if "对比" in reply or "区别" in reply:
            return reply
        return f"【产品对比分析】\n{reply}"
    
    def _format_troubleshooting(self, reply: str) -> str:
        """格式化故障排除回复"""
        if "解决方案" in reply or "建议" in reply:
            return reply
        return f"【技术解决方案】\n{reply}"
    
    def _normalize_tech_terms(self, reply: str) -> str:
        """
        规范化技术术语
        
        Args:
            reply: 原始回复
            
        Returns:
            规范化后的回复
        """
        # 单位规范化
        reply = re.sub(r'(\d+)\s*mm', r'\1毫米', reply)
        reply = re.sub(r'(\d+)\s*cm', r'\1厘米', reply)
        reply = re.sub(r'(\d+)\s*kg', r'\1千克', reply)
        reply = re.sub(r'(\d+)\s*w', r'\1瓦', reply, flags=re.IGNORECASE)
        
        # 技术术语规范化
        tech_terms = {
            'CPU': '处理器',
            'RAM': '内存',
            'ROM': '存储',
            'GPU': '显卡',
            'USB': 'USB接口',
            'WiFi': 'Wi-Fi',
            'Bluetooth': '蓝牙'
        }
        
        for english, chinese in tech_terms.items():
            reply = re.sub(f'\\b{english}\\b', chinese, reply, flags=re.IGNORECASE)
        
        return reply
    
    def _get_fallback_tech_reply(self, user_msg: str) -> str:
        """
        获取技术代理的兜底回复
        
        Args:
            user_msg: 用户消息
            
        Returns:
            兜底回复
        """
        # 根据消息中的关键词提供不同的兜底回复
        if any(word in user_msg for word in ['参数', '规格', '配置']):
            return "关于产品的详细参数规格，我需要查看具体的商品信息才能为您提供准确的答案。请您提供更多商品细节，我会尽力为您解答。"
        elif any(word in user_msg for word in ['兼容', '支持', '适配']):
            return "关于产品兼容性问题，这需要根据具体的使用环境和设备来判断。建议您提供更详细的使用场景，我可以为您做专业的兼容性分析。"
        elif any(word in user_msg for word in ['对比', '比较', '区别']):
            return "产品对比需要明确对比的具体型号或品牌。请您告诉我需要对比的产品信息，我会为您提供详细的对比分析。"
        else:
            return "这是一个很好的技术问题。为了给您提供最准确的答案，建议您提供更多相关的技术细节或具体需求，我会为您做专业的技术分析。"
    
    def get_supported_tech_categories(self) -> List[str]:
        """
        获取支持的技术问题类别
        
        Returns:
            支持的技术类别列表
        """
        return list(self.tech_categories.keys())
    
    def get_tech_statistics(self) -> Dict[str, Any]:
        """
        获取技术代理统计信息
        
        Returns:
            技术代理统计数据
        """
        return {
            "supported_categories": len(self.tech_categories),
            "spec_patterns": len(self.spec_patterns),
            "category_list": list(self.tech_categories.keys()),
            "pattern_types": list(self.spec_patterns.keys())
        }
    
    def update_tech_patterns(self, new_patterns: Dict[str, str]):
        """
        更新技术参数识别模式
        
        Args:
            new_patterns: 新的正则模式字典
        """
        self.spec_patterns.update(new_patterns)
        logger.info(f"技术参数模式已更新，新增 {len(new_patterns)} 个模式")
    
    def add_tech_category(self, category_name: str, keywords: List[str], approach: str):
        """
        添加新的技术问题类别
        
        Args:
            category_name: 类别名称
            keywords: 关键词列表
            approach: 处理方式
        """
        self.tech_categories[category_name] = {
            "keywords": keywords,
            "approach": approach
        }
        logger.info(f"添加新技术类别: {category_name}") 