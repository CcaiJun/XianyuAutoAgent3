"""
缓存管理器模块
提供内存缓存、过期管理、LRU清理等功能
"""

import time
import asyncio
import json
from typing import Dict, Any, Optional, Union, Set
from collections import OrderedDict
from dataclasses import dataclass, field
from config.logger_config import get_logger
from config.config_manager import ConfigManager

# 获取专用日志记录器
logger = get_logger("data", "cache")


@dataclass
class CacheItem:
    """
    缓存项数据结构
    """
    value: Any
    created_at: float = field(default_factory=time.time)
    accessed_at: float = field(default_factory=time.time)
    access_count: int = 0
    expire_at: Optional[float] = None
    
    def is_expired(self) -> bool:
        """检查是否已过期"""
        if self.expire_at is None:
            return False
        return time.time() > self.expire_at
    
    def touch(self):
        """更新访问时间"""
        self.accessed_at = time.time()
        self.access_count += 1


class CacheManager:
    """
    内存缓存管理器
    提供LRU淘汰策略、自动过期、分类存储等功能
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        """
        初始化缓存管理器
        
        Args:
            max_size: 最大缓存项数量
            default_ttl: 默认过期时间（秒）
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.config_manager = ConfigManager()
        
        # 分类缓存存储
        self._caches: Dict[str, OrderedDict] = {
            'sessions': OrderedDict(),     # 会话缓存
            'items': OrderedDict(),        # 商品信息缓存
            'bargains': OrderedDict(),     # 议价信息缓存
            'messages': OrderedDict(),     # 消息缓存
            'users': OrderedDict(),        # 用户信息缓存
            'api_responses': OrderedDict() # API响应缓存
        }
        
        # 统计信息
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expirations': 0,
            'total_sets': 0,
            'total_gets': 0
        }
        
        # 清理任务
        self._cleanup_task = None
        self._running = False
    
    async def start(self):
        """启动缓存管理器"""
        if self._running:
            return
            
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("缓存管理器已启动")
    
    async def stop(self):
        """停止缓存管理器"""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        logger.info("缓存管理器已停止")
    
    def set(
        self, 
        category: str, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """
        设置缓存项
        
        Args:
            category: 缓存分类
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），None表示使用默认值
            
        Returns:
            是否设置成功
        """
        try:
            if category not in self._caches:
                logger.warning(f"未知的缓存分类: {category}")
                return False
            
            cache = self._caches[category]
            expire_time = None
            
            if ttl is not None:
                expire_time = time.time() + ttl
            elif self.default_ttl > 0:
                expire_time = time.time() + self.default_ttl
            
            cache_item = CacheItem(
                value=value,
                expire_at=expire_time
            )
            
            # 如果key已存在，移动到末尾
            if key in cache:
                del cache[key]
            
            cache[key] = cache_item
            
            # 检查是否需要LRU清理
            if len(cache) > self.max_size:
                self._evict_lru(category)
            
            self._stats['total_sets'] += 1
            return True
            
        except Exception as e:
            logger.error(f"设置缓存失败: {category}/{key} - {e}")
            return False
    
    def get(self, category: str, key: str) -> Optional[Any]:
        """
        获取缓存项
        
        Args:
            category: 缓存分类
            key: 缓存键
            
        Returns:
            缓存值，如果不存在或已过期返回None
        """
        try:
            self._stats['total_gets'] += 1
            
            if category not in self._caches:
                logger.warning(f"未知的缓存分类: {category}")
                self._stats['misses'] += 1
                return None
            
            cache = self._caches[category]
            
            if key not in cache:
                self._stats['misses'] += 1
                return None
            
            cache_item = cache[key]
            
            # 检查是否过期
            if cache_item.is_expired():
                del cache[key]
                self._stats['misses'] += 1
                self._stats['expirations'] += 1
                return None
            
            # 更新访问信息并移动到末尾（LRU）
            cache_item.touch()
            cache.move_to_end(key)
            
            self._stats['hits'] += 1
            return cache_item.value
            
        except Exception as e:
            logger.error(f"获取缓存失败: {category}/{key} - {e}")
            self._stats['misses'] += 1
            return None
    
    def delete(self, category: str, key: str) -> bool:
        """
        删除缓存项
        
        Args:
            category: 缓存分类
            key: 缓存键
            
        Returns:
            是否删除成功
        """
        try:
            if category not in self._caches:
                return False
            
            cache = self._caches[category]
            if key in cache:
                del cache[key]
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"删除缓存失败: {category}/{key} - {e}")
            return False
    
    def exists(self, category: str, key: str) -> bool:
        """
        检查缓存项是否存在且未过期
        
        Args:
            category: 缓存分类
            key: 缓存键
            
        Returns:
            是否存在
        """
        return self.get(category, key) is not None
    
    def clear_category(self, category: str) -> int:
        """
        清空指定分类的缓存
        
        Args:
            category: 缓存分类
            
        Returns:
            清理的项数
        """
        try:
            if category not in self._caches:
                return 0
            
            count = len(self._caches[category])
            self._caches[category].clear()
            logger.info(f"清空缓存分类 {category}，共清理 {count} 项")
            return count
            
        except Exception as e:
            logger.error(f"清空缓存分类失败: {category} - {e}")
            return 0
    
    def clear_all(self) -> int:
        """
        清空所有缓存
        
        Returns:
            清理的项数
        """
        total_count = 0
        for category in self._caches:
            total_count += self.clear_category(category)
        
        # 重置统计信息
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expirations': 0,
            'total_sets': 0,
            'total_gets': 0
        }
        
        logger.info(f"清空所有缓存，共清理 {total_count} 项")
        return total_count
    
    def _evict_lru(self, category: str):
        """LRU淘汰策略"""
        try:
            cache = self._caches[category]
            if not cache:
                return
            
            # 移除最久未使用的项
            oldest_key = next(iter(cache))
            del cache[oldest_key]
            self._stats['evictions'] += 1
            
        except Exception as e:
            logger.error(f"LRU淘汰失败: {category} - {e}")
    
    def _cleanup_expired(self) -> int:
        """清理所有过期的缓存项"""
        total_cleaned = 0
        
        try:
            for category, cache in self._caches.items():
                expired_keys = []
                
                for key, cache_item in cache.items():
                    if cache_item.is_expired():
                        expired_keys.append(key)
                
                for key in expired_keys:
                    del cache[key]
                    total_cleaned += 1
                    self._stats['expirations'] += 1
                
                if expired_keys:
                    logger.debug(f"清理 {category} 分类下 {len(expired_keys)} 个过期缓存项")
            
            return total_cleaned
            
        except Exception as e:
            logger.error(f"清理过期缓存失败: {e}")
            return 0
    
    async def _cleanup_loop(self):
        """后台清理循环"""
        cleanup_interval = 300  # 5分钟清理一次
        
        while self._running:
            try:
                await asyncio.sleep(cleanup_interval)
                
                if not self._running:
                    break
                
                cleaned_count = self._cleanup_expired()
                if cleaned_count > 0:
                    logger.info(f"定期清理完成，清理了 {cleaned_count} 个过期缓存项")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"缓存清理循环异常: {e}")
                await asyncio.sleep(60)  # 出错时减少清理频率
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            统计信息字典
        """
        try:
            # 计算各分类大小
            category_sizes = {}
            total_items = 0
            
            for category, cache in self._caches.items():
                size = len(cache)
                category_sizes[category] = size
                total_items += size
            
            # 计算命中率
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = self._stats['hits'] / total_requests if total_requests > 0 else 0.0
            
            return {
                'total_items': total_items,
                'max_size': self.max_size,
                'default_ttl': self.default_ttl,
                'category_sizes': category_sizes,
                'hit_rate': round(hit_rate, 4),
                'stats': self._stats.copy()
            }
            
        except Exception as e:
            logger.error(f"获取缓存统计失败: {e}")
            return {}
    
    def get_health_info(self) -> Dict[str, Any]:
        """
        获取健康状态信息
        
        Returns:
            健康状态字典
        """
        stats = self.get_stats()
        
        return {
            "status": "healthy" if self._running else "stopped",
            "total_items": stats.get('total_items', 0),
            "hit_rate": stats.get('hit_rate', 0.0),
            "memory_usage_percent": round(
                (stats.get('total_items', 0) / self.max_size) * 100, 2
            ) if self.max_size > 0 else 0,
            "cleanup_running": self._cleanup_task is not None and not self._cleanup_task.done()
        }
    
    # 便捷方法
    def set_session(self, session_id: str, session_data: Any, ttl: Optional[int] = None) -> bool:
        """设置会话缓存"""
        return self.set('sessions', session_id, session_data, ttl)
    
    def get_session(self, session_id: str) -> Optional[Any]:
        """获取会话缓存"""
        return self.get('sessions', session_id)
    
    def set_item(self, item_id: str, item_data: Any, ttl: Optional[int] = None) -> bool:
        """设置商品缓存"""
        return self.set('items', item_id, item_data, ttl)
    
    def get_item(self, item_id: str) -> Optional[Any]:
        """获取商品缓存"""
        return self.get('items', item_id)
    
    def set_bargain(self, chat_id: str, bargain_data: Any, ttl: Optional[int] = None) -> bool:
        """设置议价缓存"""
        return self.set('bargains', chat_id, bargain_data, ttl)
    
    def get_bargain(self, chat_id: str) -> Optional[Any]:
        """获取议价缓存"""
        return self.get('bargains', chat_id)
    
    def set_api_response(self, api_key: str, response_data: Any, ttl: Optional[int] = None) -> bool:
        """设置API响应缓存"""
        return self.set('api_responses', api_key, response_data, ttl)
    
    def get_api_response(self, api_key: str) -> Optional[Any]:
        """获取API响应缓存"""
        return self.get('api_responses', api_key) 