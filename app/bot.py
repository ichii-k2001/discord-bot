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
        # await self.load_extension("app.cogs.calendar")  # 一時的に無効化（Google連携設定待ち）
        # await self.load_extension("app.cogs.tasks")     # 一時的に無効化（Google連携設定待ち）

        try:
            await self.load_extension("app.cogs.qr")
            print("[OK] QR cog loaded")
        except Exception as e:
            print(f"[ERROR] Failed to load QR cog: {e}")
        
        try:
            await self.load_extension("app.cogs.reminder")
            print("[OK] Reminder cog loaded")
        except Exception as e:
            print(f"[ERROR] Failed to load reminder cog: {e}")
        
        try:
            await self.load_extension("app.cogs.general")
            print("[OK] General cog loaded")
        except Exception as e:
            print(f"[ERROR] Failed to load general cog: {e}")
        
        try:
            await self.load_extension("app.cogs.translate")
            print("[OK] Translate cog loaded")
        except Exception as e:
            print(f"[ERROR] Failed to load translate cog: {e}")
        
        # スラッシュコマンドを同期
        try:
            synced = await self.tree.sync()
            print(f"[OK] Synced {len(synced)} commands")
            for cmd in synced:
                print(f"  - {cmd.name}: {cmd.description}")
        except Exception as e:
            print(f"[ERROR] Failed to sync commands: {e}")

bot = MultiFeatureBot()

@bot.event
async def on_ready():
    print(f"[OK] Logged in as {bot.user}")
    print(f"[INFO] Serving {len(bot.guilds)} guilds")
    print("[START] Bot is ready!")
