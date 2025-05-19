import redis
from datetime import datetime, timedelta
import re
from typing import Optional

class SMSStorage:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        
    async def store_sms(self, phone_number: str, message: str):
        """存储短信
        
        Args:
            phone_number: 手机号(必须是中国手机号)
            message: 短信内容
        """
        # 验证是否为中国手机号
        if not re.match(r'^1[3-9]\d{9}$', phone_number):
            raise ValueError("Invalid Chinese phone number")
            
        key = f"sms:cn:{phone_number}:{datetime.now().timestamp()}"
        self.redis_client.setex(key, timedelta(minutes=15), message)
        
    async def get_verification_code(self, phone_number: str) -> Optional[str]:
        """提取短信中的验证码
        
        Args:
            phone_number: 手机号
            
        Returns:
            str: 验证码
        """
        message = await self.get_latest_sms(phone_number)
        if not message:
            return None
            
        # 常见验证码格式匹配
        patterns = [
            r'验证码[是为:]?\s*([0-9]{4,6})',
            r'[验证码号码]\s*[:：是]?\s*([0-9]{4,6})',
            r'([0-9]{4,6})\s*[是为]?[验证码]',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                return match.group(1)
        return None
        
    async def get_latest_sms(self, phone_number: str):
        # 获取最新短信
        pattern = f"sms:cn:{phone_number}:*"
        keys = self.redis_client.keys(pattern)
        if not keys:
            return None
        latest_key = max(keys)
        return self.redis_client.get(latest_key) 