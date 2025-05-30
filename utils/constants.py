"""
项目常量定义模块
集中管理项目中使用的所有常量，便于维护和配置
"""

# WebSocket连接相关常量
WEBSOCKET_BASE_URL = 'wss://wss-goofish.dingtalk.com/'
WEBSOCKET_TIMEOUT = 30  # WebSocket连接超时时间（秒）
WEBSOCKET_PING_INTERVAL = 20  # WebSocket心跳间隔（秒）

# API相关常量
API_APP_KEY = "444e9908a51d1cb236a27862abc769c9"
API_MAGIC_NUMBER = "34839810"  # 签名生成中使用的魔数
API_REQUEST_TIMEOUT = 30  # API请求超时时间（秒）
API_RETRY_TIMES = 3  # API请求重试次数

# 用户代理常量
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 DingTalk(2.1.5) OS(Windows/10) Browser(Chrome/133.0.0.0) DingWeb/2.1.5 IMPaaS DingWeb/2.1.5"

# 日志相关常量
LOG_ROTATION_SIZE = "10 MB"  # 日志文件轮转大小
LOG_RETENTION_DAYS = "10 days"  # 日志保留天数
LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}"

# 时间相关常量
HEARTBEAT_INTERVAL_DEFAULT = 15  # 默认心跳间隔（秒）
HEARTBEAT_TIMEOUT_DEFAULT = 5  # 默认心跳超时（秒）
TOKEN_REFRESH_INTERVAL_DEFAULT = 3600  # 默认Token刷新间隔（秒）
TOKEN_RETRY_INTERVAL_DEFAULT = 300  # 默认Token重试间隔（秒）
MANUAL_MODE_TIMEOUT_DEFAULT = 3600  # 默认人工模式超时（秒）
MESSAGE_EXPIRE_TIME_DEFAULT = 300000  # 默认消息过期时间（毫秒）

# 会话相关常量
SESSION_LIFETIME_HOURS = 24  # Web UI会话生命周期（小时）
MAX_CONTEXT_LENGTH = 1000  # 对话上下文最大长度

# AI相关常量
DEFAULT_MODEL_NAME = "qwen-plus"
DEFAULT_MODEL_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
MAX_TOKENS_DEFAULT = 2000  # 默认最大token数量
TEMPERATURE_DEFAULT = 0.7  # 默认温度参数

# 安全相关常量
BLOCKED_PHRASES = ["微信", "QQ", "支付宝", "银行卡", "线下"]  # 安全过滤的敏感词
SECURITY_WARNING_MESSAGE = "[安全提醒]请通过平台沟通"

# 文件路径常量
PROMPTS_DIR = "config/prompts"
LOGS_DIR = "logs"
DATA_DIR = "data"
STATIC_DIR = "web/static"
TEMPLATES_DIR = "web/templates"

# 提示词文件名常量
CLASSIFY_PROMPT_FILE = "classify_prompt.txt"
PRICE_PROMPT_FILE = "price_prompt.txt"
TECH_PROMPT_FILE = "tech_prompt.txt"
DEFAULT_PROMPT_FILE = "default_prompt.txt"

# 数据库相关常量
DATABASE_FILE = "data/chat_history.db"
DATABASE_TIMEOUT = 30  # 数据库连接超时（秒）

# HTTP状态码常量
HTTP_OK = 200
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_INTERNAL_ERROR = 500

# Agent类型常量
AGENT_CLASSIFY = "classify"
AGENT_PRICE = "price"
AGENT_TECH = "tech"
AGENT_DEFAULT = "default"

# 消息类型常量
MESSAGE_TYPE_TEXT = 1
MESSAGE_TYPE_IMAGE = 2
MESSAGE_TYPE_FILE = 3
MESSAGE_TYPE_SYSTEM = 100

# 对话状态常量
CONVERSATION_STATE_ACTIVE = "active"
CONVERSATION_STATE_MANUAL = "manual"
CONVERSATION_STATE_ENDED = "ended"

# 正则表达式常量
TECH_PATTERNS = [
    r'和.+比',           # 产品对比
    r'\d+参数',          # 参数查询
    r'规格\w+',          # 规格询问
    r'连接\w+',          # 连接方式
]

PRICE_PATTERNS = [
    r'\d+元',            # 价格数字
    r'能少\d+',          # 砍价表达
    r'便宜\d+',          # 便宜多少
    r'最低\d+',          # 最低价格
]

# 错误消息常量
ERROR_MESSAGES = {
    "invalid_token": "Token无效或已过期",
    "connection_failed": "连接失败，请检查网络",
    "decode_failed": "数据解码失败",
    "config_missing": "配置文件缺失或格式错误",
    "permission_denied": "权限不足",
    "rate_limited": "请求频率过高，请稍后重试",
    "service_unavailable": "服务暂时不可用"
}

# 成功消息常量
SUCCESS_MESSAGES = {
    "login_success": "登录成功",
    "connection_established": "连接建立成功",
    "message_sent": "消息发送成功",
    "config_loaded": "配置加载完成",
    "agent_initialized": "AI代理初始化完成",
    "session_created": "会话创建成功"
}

# 调试相关常量
DEBUG_MODE = False  # 是否启用调试模式
VERBOSE_LOGGING = False  # 是否启用详细日志

# 性能相关常量
MAX_CONCURRENT_CONNECTIONS = 10  # 最大并发连接数
BUFFER_SIZE = 8192  # 缓冲区大小
CACHE_TTL = 300  # 缓存生存时间（秒）

# 特殊字符常量
MANUAL_MODE_TOGGLE_DEFAULT = "。"  # 人工模式切换默认关键词
CONVERSATION_SEPARATOR = "\n---\n"  # 对话分隔符
SYSTEM_MESSAGE_PREFIX = "[系统]"  # 系统消息前缀

# 文件扩展名常量
ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
ALLOWED_DOCUMENT_EXTENSIONS = ['.txt', '.pdf', '.doc', '.docx']

# 版本信息常量
PROJECT_VERSION = "2.0.0"
PROJECT_NAME = "XianyuAutoAgent"
PROJECT_DESCRIPTION = "智能闲鱼客服机器人系统" 