from .base import SMSProvider
import aiohttp
from typing import Optional, Dict

class SMSActivateProvider(SMSProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.sms-activate.org/stubs/handler_api.php"

    async def get_number(self, service: str) -> Optional[Dict]:
        """获取临时手机号
        
        Args:
            service: 服务类型(如wechat/qq/alipay等)
            
        Returns:
            Dict: {
                "phone": "手机号",
                "order_id": "订单ID",
                "price": "价格"
            }
        """
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "api_key": self.api_key,
                    "action": "getNumber",
                    "service": service,
                    "country": 0, # 中国
                }
                async with session.get(self.base_url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.text()
                        # ACCESS_NUMBER:订单ID:手机号:价格
                        if data.startswith("ACCESS_NUMBER"):
                            _, order_id, phone, price = data.split(":")
                            return {
                                "phone": phone,
                                "order_id": order_id,
                                "price": float(price)
                            }
            return None
        except Exception as e:
            print(f"Get number error: {str(e)}")
            return None 