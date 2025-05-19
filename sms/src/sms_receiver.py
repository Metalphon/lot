from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class SMS(BaseModel):
    phone_number: str
    message: str
    timestamp: float

@app.post("/receive_sms")
async def receive_sms(sms: SMS):
    # 处理接收到的短信
    try:
        await store_sms(sms)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 