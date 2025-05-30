"""
闲鱼API客户端模块
负责所有闲鱼相关的API调用，包括认证、商品信息获取、Token管理等
"""

import time
import json
import sys
import os
import re
from typing import Dict, Any, Optional, Tuple
import requests
from config.logger_config import get_logger
from config.settings import get_config
from utils.crypto_utils import generate_sign
from utils.device_utils import trans_cookies, generate_device_id
from utils.constants import (
    API_APP_KEY, API_MAGIC_NUMBER, API_REQUEST_TIMEOUT, API_RETRY_TIMES,
    DEFAULT_USER_AGENT
)

# 获取专用日志记录器
logger = get_logger("api", "xianyu")


class XianyuAPIClient:
    """
    闲鱼API客户端
    统一管理闲鱼平台的所有API交互，包括认证、商品查询、Token管理等
    """
    
    def __init__(self):
        """初始化闲鱼API客户端"""
        self.config = get_config()
        self.xianyu_config = self.config.get_xianyu_config()
        
        # API基础URLs
        self.token_api_url = 'https://h5api.m.goofish.com/h5/mtop.taobao.idlemessage.pc.login.token/1.0/'
        self.login_check_url = 'https://passport.goofish.com/newlogin/hasLogin.do'
        self.item_detail_url = 'https://h5api.m.goofish.com/h5/mtop.taobao.idle.pc.detail/1.0/'
        
        # 初始化HTTP会话
        self.session = requests.Session()
        self._setup_session()
        
        # 用户信息
        self.cookies_str = self.xianyu_config['cookies_str']
        self.cookies = trans_cookies(self.cookies_str)
        self.session.cookies.update(self.cookies)
        self.user_id = self.cookies.get('unb', '')
        self.device_id = generate_device_id(self.user_id)
        
        # Token管理
        self.current_token = None
        self.last_token_refresh_time = 0
        self.token_refresh_interval = self.xianyu_config['token_refresh_interval']
        self.token_retry_interval = self.xianyu_config['token_retry_interval']
        
        logger.info(f"闲鱼API客户端初始化完成，用户ID: {self.user_id}")
    
    def _setup_session(self):
        """设置HTTP会话的默认配置"""
        self.session.headers.update({
            'accept': 'application/json',
            'accept-language': 'zh-CN,zh;q=0.9',
            'cache-control': 'no-cache',
            'origin': 'https://www.goofish.com',
            'pragma': 'no-cache',
            'priority': 'u=1, i',
            'referer': 'https://www.goofish.com/',
            'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': DEFAULT_USER_AGENT,
        })
        
        # 设置默认超时
        self.session.timeout = API_REQUEST_TIMEOUT
    
    def clear_duplicate_cookies(self):
        """
        清理重复的cookies
        确保每个cookie名称只保留最新的值
        """
        try:
            # 创建新的CookieJar
            new_jar = requests.cookies.RequestsCookieJar()
            added_cookies = set()
            
            # 按照cookies列表的逆序遍历（最新的通常在后面）
            cookie_list = list(self.session.cookies)
            cookie_list.reverse()
            
            for cookie in cookie_list:
                if cookie.name not in added_cookies:
                    new_jar.set_cookie(cookie)
                    added_cookies.add(cookie.name)
            
            # 替换session的cookies
            self.session.cookies = new_jar
            logger.debug(f"清理重复cookies完成，保留 {len(added_cookies)} 个唯一cookies")
            
            # 清理完cookies后，自动更新.env文件
            self.update_env_cookies()
            
        except Exception as e:
            logger.error(f"清理cookies失败: {e}")
    
    def update_env_cookies(self):
        """
        自动更新.env文件中的COOKIES_STR
        将当前session中的cookies同步到环境配置文件中，延长cookie有效期
        """
        try:
            # 获取当前cookies的字符串形式
            cookie_str = '; '.join([f"{cookie.name}={cookie.value}" for cookie in self.session.cookies])
            
            if not cookie_str:
                logger.warning("当前session中没有有效的cookies，跳过.env文件更新")
                return
            
            # 查找.env文件路径（优先级：当前目录 -> 项目根目录）
            possible_paths = [
                os.path.join(os.getcwd(), '.env'),
                os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'),  # 项目根目录
                os.path.join(os.path.expanduser('~'), '.env')  # 用户主目录
            ]
            
            env_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    env_path = path
                    break
            
            if not env_path:
                logger.warning(".env文件不存在于常见路径中，无法自动更新COOKIES_STR")
                return
                
            # 读取.env文件内容
            with open(env_path, 'r', encoding='utf-8') as f:
                env_content = f.read()
                
            # 使用正则表达式替换COOKIES_STR的值
            if 'COOKIES_STR=' in env_content:
                # 处理可能包含特殊字符的cookie值
                escaped_cookie_str = cookie_str.replace('\\', '\\\\').replace('$', '\\$')
                
                new_env_content = re.sub(
                    r'COOKIES_STR=.*?(?=\n|$)', 
                    f'COOKIES_STR={escaped_cookie_str}',
                    env_content,
                    flags=re.MULTILINE
                )
                
                # 写回.env文件
                with open(env_path, 'w', encoding='utf-8') as f:
                    f.write(new_env_content)
                    
                logger.info(f"✅ 已自动更新.env文件中的COOKIES_STR ({len(self.session.cookies)} 个cookies)")
                logger.debug(f"更新的cookies: {cookie_str[:100]}..." if len(cookie_str) > 100 else f"更新的cookies: {cookie_str}")
                
            else:
                # 如果.env文件中没有COOKIES_STR配置项，则追加添加
                if not env_content.endswith('\n'):
                    env_content += '\n'
                env_content += f'COOKIES_STR={cookie_str}\n'
                
                with open(env_path, 'w', encoding='utf-8') as f:
                    f.write(env_content)
                    
                logger.info("✅ 已在.env文件中新增COOKIES_STR配置项")
                
        except FileNotFoundError:
            logger.warning("无法找到.env文件，跳过COOKIES_STR自动更新")
        except PermissionError:
            logger.warning("没有权限写入.env文件，跳过COOKIES_STR自动更新")
        except Exception as e:
            logger.warning(f"自动更新.env文件失败: {str(e)}")
    
    def validate_login_status(self, retry_count: int = 0) -> bool:
        """
        验证登录状态
        
        Args:
            retry_count: 重试次数
            
        Returns:
            登录状态是否有效
        """
        if retry_count >= API_RETRY_TIMES:
            logger.error("登录状态验证失败，重试次数过多")
            return False
        
        try:
            params = {
                'appName': 'xianyu',
                'fromSite': '77'
            }
            
            data = {
                'hid': self.session.cookies.get('unb', ''),
                'ltl': 'true',
                'appName': 'xianyu',
                'appEntrance': 'web',
                '_csrf_token': self.session.cookies.get('XSRF-TOKEN', ''),
                'umidToken': '',
                'hsiz': self.session.cookies.get('cookie2', ''),
                'bizParams': 'taobaoBizLoginFrom=web',
                'mainPage': 'false',
                'isMobile': 'false',
                'lang': 'zh_CN',
                'returnUrl': '',
                'fromSite': '77',
                'isIframe': 'true',
                'documentReferer': 'https://www.goofish.com/',
                'defaultView': 'hasLogin',
                'umidTag': 'SERVER',
                'deviceId': self.session.cookies.get('cna', '')
            }
            
            response = self.session.post(self.login_check_url, params=params, data=data)
            response.raise_for_status()
            
            res_json = response.json()
            
            if res_json.get('content', {}).get('success'):
                logger.debug("登录状态验证成功")
                self.clear_duplicate_cookies()
                return True
            else:
                logger.warning(f"登录状态验证失败: {res_json}")
                time.sleep(0.5)
                return self.validate_login_status(retry_count + 1)
                
        except Exception as e:
            logger.error(f"登录状态验证异常: {e}")
            time.sleep(0.5)
            return self.validate_login_status(retry_count + 1)
    
    def get_token(self, retry_count: int = 0) -> Optional[Dict[str, Any]]:
        """
        获取访问令牌
        
        Args:
            retry_count: 重试次数
            
        Returns:
            包含token信息的字典，失败返回None
        """
        if retry_count >= API_RETRY_TIMES:
            logger.warning("获取token失败，尝试重新登录")
            
            # 尝试通过登录状态验证重新登录
            if self.validate_login_status():
                logger.info("重新登录成功，重新尝试获取token")
                return self.get_token(0)  # 重置重试次数
            else:
                logger.error("重新登录失败，Cookie已失效")
                logger.error("🔴 程序即将退出，请更新.env文件中的COOKIES_STR后重新启动")
                sys.exit(1)
        
        try:
            # 准备请求参数
            timestamp = str(int(time.time()) * 1000)
            data_val = json.dumps({
                "appKey": API_APP_KEY,
                "deviceId": self.device_id
            }, separators=(',', ':'))
            
            # 获取当前token用于签名
            current_token = self.session.cookies.get('_m_h5_tk', '').split('_')[0]
            
            # 生成签名
            sign = generate_sign(timestamp, current_token, data_val)
            
            params = {
                'jsv': '2.7.2',
                'appKey': API_MAGIC_NUMBER,
                't': timestamp,
                'sign': sign,
                'v': '1.0',
                'type': 'originaljson',
                'accountSite': 'xianyu',
                'dataType': 'json',
                'timeout': '20000',
                'api': 'mtop.taobao.idlemessage.pc.login.token',
                'sessionOption': 'AutoLoginOnly',
                'spm_cnt': 'a21ybx.im.0.0',
            }
            
            data = {'data': data_val}
            
            response = self.session.post(self.token_api_url, params=params, data=data)
            response.raise_for_status()
            
            res_json = response.json()
            
            if isinstance(res_json, dict):
                ret_value = res_json.get('ret', [])
                
                # 检查API调用是否成功
                if not any('SUCCESS::调用成功' in ret for ret in ret_value):
                    logger.warning(f"Token API调用失败，错误信息: {ret_value}")
                    
                    # 处理响应中的Set-Cookie
                    if 'Set-Cookie' in response.headers:
                        logger.debug("检测到Set-Cookie，更新cookie")
                        self.clear_duplicate_cookies()
                    
                    time.sleep(0.5)
                    return self.get_token(retry_count + 1)
                else:
                    logger.info("Token获取成功")
                    self.current_token = res_json.get('data', {}).get('accessToken')
                    self.last_token_refresh_time = time.time()
                    return res_json
            else:
                logger.error(f"Token API返回格式异常: {res_json}")
                return self.get_token(retry_count + 1)
                
        except Exception as e:
            logger.error(f"Token API请求异常: {e}")
            time.sleep(0.5)
            return self.get_token(retry_count + 1)
    
    def get_item_info(self, item_id: str, retry_count: int = 0) -> Optional[Dict[str, Any]]:
        """
        获取商品信息
        
        Args:
            item_id: 商品ID
            retry_count: 重试次数
            
        Returns:
            商品信息字典，失败返回None
        """
        if retry_count >= API_RETRY_TIMES:
            logger.error(f"获取商品信息失败，商品ID: {item_id}，重试次数过多")
            return {"error": f"获取商品信息失败，商品ID: {item_id}"}
        
        try:
            # 准备请求参数
            timestamp = str(int(time.time()) * 1000)
            data_val = json.dumps({"itemId": item_id}, separators=(',', ':'))
            
            # 获取当前token用于签名
            current_token = self.session.cookies.get('_m_h5_tk', '').split('_')[0]
            
            # 生成签名
            sign = generate_sign(timestamp, current_token, data_val)
            
            params = {
                'jsv': '2.7.2',
                'appKey': API_MAGIC_NUMBER,
                't': timestamp,
                'sign': sign,
                'v': '1.0',
                'type': 'originaljson',
                'accountSite': 'xianyu',
                'dataType': 'json',
                'timeout': '20000',
                'api': 'mtop.taobao.idle.pc.detail',
                'sessionOption': 'AutoLoginOnly',
                'spm_cnt': 'a21ybx.im.0.0',
            }
            
            data = {'data': data_val}
            
            response = self.session.post(self.item_detail_url, params=params, data=data)
            response.raise_for_status()
            
            res_json = response.json()
            
            if isinstance(res_json, dict):
                ret_value = res_json.get('ret', [])
                
                # 检查API调用是否成功
                if not any('SUCCESS::调用成功' in ret for ret in ret_value):
                    logger.warning(f"商品信息API调用失败，商品ID: {item_id}，错误信息: {ret_value}")
                    
                    # 处理响应中的Set-Cookie
                    if 'Set-Cookie' in response.headers:
                        logger.debug("检测到Set-Cookie，更新cookie")
                        self.clear_duplicate_cookies()
                    
                    time.sleep(0.5)
                    return self.get_item_info(item_id, retry_count + 1)
                else:
                    logger.debug(f"商品信息获取成功: {item_id}")
                    return res_json
            else:
                logger.error(f"商品信息API返回格式异常，商品ID: {item_id}: {res_json}")
                return self.get_item_info(item_id, retry_count + 1)
                
        except Exception as e:
            logger.error(f"商品信息API请求异常，商品ID: {item_id}: {e}")
            time.sleep(0.5)
            return self.get_item_info(item_id, retry_count + 1)
    
    def is_token_expired(self) -> bool:
        """
        检查token是否过期
        
        Returns:
            token是否过期
        """
        if not self.current_token:
            return True
        
        current_time = time.time()
        return (current_time - self.last_token_refresh_time) >= self.token_refresh_interval
    
    def refresh_token(self) -> bool:
        """
        刷新token
        
        Returns:
            刷新是否成功
        """
        try:
            logger.info("开始刷新token...")
            token_result = self.get_token()
            
            if token_result and 'data' in token_result and 'accessToken' in token_result['data']:
                self.current_token = token_result['data']['accessToken']
                self.last_token_refresh_time = time.time()
                logger.info("Token刷新成功")
                return True
            else:
                logger.error(f"Token刷新失败: {token_result}")
                return False
                
        except Exception as e:
            logger.error(f"Token刷新异常: {e}")
            return False
    
    def get_current_token(self) -> Optional[str]:
        """
        获取当前有效的token
        
        Returns:
            当前token，如果过期则自动刷新
        """
        if self.is_token_expired():
            if self.refresh_token():
                return self.current_token
            else:
                return None
        
        return self.current_token
    
    def get_user_info(self) -> Dict[str, Any]:
        """
        获取当前用户信息
        
        Returns:
            用户信息字典
        """
        return {
            "user_id": self.user_id,
            "device_id": self.device_id,
            "token_status": "valid" if not self.is_token_expired() else "expired",
            "last_token_refresh": self.last_token_refresh_time
        }
    
    def get_api_statistics(self) -> Dict[str, Any]:
        """
        获取API使用统计信息
        
        Returns:
            API统计信息
        """
        return {
            "base_urls": {
                "token_api": self.token_api_url,
                "login_check": self.login_check_url,
                "item_detail": self.item_detail_url
            },
            "current_session": {
                "cookies_count": len(self.session.cookies),
                "user_id": self.user_id,
                "device_id": self.device_id
            },
            "token_info": {
                "current_token": bool(self.current_token),
                "last_refresh_time": self.last_token_refresh_time,
                "is_expired": self.is_token_expired()
            }
        }
    
    def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            健康状态信息
        """
        health = {
            "status": "healthy",
            "checks": {
                "cookies_loaded": bool(self.cookies),
                "user_id_valid": bool(self.user_id),
                "device_id_generated": bool(self.device_id),
                "session_initialized": bool(self.session),
                "token_available": bool(self.current_token and not self.is_token_expired())
            },
            "issues": []
        }
        
        # 检查各项状态
        if not health["checks"]["cookies_loaded"]:
            health["issues"].append("Cookies未正确加载")
        
        if not health["checks"]["user_id_valid"]:
            health["issues"].append("用户ID无效")
        
        if not health["checks"]["token_available"]:
            health["issues"].append("Token不可用或已过期")
        
        # 如果有问题，更新整体状态
        if health["issues"]:
            health["status"] = "degraded" if len(health["issues"]) <= 2 else "unhealthy"
        
        return health
    
    def __del__(self):
        """析构函数，清理资源"""
        if hasattr(self, 'session'):
            self.session.close() 