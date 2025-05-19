from typing import Dict, Optional
from datetime import datetime, timedelta
import aiohttp
import json

class ChineseNumberPool:
    def __init__(self):
        self.available_numbers: Dict[str, dict] = {}  # 存储可用号码
        self.in_use_numbers: Dict[str, dict] = {}    # 存储使用中的号码
        self.api_key = "YOUR_API_KEY"  # 接码平台的API密钥
        self.provider_urls = {
            "sms_activate": "https://api.sms-activate.org/stubs/handler_api.php",
            "yunxiang": "http://api.yunxiang.com/api/v1",  # 云享号码池
            "smspva": "http://smspva.com/priemnik.php"
        }
        self.provider_stats = {
            "sms_activate": {"success": 0, "total": 0, "total_response_time": 0, "total_cost": 0, "errors": 0},
            "yunxiang": {"success": 0, "total": 0, "total_response_time": 0, "total_cost": 0, "errors": 0},
            "smspva": {"success": 0, "total": 0, "total_response_time": 0, "total_cost": 0, "errors": 0}
        }
        self.base_url = "https://5sim.net/v1"
        
    async def acquire_number(self, service: str = "any") -> Optional[str]:
        """获取一个中国临时号码
        
        Args:
            service: 需要接码的服务名称，如'wechat','alipay'等
            
        Returns:
            str: 手机号码
        """
        if not self.available_numbers:
            await self._replenish_pool()
            
        for number, info in self.available_numbers.items():
            if service == "any" or service in info["supported_services"]:
                self.in_use_numbers[number] = self.available_numbers.pop(number)
                return number
        return None

    async def _replenish_pool(self, count: int = 5):
        """补充号码池
        
        Args:
            count: 需要补充的号码数量
        """
        for provider, url in self.provider_urls.items():
            try:
                async with aiohttp.ClientSession() as session:
                    params = {
                        "api_key": self.api_key,
                        "action": "getNumber",
                        "service": "any",
                        "country": "cn",
                        "count": count
                    }
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            for number_data in data["numbers"]:
                                self.available_numbers[number_data["phone"]] = {
                                    "provider": provider,
                                    "expire_time": datetime.now() + timedelta(minutes=20),
                                    "supported_services": number_data["services"],
                                    "order_id": number_data["id"]
                                }
                            if self.available_numbers:
                                break
            except Exception as e:
                print(f"Provider {provider} error: {str(e)}")
                continue

    async def release_number(self, number: str):
        """释放号码回号码池
        
        Args:
            number: 要释放的手机号
        """
        if number in self.in_use_numbers:
            info = self.in_use_numbers.pop(number)
            # 通知供应商释放号码
            try:
                async with aiohttp.ClientSession() as session:
                    params = {
                        "api_key": self.api_key,
                        "action": "setStatus",
                        "id": info["order_id"],
                        "status": 8  # 标记为完成
                    }
                    provider_url = self.provider_urls[info["provider"]]
                    await session.get(provider_url, params=params)
            except Exception as e:
                print(f"Release number error: {str(e)}")

    async def get_sms(self, number: str, timeout: int = 60) -> Optional[str]:
        """获取指定号码的短信内容
        
        Args:
            number: 手机号
            timeout: 等待超时时间(秒)
            
        Returns:
            str: 短信内容
        """
        if number not in self.in_use_numbers:
            return None
            
        info = self.in_use_numbers[number]
        start_time = datetime.now()
        
        while (datetime.now() - start_time).seconds < timeout:
            try:
                async with aiohttp.ClientSession() as session:
                    params = {
                        "api_key": self.api_key,
                        "action": "getStatus",
                        "id": info["order_id"]
                    }
                    provider_url = self.provider_urls[info["provider"]]
                    async with session.get(provider_url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get("sms"):
                                return data["sms"]
            except Exception as e:
                print(f"Get SMS error: {str(e)}")
            await asyncio.sleep(3)
        
        return None 

    async def _select_best_provider(self) -> str:
        """选择最优供应商"""
        provider_scores = {
            "sms_activate": 0,
            "yunxiang": 0,
            "smspva": 0
        }
        
        # 检查成功率
        for provider in self.provider_stats:
            success_rate = provider["success"] / (provider["total"] + 1)
            provider_scores[provider["name"]] += success_rate * 5
            
        # 检查平均响应时间
        for provider in self.provider_stats:
            avg_response = provider["total_response_time"] / (provider["total"] + 1)
            provider_scores[provider["name"]] += (1 / avg_response) * 3
            
        # 检查价格
        for provider in self.provider_stats:
            avg_price = provider["total_cost"] / (provider["total"] + 1)
            provider_scores[provider["name"]] += (1 / avg_price) * 2
            
        return max(provider_scores.items(), key=lambda x: x[1])[0]

    async def _handle_provider_error(self, provider: str, error: Exception):
        """处理供应商错误"""
        self.provider_stats[provider]["errors"] += 1
        
        # 如果错误次数过多，暂时禁用该供应商
        if self.provider_stats[provider]["errors"] > 5:
            self.provider_stats[provider]["disabled_until"] = datetime.now() + timedelta(minutes=30)

    async def get_product_price(self, product: str = "any", country: str = "china") -> dict:
        """获取指定产品的号码价格
        
        Args:
            product: 产品名称(如:telegram, whatsapp等)
            country: 国家代码(默认:china)
            
        Returns:
            dict: {
                "cost": float,      # 价格
                "count": int,       # 可用数量
                "rate": float       # 到货率(百分比)
            }
        """
        try:
            async with aiohttp.ClientSession() as session:
                # 获取价格列表
                url = f"{self.base_url}/guest/prices"
                params = {
                    "country": country,
                    "product": product
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # 解析返回数据
                        if country in data and product in data[country]:
                            operators = data[country][product]
                            
                            # 找出最低价格的运营商
                            best_price = None
                            for operator_data in operators.values():
                                if operator_data["count"] > 0:  # 只考虑有库存的
                                    price = operator_data["cost"]
                                    if best_price is None or price < best_price["cost"]:
                                        best_price = operator_data
                            
                            if best_price:
                                return {
                                    "cost": best_price["cost"],
                                    "count": best_price["count"],
                                    "rate": best_price.get("rate", 0)
                                }
                            
            return {"error": "No available numbers"}
                        
        except Exception as e:
            return {"error": f"Price check failed: {str(e)}"}
            
    async def get_all_prices(self, country: str = "china") -> dict:
        """获取所有产品的价格列表
        
        Args:
            country: 国家代码(默认:china)
            
        Returns:
            dict: {
                "product_name": {
                    "cost": float,
                    "count": int,
                    "rate": float
                },
                ...
            }
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/guest/products/{country}/any"
                
                async with session.get(url) as response:
                    if response.status == 200:
                        products = await response.json()
                        
                        result = {}
                        for product_name, product_data in products.items():
                            if product_data["Category"] == "activation":  # 只返回激活码类型
                                result[product_name] = {
                                    "cost": product_data["Price"],
                                    "count": product_data["Qty"],
                                    "category": product_data["Category"]
                                }
                        
                        return result
                        
            return {"error": "Failed to get product list"}
            
        except Exception as e:
            return {"error": f"Price check failed: {str(e)}"} 