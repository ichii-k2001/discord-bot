import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()
intents = discord.Intents.default()

class MultiFeatureBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # 各機能のCogを読み込み
        await self.load_extension("app.cogs.splatoon")
        # await self.load_extension("app.cogs.calendar")  # 一時的に無効化（Google連携設定待ち）
        # await self.load_extension("app.cogs.tasks")     # 一時的に無効化（Google連携設定待ち）

        await self.load_extension("app.cogs.qr")
        await self.load_extension("app.cogs.general")
        
        # スラッシュコマンドを同期
        await self.tree.sync()
        print("✅ All cogs loaded and commands synced")

bot = MultiFeatureBot()

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    print(f"📊 Serving {len(bot.guilds)} guilds")
    print("🚀 Bot is ready!")
