from .base import SMSProvider
import aiohttp
from typing import Optional, Dict

class YunXiangProvider(SMSProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "http://api.yunxiang.com"

    async def get_number(self, project_id: str) -> Optional[Dict]:
        """从云享平台获取号码
        
        Args:
            project_id: 项目ID
            
        Returns:
            Dict: 手机号信息
        """
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "appkey": self.api_key,
                    "pid": project_id,
                    "type": "get_mobile" 
                }
                async with session.get(f"{self.base_url}/api/get_mobile", params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data["code"] == 0:
                            return {
                                "phone": data["data"]["mobile"],
                                "order_id": data["data"]["order_id"]
                            }
            return None
        except Exception as e:
            print(f"YunXiang error: {str(e)}")
            return None 