import discord
from discord.ext import commands
from discord import app_commands

class GeneralHelp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Bot全体のコマンド一覧を表示します")
    async def help(self, interaction: discord.Interaction):
        response = (
            "**[UTIL] Discord Bot コマンド一覧**\n\n"
            "**[CAL] カレンダー機能** [WARN] 実装予定\n"
            "• Google Calendar連携の設定完了後に利用可能になります\n"
            "• 予定の追加・一覧表示・今日の予定確認などの機能を提供予定\n\n"
            "**[TASK] タスク管理機能** [WARN] 実装予定\n"
            "• Google Sheets連携の設定完了後に利用可能になります\n"
            "• タスクの追加・一覧表示・完了管理・期限確認などの機能を提供予定\n\n"
            "**[QR] QRコード機能**\n"
            "• `/qr_help` - QRコード機能のヘルプ\n"
            "• `/qr` - QRコード生成\n\n"
            "**[TRANS] 翻訳機能**\n"
            "• `/translate` - テキスト翻訳 (ja, en, zh-CN, zh-TW, ko, fr, de, es)\n"
            "• 言語選択肢と直接入力の両方に対応\n"
            "• 詳細表示時はコピー用テキストも提供\n"
            "• `/translate_help` - 翻訳機能のヘルプ\n\n"
            "**[REMIND] リマインダー機能**\n"
            "• `/remind_help` - リマインダー機能のヘルプ\n"
            "• `/remind` - 相対時間リマインダー (例: 5m, 1h)\n"
            "• `/remind_at` - 絶対時間リマインダー (例: 明日 9:00)\n"
            "• `/remind_list` - リマインダー一覧表示\n"
            "• `/remind_delete` - リマインダー削除\n"
            "• `/remind_clear` - 全リマインダー削除\n"
            "• スレッド参加者メンション・永続化対応\n\n"
            "**[UTIL] ユーティリティ機能**\n"
            "• `/ping` - Bot応答確認\n\n"
            "**[TIP] ヒント:** 各機能の詳細は対応する `_help` コマンドで確認できます！\n"
            "**[UTIL] 管理者向け:** カレンダー・タスク機能の有効化についてはセットアップドキュメントをご確認ください。"
        )
        await interaction.response.send_message(response, ephemeral=True)

    @app_commands.command(name="ping", description="Botの応答速度を確認します")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        response = f"[UTIL] Pong! レイテンシ: {latency}ms"
        await interaction.response.send_message(response, ephemeral=True)

async def setup(bot):
    await bot.add_cog(GeneralHelp(bot))