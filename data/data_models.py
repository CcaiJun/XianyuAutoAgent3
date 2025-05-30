"""
数据模型模块
定义项目中使用的各种数据结构和验证规则
"""

import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from config.logger_config import get_logger

# 获取专用日志记录器
logger = get_logger("data", "models")


@dataclass
class MessageModel:
    """
    消息数据模型
    表示聊天系统中的单条消息
    """
    id: Optional[int] = None
    chat_id: str = ""
    user_id: str = ""
    item_id: str = ""
    role: str = "user"  # user, assistant, system
    content: str = ""
    timestamp: float = field(default_factory=time.time)
    created_at: Optional[str] = None
    
    def __post_init__(self):
        """初始化后的处理"""
        if self.created_at is None:
            self.created_at = datetime.fromtimestamp(self.timestamp).isoformat()
        
        # 验证必要字段
        if not self.chat_id:
            raise ValueError("chat_id不能为空")
        if not self.user_id:
            raise ValueError("user_id不能为空")
        if not self.content:
            raise ValueError("content不能为空")
        if self.role not in ["user", "assistant", "system"]:
            raise ValueError("role必须是user、assistant或system")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "chat_id": self.chat_id,
            "user_id": self.user_id,
            "item_id": self.item_id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MessageModel':
        """从字典创建实例"""
        return cls(
            id=data.get("id"),
            chat_id=data.get("chat_id", ""),
            user_id=data.get("user_id", ""),
            item_id=data.get("item_id", ""),
            role=data.get("role", "user"),
            content=data.get("content", ""),
            timestamp=data.get("timestamp", time.time()),
            created_at=data.get("created_at")
        )
    
    def to_openai_format(self) -> Dict[str, str]:
        """转换为OpenAI聊天格式"""
        return {
            "role": self.role,
            "content": self.content
        }


@dataclass
class ItemModel:
    """
    商品数据模型
    表示闲鱼商品信息
    """
    item_id: str = ""
    title: str = ""
    description: str = ""
    price: float = 0.0
    seller_id: str = ""
    seller_name: str = ""
    category: str = ""
    condition: str = ""  # 新品、二手等
    location: str = ""
    images: List[str] = field(default_factory=list)
    raw_data: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def __post_init__(self):
        """初始化后的处理"""
        current_time = datetime.now().isoformat()
        if self.created_at is None:
            self.created_at = current_time
        if self.updated_at is None:
            self.updated_at = current_time
        
        # 验证必要字段
        if not self.item_id:
            raise ValueError("item_id不能为空")
        if self.price < 0:
            raise ValueError("price不能为负数")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "item_id": self.item_id,
            "title": self.title,
            "description": self.description,
            "price": self.price,
            "seller_id": self.seller_id,
            "seller_name": self.seller_name,
            "category": self.category,
            "condition": self.condition,
            "location": self.location,
            "images": self.images,
            "raw_data": self.raw_data,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ItemModel':
        """从字典创建实例"""
        return cls(
            item_id=data.get("item_id", ""),
            title=data.get("title", ""),
            description=data.get("description", ""),
            price=float(data.get("price", 0.0)),
            seller_id=data.get("seller_id", ""),
            seller_name=data.get("seller_name", ""),
            category=data.get("category", ""),
            condition=data.get("condition", ""),
            location=data.get("location", ""),
            images=data.get("images", []),
            raw_data=data.get("raw_data", {}),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )
    
    @classmethod
    def from_api_data(cls, item_id: str, api_data: Dict[str, Any]) -> 'ItemModel':
        """从API数据创建实例"""
        try:
            return cls(
                item_id=item_id,
                title=api_data.get("title", ""),
                description=api_data.get("desc", ""),
                price=float(api_data.get("soldPrice", 0.0)),
                seller_id=api_data.get("sellerId", ""),
                seller_name=api_data.get("sellerName", ""),
                category=api_data.get("category", ""),
                condition=api_data.get("condition", ""),
                location=api_data.get("location", ""),
                images=api_data.get("images", []),
                raw_data=api_data
            )
        except Exception as e:
            logger.error(f"从API数据创建商品模型失败: {e}")
            raise
    
    def get_description_for_ai(self) -> str:
        """获取用于AI的商品描述"""
        return f"{self.description};当前商品售卖价格为:{self.price}元"
    
    def update_from_api_data(self, api_data: Dict[str, Any]):
        """从API数据更新商品信息"""
        self.title = api_data.get("title", self.title)
        self.description = api_data.get("desc", self.description)
        self.price = float(api_data.get("soldPrice", self.price))
        self.seller_id = api_data.get("sellerId", self.seller_id)
        self.seller_name = api_data.get("sellerName", self.seller_name)
        self.category = api_data.get("category", self.category)
        self.condition = api_data.get("condition", self.condition)
        self.location = api_data.get("location", self.location)
        self.images = api_data.get("images", self.images)
        self.raw_data = api_data
        self.updated_at = datetime.now().isoformat()


@dataclass
class BargainModel:
    """
    议价数据模型
    表示用户在特定会话中的议价信息
    """
    chat_id: str = ""
    item_id: str = ""
    user_id: str = ""
    count: int = 0
    last_bargain_time: float = field(default_factory=time.time)
    last_bargain_content: str = ""
    target_price: Optional[float] = None
    negotiation_history: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "active"  # active, completed, failed
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def __post_init__(self):
        """初始化后的处理"""
        current_time = datetime.now().isoformat()
        if self.created_at is None:
            self.created_at = current_time
        if self.updated_at is None:
            self.updated_at = current_time
        
        # 验证必要字段
        if not self.chat_id:
            raise ValueError("chat_id不能为空")
        if self.count < 0:
            raise ValueError("count不能为负数")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "chat_id": self.chat_id,
            "item_id": self.item_id,
            "user_id": self.user_id,
            "count": self.count,
            "last_bargain_time": self.last_bargain_time,
            "last_bargain_content": self.last_bargain_content,
            "target_price": self.target_price,
            "negotiation_history": self.negotiation_history,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BargainModel':
        """从字典创建实例"""
        return cls(
            chat_id=data.get("chat_id", ""),
            item_id=data.get("item_id", ""),
            user_id=data.get("user_id", ""),
            count=int(data.get("count", 0)),
            last_bargain_time=data.get("last_bargain_time", time.time()),
            last_bargain_content=data.get("last_bargain_content", ""),
            target_price=data.get("target_price"),
            negotiation_history=data.get("negotiation_history", []),
            status=data.get("status", "active"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )
    
    def increment_count(self, bargain_content: str, target_price: Optional[float] = None):
        """增加议价次数"""
        self.count += 1
        self.last_bargain_time = time.time()
        self.last_bargain_content = bargain_content
        if target_price is not None:
            self.target_price = target_price
        
        # 添加到协商历史
        self.negotiation_history.append({
            "count": self.count,
            "content": bargain_content,
            "target_price": target_price,
            "timestamp": self.last_bargain_time
        })
        
        self.updated_at = datetime.now().isoformat()
    
    def get_bargain_context(self) -> str:
        """获取议价上下文信息"""
        if self.count == 0:
            return ""
        
        context_parts = [f"议价次数: {self.count}"]
        
        if self.target_price:
            context_parts.append(f"目标价格: {self.target_price}元")
        
        if self.last_bargain_content:
            context_parts.append(f"最后议价内容: {self.last_bargain_content}")
        
        return "; ".join(context_parts)
    
    def is_high_frequency_bargain(self, threshold: int = 5) -> bool:
        """检查是否为高频议价"""
        return self.count >= threshold
    
    def get_bargain_trend(self) -> str:
        """获取议价趋势分析"""
        if len(self.negotiation_history) < 2:
            return "数据不足"
        
        # 简单的趋势分析
        prices = [h.get("target_price") for h in self.negotiation_history if h.get("target_price")]
        if len(prices) < 2:
            return "价格趋势不明"
        
        if prices[-1] < prices[0]:
            return "降价趋势"
        elif prices[-1] > prices[0]:
            return "提价趋势"
        else:
            return "价格稳定"


@dataclass
class SessionModel:
    """
    会话数据模型
    表示用户会话的状态和配置信息
    """
    chat_id: str = ""
    user_id: str = ""
    item_id: str = ""
    mode: str = "auto"  # auto, manual
    status: str = "active"  # active, ended, paused
    start_time: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    message_count: int = 0
    manual_interventions: int = 0
    ai_responses: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def __post_init__(self):
        """初始化后的处理"""
        current_time = datetime.now().isoformat()
        if self.created_at is None:
            self.created_at = current_time
        if self.updated_at is None:
            self.updated_at = current_time
        
        # 验证必要字段
        if not self.chat_id:
            raise ValueError("chat_id不能为空")
        if self.mode not in ["auto", "manual"]:
            raise ValueError("mode必须是auto或manual")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "chat_id": self.chat_id,
            "user_id": self.user_id,
            "item_id": self.item_id,
            "mode": self.mode,
            "status": self.status,
            "start_time": self.start_time,
            "last_activity": self.last_activity,
            "message_count": self.message_count,
            "manual_interventions": self.manual_interventions,
            "ai_responses": self.ai_responses,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionModel':
        """从字典创建实例"""
        return cls(
            chat_id=data.get("chat_id", ""),
            user_id=data.get("user_id", ""),
            item_id=data.get("item_id", ""),
            mode=data.get("mode", "auto"),
            status=data.get("status", "active"),
            start_time=data.get("start_time", time.time()),
            last_activity=data.get("last_activity", time.time()),
            message_count=int(data.get("message_count", 0)),
            manual_interventions=int(data.get("manual_interventions", 0)),
            ai_responses=int(data.get("ai_responses", 0)),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )
    
    def update_activity(self, is_manual: bool = False, is_ai: bool = False):
        """更新活动信息"""
        self.last_activity = time.time()
        self.message_count += 1
        
        if is_manual:
            self.manual_interventions += 1
        if is_ai:
            self.ai_responses += 1
        
        self.updated_at = datetime.now().isoformat()
    
    def switch_mode(self, new_mode: str):
        """切换会话模式"""
        if new_mode not in ["auto", "manual"]:
            raise ValueError("mode必须是auto或manual")
        
        old_mode = self.mode
        self.mode = new_mode
        self.last_activity = time.time()
        self.updated_at = datetime.now().isoformat()
        
        # 记录模式切换到元数据
        if "mode_switches" not in self.metadata:
            self.metadata["mode_switches"] = []
        
        self.metadata["mode_switches"].append({
            "from": old_mode,
            "to": new_mode,
            "timestamp": self.last_activity
        })
    
    def get_duration(self) -> float:
        """获取会话持续时间（秒）"""
        return self.last_activity - self.start_time
    
    def get_activity_rate(self) -> float:
        """获取活动频率（消息/小时）"""
        duration_hours = self.get_duration() / 3600
        if duration_hours == 0:
            return 0
        return self.message_count / duration_hours 