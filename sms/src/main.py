import asyncio
import aiohttp
from number_pool import ChineseNumberPool

async def main():
    # 初始化号码池
    pool = ChineseNumberPool()
    
    # 设置API密钥(需要替换为您的实际API密钥)
    pool.api_key = "YOUR_API_KEY"  # 请替换为您在5sim.net注册获得的API密钥
    
    try:
        # 1. 查询单个产品价格
        print("\n1. 查询 Telegram 价格:")
        async with aiohttp.ClientSession() as session:
            # 使用guest API不需要认证
            url = "https://5sim.net/v1/guest/prices?country=russia&product=telegram"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    print("API返回数据:", data)
                    
                    # 解析数据
                    if "russia" in data and "telegram" in data["russia"]:
                        operators = data["russia"]["telegram"]
                        for operator, details in operators.items():
                            print(f"运营商: {operator}")
                            print(f"价格: {details['cost']}卢布")
                            print(f"库存: {details['count']}个")
                            if "rate" in details:
                                print(f"到货率: {details['rate']}%")
                            print("---")
                    else:
                        print("未找到Telegram的价格数据")
                else:
                    print(f"API请求失败，状态码: {response.status}")
                    
        # 2. 获取所有产品列表
        print("\n2. 所有可用产品列表:")
        async with aiohttp.ClientSession() as session:
            url = "https://5sim.net/v1/guest/products/russia/any"
            async with session.get(url) as response:
                if response.status == 200:
                    products = await response.json()
                    print("可用产品:")
                    for product_name, details in products.items():
                        if details["Category"] == "activation":
                            print(f"{product_name}:")
                            print(f"  价格: {details['Price']}卢布")
                            print(f"  库存: {details['Qty']}个")
                            print("---")
                else:
                    print(f"获取产品列表失败，状态码: {response.status}")
                    
    except aiohttp.ClientError as e:
        print(f"网络请求错误: {e}")
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    # 运行异步主函数
    asyncio.run(main())