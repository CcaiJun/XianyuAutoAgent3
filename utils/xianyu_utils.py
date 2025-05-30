import json
import time
import hashlib
import base64
import struct
from typing import Any, Dict, List


def trans_cookies(cookies_str: str) -> Dict[str, str]:
    """解析cookie字符串为字典"""
    cookies = {}
    for cookie in cookies_str.split("; "):
        try:
            parts = cookie.split('=', 1)
            if len(parts) == 2:
                cookies[parts[0]] = parts[1]
        except:
            continue
    return cookies


def generate_uuid() -> str:
    """生成UUID字符串"""
    import random
    import string
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=32))


def generate_mid() -> str:
    """生成消息ID"""
    import random
    timestamp = str(int(time.time() * 1000))
    random_num = str(random.randint(10000, 99999))
    return timestamp + " " + random_num


def generate_device_id(unb: str) -> str:
    """根据unb生成设备ID"""
    base_string = f"xianyu_device_{unb}_{int(time.time())}"
    hash_object = hashlib.md5(base_string.encode())
    return hash_object.hexdigest()


def generate_sign(t: str, token: str, data: str) -> str:
    """生成签名"""
    # 构造待签名字符串
    msg = f'{token}&{t}&34839810&{data}'
    
    # 计算MD5哈希
    md5_hash = hashlib.md5()
    md5_hash.update(msg.encode('utf-8'))
    return md5_hash.hexdigest()


class MessagePackDecoder:
    """MessagePack解码器的自主实现（无需外部依赖）"""
    
    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0
        self.length = len(data)
    
    def read_byte(self) -> int:
        if self.pos >= self.length:
            raise ValueError("Unexpected end of data")
        byte = self.data[self.pos]
        self.pos += 1
        return byte
    
    def read_bytes(self, count: int) -> bytes:
        if self.pos + count > self.length:
            raise ValueError("Unexpected end of data")
        result = self.data[self.pos:self.pos + count]
        self.pos += count
        return result
    
    def read_uint8(self) -> int:
        return self.read_byte()
    
    def read_uint16(self) -> int:
        return struct.unpack('>H', self.read_bytes(2))[0]
    
    def read_uint32(self) -> int:
        return struct.unpack('>I', self.read_bytes(4))[0]
    
    def read_uint64(self) -> int:
        return struct.unpack('>Q', self.read_bytes(8))[0]
    
    def read_int8(self) -> int:
        return struct.unpack('>b', self.read_bytes(1))[0]
    
    def read_int16(self) -> int:
        return struct.unpack('>h', self.read_bytes(2))[0]
    
    def read_int32(self) -> int:
        return struct.unpack('>i', self.read_bytes(4))[0]
    
    def read_int64(self) -> int:
        return struct.unpack('>q', self.read_bytes(8))[0]
    
    def read_float32(self) -> float:
        return struct.unpack('>f', self.read_bytes(4))[0]
    
    def read_float64(self) -> float:
        return struct.unpack('>d', self.read_bytes(8))[0]
    
    def read_string(self, length: int) -> str:
        return self.read_bytes(length).decode('utf-8')
    
    def read_binary(self, length: int) -> bytes:
        return self.read_bytes(length)
    
    def decode_value(self) -> Any:
        """解码单个MessagePack值"""
        if self.pos >= self.length:
            raise ValueError("Unexpected end of data")
        
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
            raise ValueError(f"Unknown MessagePack type: 0x{first_byte:02x}")
    
    def decode_array(self, size: int) -> list:
        """解码数组"""
        result = []
        for _ in range(size):
            result.append(self.decode_value())
        return result
    
    def decode_map(self, size: int) -> dict:
        """解码映射/字典"""
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
        """解码MessagePack数据"""
        try:
            self.pos = 0  # 重置位置
            return self.decode_value()
        except Exception as e:
            # 如果自主解码失败，返回原始数据的base64编码
            return base64.b64encode(self.data).decode('utf-8')


def decrypt(data: str) -> str:
    """解密函数的Python实现"""
    try:
        # 1. Base64解码
        # 清理非base64字符
        cleaned_data = ''.join(c for c in data if c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=')
        
        # 添加padding如果需要
        while len(cleaned_data) % 4 != 0:
            cleaned_data += '='
        
        try:
            decoded_bytes = base64.b64decode(cleaned_data)
        except Exception as e:
            # 如果base64解码失败，尝试其他方法
            return json.dumps({"error": f"Base64 decode failed: {str(e)}", "raw_data": data})
        
        # 2. 尝试MessagePack解码
        try:
            decoder = MessagePackDecoder(decoded_bytes)
            result = decoder.decode()
            
            # 3. 转换为JSON字符串
            def json_serializer(obj):
                """自定义JSON序列化器"""
                if isinstance(obj, bytes):
                    try:
                        return obj.decode('utf-8')
                    except:
                        return base64.b64encode(obj).decode('utf-8')
                elif hasattr(obj, '__dict__'):
                    return obj.__dict__
                else:
                    return str(obj)
            
            return json.dumps(result, ensure_ascii=False, default=json_serializer)
            
        except Exception as e:
            # 如果MessagePack解码失败，尝试直接解析为字符串
            try:
                text_result = decoded_bytes.decode('utf-8')
                return json.dumps({"text": text_result})
            except:
                # 最后的备选方案：返回十六进制表示
                hex_result = decoded_bytes.hex()
                return json.dumps({"hex": hex_result, "error": f"Decode failed: {str(e)}"})
                
    except Exception as e:
        return json.dumps({"error": f"Decrypt failed: {str(e)}", "raw_data": data})
