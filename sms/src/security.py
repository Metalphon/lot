import redis

class RateLimiter:
    def __init__(self):
        self.redis_client = redis.Redis()
        
    async def check_rate_limit(self, ip: str):
        key = f"rate_limit:{ip}"
        current = self.redis_client.incr(key)
        if current == 1:
            self.redis_client.expire(key, 3600)  # 1小时过期
        return current <= 100  # 每小时限制100次请求 

class SecurityManager:
    def __init__(self):
        self.redis = redis.Redis()
        
    async def check_number(self, phone: str) -> bool:
        """检查号码是否可用"""
        # 检查是否被封禁
        if self.redis.sismember("banned_numbers", phone):
            return False
            
        # 检查使用频率
        usage_count = self.redis.incr(f"number_usage:{phone}")
        if usage_count > 3:  # 每个号码最多使用3次
            self.redis.sadd("banned_numbers", phone)
            return False
            
        return True 