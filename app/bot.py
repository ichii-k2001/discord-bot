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
        try:
            await self.load_extension("app.cogs.splatoon")
            print("✅ Splatoon cog loaded")
        except Exception as e:
            print(f"❌ Failed to load splatoon cog: {e}")
        
        # await self.load_extension("app.cogs.calendar")  # 一時的に無効化（Google連携設定待ち）
        # await self.load_extension("app.cogs.tasks")     # 一時的に無効化（Google連携設定待ち）

        try:
            await self.load_extension("app.cogs.qr")
            print("✅ QR cog loaded")
        except Exception as e:
            print(f"❌ Failed to load QR cog: {e}")
        
        try:
            await self.load_extension("app.cogs.reminder")
            print("✅ Reminder cog loaded")
        except Exception as e:
            print(f"❌ Failed to load reminder cog: {e}")
        
        try:
            await self.load_extension("app.cogs.general")
            print("✅ General cog loaded")
        except Exception as e:
            print(f"❌ Failed to load general cog: {e}")
        
        # スラッシュコマンドを同期
        try:
            await self.tree.sync()
            print("✅ All commands synced")
        except Exception as e:
            print(f"❌ Failed to sync commands: {e}")

bot = MultiFeatureBot()

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    print(f"📊 Serving {len(bot.guilds)} guilds")
    print("🚀 Bot is ready!")
