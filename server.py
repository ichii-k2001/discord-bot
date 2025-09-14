import os
import asyncio
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from app.bot import bot

app = FastAPI()

@app.get("/", include_in_schema=False)
@app.head("/", include_in_schema=False)
async def health_check():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"✅ UptimeRobot ping received at {now}")
    return JSONResponse(content={"message": "Bot is running!"})

@app.on_event("startup")
async def on_startup():
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_TOKEN is not set")
    asyncio.create_task(bot.start(token))
