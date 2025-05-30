"""
配置管理模块
统一管理项目的所有配置信息，包括环境变量、提示词、Web UI配置等
"""

import os
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from loguru import logger


class ConfigManager:
    """配置管理器 - 统一管理项目配置"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """单例模式确保全局唯一的配置管理器"""
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化配置管理器"""
        if not self._initialized:
            self._load_env_config()
            self._load_web_ui_config()
            self._load_prompts()
            self._initialized = True
            logger.info("配置管理器初始化完成")
    
    def _load_env_config(self):
        """加载环境变量配置"""
        load_dotenv()
        
        # 必需的配置项
        self.api_key = os.getenv("API_KEY")
        self.cookies_str = os.getenv("COOKIES_STR")
        self.model_base_url = os.getenv("MODEL_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        self.model_name = os.getenv("MODEL_NAME", "qwen-plus")
        
        # 可选配置项
        self.toggle_keywords = os.getenv("TOGGLE_KEYWORDS", "。")
        self.heartbeat_interval = int(os.getenv("HEARTBEAT_INTERVAL", "15"))
        self.heartbeat_timeout = int(os.getenv("HEARTBEAT_TIMEOUT", "5"))
        self.token_refresh_interval = int(os.getenv("TOKEN_REFRESH_INTERVAL", "3600"))
        self.token_retry_interval = int(os.getenv("TOKEN_RETRY_INTERVAL", "300"))
        self.manual_mode_timeout = int(os.getenv("MANUAL_MODE_TIMEOUT", "3600"))
        self.message_expire_time = int(os.getenv("MESSAGE_EXPIRE_TIME", "300000"))
        
        # 验证必需配置
        if not self.api_key:
            logger.error("API_KEY 未配置，请检查.env文件")
            raise ValueError("API_KEY is required")
        
        if not self.cookies_str:
            logger.error("COOKIES_STR 未配置，请检查.env文件")
            raise ValueError("COOKIES_STR is required")
            
        logger.info("环境变量配置加载完成")
    
    def _load_web_ui_config(self):
        """加载Web UI配置"""
        config_file = "web_ui_config.json"
        default_config = {
            "auth": {
                "username": "admin",
                "password": "admin123",
                "secret_key": "xianyu_auto_agent_secret_key_change_this_in_production"
            },
            "session": {
                "permanent_session_lifetime_hours": 24
            }
        }
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    self.web_ui_config = json.load(f)
                logger.info(f"已加载Web UI配置文件: {config_file}")
            else:
                # 创建默认配置文件
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=4, ensure_ascii=False)
                self.web_ui_config = default_config
                logger.info(f"已创建默认Web UI配置文件: {config_file}")
        except Exception as e:
            logger.error(f"加载Web UI配置失败，使用默认配置: {e}")
            self.web_ui_config = default_config
    
    def _load_prompts(self):
        """加载所有提示词文件"""
        prompt_dir = "config/prompts"
        self.prompts = {}
        
        prompt_files = {
            'classify': 'classify_prompt.txt',
            'price': 'price_prompt.txt', 
            'tech': 'tech_prompt.txt',
            'default': 'default_prompt.txt'
        }
        
        for prompt_type, filename in prompt_files.items():
            file_path = os.path.join(prompt_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.prompts[prompt_type] = f.read()
                logger.debug(f"已加载{prompt_type}提示词，长度: {len(self.prompts[prompt_type])} 字符")
            except Exception as e:
                logger.error(f"加载提示词文件 {filename} 失败: {e}")
                self.prompts[prompt_type] = ""
        
        logger.info("提示词配置加载完成")
    
    def get_prompt(self, prompt_type: str) -> str:
        """获取指定类型的提示词"""
        return self.prompts.get(prompt_type, "")
    
    def reload_prompts(self):
        """重新加载提示词"""
        logger.info("正在重新加载提示词...")
        self._load_prompts()
        logger.info("提示词重新加载完成")
    
    def get_web_ui_auth(self) -> Dict[str, str]:
        """获取Web UI认证配置"""
        return self.web_ui_config.get('auth', {})
    
    def get_web_ui_session_config(self) -> Dict[str, Any]:
        """获取Web UI会话配置"""
        return self.web_ui_config.get('session', {})
    
    def get_openai_config(self) -> Dict[str, str]:
        """获取OpenAI客户端配置"""
        return {
            'api_key': self.api_key,
            'base_url': self.model_base_url,
            'model_name': self.model_name
        }
    
    def get_xianyu_config(self) -> Dict[str, Any]:
        """获取闲鱼相关配置"""
        return {
            'cookies_str': self.cookies_str,
            'toggle_keywords': self.toggle_keywords,
            'heartbeat_interval': self.heartbeat_interval,
            'heartbeat_timeout': self.heartbeat_timeout,
            'token_refresh_interval': self.token_refresh_interval,
            'token_retry_interval': self.token_retry_interval,
            'manual_mode_timeout': self.manual_mode_timeout,
            'message_expire_time': self.message_expire_time
        }


# 全局配置管理器实例
config_manager = ConfigManager()


def get_config() -> ConfigManager:
    """获取全局配置管理器实例"""
    return config_manager 