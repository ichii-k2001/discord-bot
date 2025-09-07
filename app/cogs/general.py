import discord
from discord.ext import commands
from discord import app_commands

class GeneralHelp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Bot全体のコマンド一覧を表示します")
    async def help(self, interaction: discord.Interaction):
        response = (
            "**🤖 Discord Bot コマンド一覧**\n\n"
            "**🎮 スプラトゥーン機能**\n"
            "• `/splatoon_help` - スプラトゥーン機能のヘルプ\n"
            "• `/splatoon_team` - チーム編成\n"
            "• `/splatoon_weapon` - ブキ情報検索\n\n"
            "**📅 カレンダー機能**\n"
            "• `/calendar_help` - カレンダー機能のヘルプ\n"
            "• `/calendar_add` - 予定追加\n"
            "• `/calendar_list` - 予定一覧\n"
            "• `/calendar_today` - 今日の予定\n\n"
            "**📋 タスク管理機能**\n"
            "• `/task_help` - タスク管理機能のヘルプ\n"
            "• `/task_add` - タスク追加\n"
            "• `/task_list` - タスク一覧\n"
            "• `/task_due` - 期限確認\n\n"
            "**💡 ヒント:** 各機能の詳細は対応する `_help` コマンドで確認できます！"
        )
        await interaction.response.send_message(response, ephemeral=True)

    @app_commands.command(name="ping", description="Botの応答速度を確認します")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        response = f"🏓 Pong! レイテンシ: {latency}ms"
        await interaction.response.send_message(response, ephemeral=True)

async def setup(bot):
    await bot.add_cog(GeneralHelp(bot))