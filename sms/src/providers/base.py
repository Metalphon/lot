class SMSProvider:
    async def get_number(self, country_code: str):
        raise NotImplementedError
        
    async def release_number(self, number: str):
        raise NotImplementedError 