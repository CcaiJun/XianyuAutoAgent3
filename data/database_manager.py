"""
数据库管理器模块
负责数据库连接、初始化、查询操作和事务管理
"""

import sqlite3
import asyncio
import aiosqlite
import json
import os
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from contextlib import asynccontextmanager
from config.logger_config import get_logger
from config.config_manager import ConfigManager
from utils.constants import DATABASE_FILE, DATABASE_TIMEOUT

# 获取专用日志记录器
logger = get_logger("data", "database")


class DatabaseManager:
    """
    异步数据库管理器
    提供数据库连接池管理、表操作、事务处理等功能
    """
    
    def __init__(self, db_path: str = DATABASE_FILE):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.config_manager = ConfigManager()
        self._pool = None
        self._connection_count = 0
        self._max_connections = 10
        self._initialized = False
        
        # 确保数据库目录存在
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
            logger.info(f"创建数据库目录: {db_dir}")
    
    async def initialize(self):
        """初始化数据库连接和表结构"""
        try:
            if self._initialized:
                return
                
            await self._create_tables()
            self._initialized = True
            logger.info("数据库管理器初始化完成")
            
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    async def _create_tables(self):
        """创建所有必要的数据库表"""
        async with self.get_connection() as conn:
            # 消息表
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
                    content TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (chat_id) REFERENCES sessions(chat_id)
                )
            ''')
            
            # 商品表
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS items (
                    item_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL DEFAULT '',
                    description TEXT NOT NULL DEFAULT '',
                    price REAL NOT NULL DEFAULT 0.0,
                    seller_id TEXT NOT NULL DEFAULT '',
                    seller_name TEXT NOT NULL DEFAULT '',
                    category TEXT NOT NULL DEFAULT '',
                    condition TEXT NOT NULL DEFAULT '',
                    location TEXT NOT NULL DEFAULT '',
                    images TEXT NOT NULL DEFAULT '[]',
                    raw_data TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')
            
            # 议价表
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS bargains (
                    chat_id TEXT PRIMARY KEY,
                    item_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    count INTEGER NOT NULL DEFAULT 0,
                    last_bargain_time REAL NOT NULL,
                    last_bargain_content TEXT NOT NULL DEFAULT '',
                    target_price REAL,
                    negotiation_history TEXT NOT NULL DEFAULT '[]',
                    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'completed', 'failed')),
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (chat_id) REFERENCES sessions(chat_id),
                    FOREIGN KEY (item_id) REFERENCES items(item_id)
                )
            ''')
            
            # 会话表
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    chat_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    mode TEXT NOT NULL DEFAULT 'auto' CHECK(mode IN ('auto', 'manual')),
                    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'ended', 'paused')),
                    start_time REAL NOT NULL,
                    last_activity REAL NOT NULL,
                    message_count INTEGER NOT NULL DEFAULT 0,
                    manual_interventions INTEGER NOT NULL DEFAULT 0,
                    ai_responses INTEGER NOT NULL DEFAULT 0,
                    metadata TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (item_id) REFERENCES items(item_id)
                )
            ''')
            
            # 创建索引
            await self._create_indexes(conn)
            await conn.commit()
            
        logger.info("数据库表结构创建完成")
    
    async def _create_indexes(self, conn):
        """创建数据库索引以优化查询性能"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id)",
            "CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_messages_user_item ON messages(user_id, item_id)",
            "CREATE INDEX IF NOT EXISTS idx_items_seller ON items(seller_id)",
            "CREATE INDEX IF NOT EXISTS idx_items_price ON items(price)",
            "CREATE INDEX IF NOT EXISTS idx_bargains_item ON bargains(item_id)",
            "CREATE INDEX IF NOT EXISTS idx_bargains_user ON bargains(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status)",
            "CREATE INDEX IF NOT EXISTS idx_sessions_activity ON sessions(last_activity)"
        ]
        
        for index_sql in indexes:
            await conn.execute(index_sql)
    
    @asynccontextmanager
    async def get_connection(self):
        """获取数据库连接的异步上下文管理器"""
        conn = None
        try:
            conn = await aiosqlite.connect(
                self.db_path,
                timeout=DATABASE_TIMEOUT,
                check_same_thread=False
            )
            conn.row_factory = aiosqlite.Row
            self._connection_count += 1
            logger.debug(f"获取数据库连接，当前连接数: {self._connection_count}")
            yield conn
            
        except Exception as e:
            logger.error(f"数据库连接异常: {e}")
            if conn:
                await conn.rollback()
            raise
        finally:
            if conn:
                await conn.close()
                self._connection_count -= 1
                logger.debug(f"关闭数据库连接，剩余连接数: {self._connection_count}")
    
    async def execute_query(
        self, 
        query: str, 
        params: tuple = (), 
        fetch_one: bool = False,
        fetch_all: bool = False
    ) -> Optional[Union[Dict[str, Any], List[Dict[str, Any]]]]:
        """
        执行查询操作
        
        Args:
            query: SQL查询语句
            params: 查询参数
            fetch_one: 是否只返回一行结果
            fetch_all: 是否返回所有结果
            
        Returns:
            查询结果
        """
        try:
            async with self.get_connection() as conn:
                cursor = await conn.execute(query, params)
                
                if fetch_one:
                    row = await cursor.fetchone()
                    return dict(row) if row else None
                elif fetch_all:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
                else:
                    await conn.commit()
                    return None
                    
        except Exception as e:
            logger.error(f"执行查询失败: {query} - {e}")
            raise
    
    async def execute_transaction(self, operations: List[Dict[str, Any]]) -> bool:
        """
        执行事务操作
        
        Args:
            operations: 操作列表，每个操作包含query和params
            
        Returns:
            是否执行成功
        """
        try:
            async with self.get_connection() as conn:
                for op in operations:
                    await conn.execute(op['query'], op.get('params', ()))
                await conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"事务执行失败: {e}")
            return False
    
    async def save_message(self, message_data: Dict[str, Any]) -> bool:
        """
        保存消息到数据库
        
        Args:
            message_data: 消息数据
            
        Returns:
            是否保存成功
        """
        try:
            query = '''
                INSERT INTO messages (
                    chat_id, user_id, item_id, role, content, timestamp, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            '''
            params = (
                message_data['chat_id'],
                message_data['user_id'],
                message_data['item_id'],
                message_data['role'],
                message_data['content'],
                message_data['timestamp'],
                message_data['created_at']
            )
            
            await self.execute_query(query, params)
            return True
            
        except Exception as e:
            logger.error(f"保存消息失败: {e}")
            return False
    
    async def get_messages_by_chat(self, chat_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        根据会话ID获取消息
        
        Args:
            chat_id: 会话ID
            limit: 消息数量限制
            
        Returns:
            消息列表
        """
        query = '''
            SELECT * FROM messages 
            WHERE chat_id = ? 
            ORDER BY timestamp ASC 
            LIMIT ?
        '''
        return await self.execute_query(query, (chat_id, limit), fetch_all=True) or []
    
    async def save_item(self, item_data: Dict[str, Any]) -> bool:
        """
        保存商品信息
        
        Args:
            item_data: 商品数据
            
        Returns:
            是否保存成功
        """
        try:
            query = '''
                INSERT OR REPLACE INTO items (
                    item_id, title, description, price, seller_id, seller_name,
                    category, condition, location, images, raw_data, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            params = (
                item_data['item_id'],
                item_data['title'],
                item_data['description'],
                item_data['price'],
                item_data['seller_id'],
                item_data['seller_name'],
                item_data['category'],
                item_data['condition'],
                item_data['location'],
                json.dumps(item_data['images']),
                json.dumps(item_data['raw_data']),
                item_data['created_at'],
                item_data['updated_at']
            )
            
            await self.execute_query(query, params)
            return True
            
        except Exception as e:
            logger.error(f"保存商品信息失败: {e}")
            return False
    
    async def get_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        获取商品信息
        
        Args:
            item_id: 商品ID
            
        Returns:
            商品信息
        """
        query = "SELECT * FROM items WHERE item_id = ?"
        result = await self.execute_query(query, (item_id,), fetch_one=True)
        
        if result:
            # 反序列化JSON字段
            result['images'] = json.loads(result['images'])
            result['raw_data'] = json.loads(result['raw_data'])
        
        return result
    
    async def save_bargain(self, bargain_data: Dict[str, Any]) -> bool:
        """
        保存议价信息
        
        Args:
            bargain_data: 议价数据
            
        Returns:
            是否保存成功
        """
        try:
            query = '''
                INSERT OR REPLACE INTO bargains (
                    chat_id, item_id, user_id, count, last_bargain_time,
                    last_bargain_content, target_price, negotiation_history,
                    status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            params = (
                bargain_data['chat_id'],
                bargain_data['item_id'],
                bargain_data['user_id'],
                bargain_data['count'],
                bargain_data['last_bargain_time'],
                bargain_data['last_bargain_content'],
                bargain_data['target_price'],
                json.dumps(bargain_data['negotiation_history']),
                bargain_data['status'],
                bargain_data['created_at'],
                bargain_data['updated_at']
            )
            
            await self.execute_query(query, params)
            return True
            
        except Exception as e:
            logger.error(f"保存议价信息失败: {e}")
            return False
    
    async def get_bargain(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """
        获取议价信息
        
        Args:
            chat_id: 会话ID
            
        Returns:
            议价信息
        """
        query = "SELECT * FROM bargains WHERE chat_id = ?"
        result = await self.execute_query(query, (chat_id,), fetch_one=True)
        
        if result:
            # 反序列化JSON字段
            result['negotiation_history'] = json.loads(result['negotiation_history'])
        
        return result
    
    async def save_session(self, session_data: Dict[str, Any]) -> bool:
        """
        保存会话信息
        
        Args:
            session_data: 会话数据
            
        Returns:
            是否保存成功
        """
        try:
            query = '''
                INSERT OR REPLACE INTO sessions (
                    chat_id, user_id, item_id, mode, status, start_time,
                    last_activity, message_count, manual_interventions,
                    ai_responses, metadata, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            params = (
                session_data['chat_id'],
                session_data['user_id'],
                session_data['item_id'],
                session_data['mode'],
                session_data['status'],
                session_data['start_time'],
                session_data['last_activity'],
                session_data['message_count'],
                session_data['manual_interventions'],
                session_data['ai_responses'],
                json.dumps(session_data['metadata']),
                session_data['created_at'],
                session_data['updated_at']
            )
            
            await self.execute_query(query, params)
            return True
            
        except Exception as e:
            logger.error(f"保存会话信息失败: {e}")
            return False
    
    async def get_session(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """
        获取会话信息
        
        Args:
            chat_id: 会话ID
            
        Returns:
            会话信息
        """
        query = "SELECT * FROM sessions WHERE chat_id = ?"
        result = await self.execute_query(query, (chat_id,), fetch_one=True)
        
        if result:
            # 反序列化JSON字段
            result['metadata'] = json.loads(result['metadata'])
        
        return result
    
    async def cleanup_old_data(self, days: int = 30) -> int:
        """
        清理旧数据
        
        Args:
            days: 保留天数
            
        Returns:
            清理的记录数
        """
        try:
            cutoff_time = datetime.now().timestamp() - (days * 24 * 3600)
            
            operations = [
                {
                    'query': 'DELETE FROM messages WHERE timestamp < ?',
                    'params': (cutoff_time,)
                },
                {
                    'query': 'DELETE FROM sessions WHERE last_activity < ?',
                    'params': (cutoff_time,)
                }
            ]
            
            await self.execute_transaction(operations)
            logger.info(f"清理了超过{days}天的旧数据")
            return True
            
        except Exception as e:
            logger.error(f"清理旧数据失败: {e}")
            return 0
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        获取数据库统计信息
        
        Returns:
            统计信息字典
        """
        try:
            stats = {}
            
            # 获取各表记录数
            tables = ['messages', 'items', 'bargains', 'sessions']
            for table in tables:
                query = f"SELECT COUNT(*) as count FROM {table}"
                result = await self.execute_query(query, fetch_one=True)
                stats[f"{table}_count"] = result['count'] if result else 0
            
            # 获取数据库文件大小
            if os.path.exists(self.db_path):
                stats['db_size_bytes'] = os.path.getsize(self.db_path)
                stats['db_size_mb'] = round(stats['db_size_bytes'] / 1024 / 1024, 2)
            
            stats['connection_count'] = self._connection_count
            stats['initialized'] = self._initialized
            
            return stats
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}
    
    def get_health_info(self) -> Dict[str, Any]:
        """
        获取健康状态信息
        
        Returns:
            健康状态字典
        """
        return {
            "status": "healthy" if self._initialized else "initializing",
            "db_path": self.db_path,
            "connection_count": self._connection_count,
            "max_connections": self._max_connections,
            "db_exists": os.path.exists(self.db_path)
        }
    
    async def close(self):
        """关闭数据库管理器"""
        try:
            self._initialized = False
            logger.info("数据库管理器已关闭")
        except Exception as e:
            logger.error(f"关闭数据库管理器失败: {e}") 