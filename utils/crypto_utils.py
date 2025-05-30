"""
加密解密工具模块
提供签名生成、MessagePack解码、数据解密等加密相关功能
"""

import json
import hashlib
import base64
import struct
from typing import Any, Dict
from config.logger_config import get_logger

# 获取专用日志记录器
logger = get_logger("utils", "crypto")


def generate_sign(t: str, token: str, data: str) -> str:
    """
    生成API请求签名
    
    Args:
        t: 时间戳字符串
        token: 访问令牌
        data: 请求数据
        
    Returns:
        MD5签名字符串
    """
    # 构造待签名字符串
    msg = f'{token}&{t}&34839810&{data}'
    
    # 计算MD5哈希
    md5_hash = hashlib.md5()
    md5_hash.update(msg.encode('utf-8'))
    signature = md5_hash.hexdigest()
    
    logger.debug(f"生成签名 - 时间戳: {t}, 数据长度: {len(data)}, 签名: {signature[:8]}...")
    return signature


class MessagePackDecoder:
    """
    MessagePack解码器的自主实现
    无需外部依赖，支持完整的MessagePack格式解码
    """
    
    def __init__(self, data: bytes):
        """
        初始化解码器
        
        Args:
            data: 待解码的字节数据
        """
        self.data = data
        self.pos = 0
        self.length = len(data)
        logger.debug(f"初始化MessagePack解码器，数据长度: {self.length} 字节")
    
    def read_byte(self) -> int:
        """读取单个字节"""
        if self.pos >= self.length:
            raise ValueError("数据意外结束")
        byte = self.data[self.pos]
        self.pos += 1
        return byte
    
    def read_bytes(self, count: int) -> bytes:
        """读取指定数量的字节"""
        if self.pos + count > self.length:
            raise ValueError("数据意外结束")
        result = self.data[self.pos:self.pos + count]
        self.pos += count
        return result
    
    def read_uint8(self) -> int:
        """读取8位无符号整数"""
        return self.read_byte()
    
    def read_uint16(self) -> int:
        """读取16位无符号整数（大端序）"""
        return struct.unpack('>H', self.read_bytes(2))[0]
    
    def read_uint32(self) -> int:
        """读取32位无符号整数（大端序）"""
        return struct.unpack('>I', self.read_bytes(4))[0]
    
    def read_uint64(self) -> int:
        """读取64位无符号整数（大端序）"""
        return struct.unpack('>Q', self.read_bytes(8))[0]
    
    def read_int8(self) -> int:
        """读取8位有符号整数"""
        return struct.unpack('>b', self.read_bytes(1))[0]
    
    def read_int16(self) -> int:
        """读取16位有符号整数（大端序）"""
        return struct.unpack('>h', self.read_bytes(2))[0]
    
    def read_int32(self) -> int:
        """读取32位有符号整数（大端序）"""
        return struct.unpack('>i', self.read_bytes(4))[0]
    
    def read_int64(self) -> int:
        """读取64位有符号整数（大端序）"""
        return struct.unpack('>q', self.read_bytes(8))[0]
    
    def read_float32(self) -> float:
        """读取32位浮点数（大端序）"""
        return struct.unpack('>f', self.read_bytes(4))[0]
    
    def read_float64(self) -> float:
        """读取64位浮点数（大端序）"""
        return struct.unpack('>d', self.read_bytes(8))[0]
    
    def read_string(self, length: int) -> str:
        """读取指定长度的UTF-8字符串"""
        return self.read_bytes(length).decode('utf-8')
    
    def read_binary(self, length: int) -> bytes:
        """读取指定长度的二进制数据"""
        return self.read_bytes(length)
    
    def decode_value(self) -> Any:
        """
        解码单个MessagePack值
        
        Returns:
            解码后的Python对象
        """
        if self.pos >= self.length:
            raise ValueError("数据意外结束")
        
        first_byte = self.read_byte()
        
        # Positive fixint (0x00 - 0x7f)
        if first_byte <= 0x7f:
            return first_byte
        
        # Fixmap (0x80 - 0x8f)
        elif 0x80 <= first_byte <= 0x8f:
            size = first_byte & 0x0f
            return self.decode_map(size)
        
        # Fixarray (0x90 - 0x9f)
        elif 0x90 <= first_byte <= 0x9f:
            size = first_byte & 0x0f
            return self.decode_array(size)
        
        # Fixstr (0xa0 - 0xbf)
        elif 0xa0 <= first_byte <= 0xbf:
            size = first_byte & 0x1f
            return self.read_string(size)
        
        # nil
        elif first_byte == 0xc0:
            return None
        
        # false
        elif first_byte == 0xc2:
            return False
        
        # true
        elif first_byte == 0xc3:
            return True
        
        # bin 8
        elif first_byte == 0xc4:
            size = self.read_uint8()
            return self.read_binary(size)
        
        # bin 16
        elif first_byte == 0xc5:
            size = self.read_uint16()
            return self.read_binary(size)
        
        # bin 32
        elif first_byte == 0xc6:
            size = self.read_uint32()
            return self.read_binary(size)
        
        # float 32
        elif first_byte == 0xca:
            return self.read_float32()
        
        # float 64
        elif first_byte == 0xcb:
            return self.read_float64()
        
        # uint 8
        elif first_byte == 0xcc:
            return self.read_uint8()
        
        # uint 16
        elif first_byte == 0xcd:
            return self.read_uint16()
        
        # uint 32
        elif first_byte == 0xce:
            return self.read_uint32()
        
        # uint 64
        elif first_byte == 0xcf:
            return self.read_uint64()
        
        # int 8
        elif first_byte == 0xd0:
            return self.read_int8()
        
        # int 16
        elif first_byte == 0xd1:
            return self.read_int16()
        
        # int 32
        elif first_byte == 0xd2:
            return self.read_int32()
        
        # int 64
        elif first_byte == 0xd3:
            return self.read_int64()
        
        # str 8
        elif first_byte == 0xd9:
            size = self.read_uint8()
            return self.read_string(size)
        
        # str 16
        elif first_byte == 0xda:
            size = self.read_uint16()
            return self.read_string(size)
        
        # str 32
        elif first_byte == 0xdb:
            size = self.read_uint32()
            return self.read_string(size)
        
        # array 16
        elif first_byte == 0xdc:
            size = self.read_uint16()
            return self.decode_array(size)
        
        # array 32
        elif first_byte == 0xdd:
            size = self.read_uint32()
            return self.decode_array(size)
        
        # map 16
        elif first_byte == 0xde:
            size = self.read_uint16()
            return self.decode_map(size)
        
        # map 32
        elif first_byte == 0xdf:
            size = self.read_uint32()
            return self.decode_map(size)
        
        # Negative fixint (0xe0 - 0xff)
        elif 0xe0 <= first_byte <= 0xff:
            return struct.unpack('b', bytes([first_byte]))[0]
        
        else:
            raise ValueError(f"未知的MessagePack类型: 0x{first_byte:02x}")
    
    def decode_array(self, size: int) -> list:
        """
        解码数组
        
        Args:
            size: 数组大小
            
        Returns:
            解码后的Python列表
        """
        result = []
        for _ in range(size):
            result.append(self.decode_value())
        return result
    
    def decode_map(self, size: int) -> dict:
        """
        解码映射/字典
        
        Args:
            size: 映射大小
            
        Returns:
            解码后的Python字典
        """
        result = {}
        for _ in range(size):
            key = self.decode_value()
            value = self.decode_value()
            # 确保key是字符串类型（对于字典）
            if isinstance(key, bytes):
                key = key.decode('utf-8')
            result[key] = value
        return result
    
    def decode(self) -> Any:
        """
        解码MessagePack数据的主入口
        
        Returns:
            解码后的Python对象
        """
        try:
            self.pos = 0  # 重置位置
            result = self.decode_value()
            logger.debug(f"MessagePack解码成功，结果类型: {type(result)}")
            return result
        except Exception as e:
            logger.warning(f"MessagePack解码失败: {e}，返回base64编码")
            # 如果自主解码失败，返回原始数据的base64编码
            return base64.b64encode(self.data).decode('utf-8')


def decrypt(data: str) -> str:
    """
    解密闲鱼消息数据
    支持Base64解码、MessagePack解码和JSON序列化
    
    Args:
        data: 待解密的数据字符串
        
    Returns:
        解密后的JSON字符串
    """
    try:
        logger.debug(f"开始解密数据，长度: {len(data)} 字符")
        
        # 1. Base64解码
        # 清理非base64字符
        cleaned_data = ''.join(c for c in data if c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=')
        
        # 添加padding如果需要
        while len(cleaned_data) % 4 != 0:
            cleaned_data += '='
        
        try:
            decoded_bytes = base64.b64decode(cleaned_data)
            logger.debug(f"Base64解码成功，得到 {len(decoded_bytes)} 字节")
        except Exception as e:
            # 如果base64解码失败，尝试其他方法
            logger.error(f"Base64解码失败: {e}")
            return json.dumps({"error": f"Base64解码失败: {str(e)}", "raw_data": data}, ensure_ascii=False)
        
        # 2. 尝试MessagePack解码
        try:
            decoder = MessagePackDecoder(decoded_bytes)
            result = decoder.decode()
            
            # 3. 转换为JSON字符串
            def json_serializer(obj):
                """自定义JSON序列化器，处理特殊对象类型"""
                if isinstance(obj, bytes):
                    try:
                        return obj.decode('utf-8')
                    except:
                        return base64.b64encode(obj).decode('utf-8')
                elif hasattr(obj, '__dict__'):
                    return obj.__dict__
                else:
                    return str(obj)
            
            json_result = json.dumps(result, ensure_ascii=False, default=json_serializer)
            logger.debug("数据解密成功")
            return json_result
            
        except Exception as e:
            logger.warning(f"MessagePack解码失败: {e}，尝试UTF-8解码")
            # 如果MessagePack解码失败，尝试直接解析为字符串
            try:
                text_result = decoded_bytes.decode('utf-8')
                return json.dumps({"text": text_result}, ensure_ascii=False)
            except:
                logger.warning("UTF-8解码失败，返回十六进制表示")
                # 最后的备选方案：返回十六进制表示
                hex_result = decoded_bytes.hex()
                return json.dumps({"hex": hex_result, "error": f"解码失败: {str(e)}"}, ensure_ascii=False)
                
    except Exception as e:
        logger.error(f"数据解密完全失败: {e}")
        return json.dumps({"error": f"解密失败: {str(e)}", "raw_data": data}, ensure_ascii=False) 