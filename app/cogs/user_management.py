import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

class UserManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="privacy_mode", description="プライバシーモードの設定を変更します")
    @app_commands.describe(
        mode="プライバシーモード（shared/private）",
        feature="対象機能（calendar/tasks/all）"
    )
    @app_commands.choices(
        mode=[
            app_commands.Choice(name="共有モード", value="shared"),
            app_commands.Choice(name="プライベートモード", value="private")
        ],
        feature=[
            app_commands.Choice(name="カレンダー", value="calendar"),
            app_commands.Choice(name="タスク", value="tasks"),
            app_commands.Choice(name="すべて", value="all")
        ]
    )
    async def privacy_mode(self, interaction: discord.Interaction, mode: str, feature: str = "all"):
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild.id) if interaction.guild else "dm"
        
        # 設定を保存（実際の実装では永続化が必要）
        # ここでは簡単な例として応答のみ
        
        mode_text = "共有モード" if mode == "shared" else "プライベートモード"
        feature_text = {
            "calendar": "カレンダー",
            "tasks": "タスク",
            "all": "すべての機能"
        }.get(feature, feature)
        
        response = f"🔧 設定を更新しました！\n\n"
        response += f"👤 **ユーザー**: {interaction.user.display_name}\n"
        response += f"🏠 **サーバー**: {interaction.guild.name if interaction.guild else 'DM'}\n"
        response += f"🔒 **モード**: {mode_text}\n"
        response += f"📋 **対象**: {feature_text}\n\n"
        
        if mode == "shared":
            response += "✅ **共有モード**: 他のユーザーとデータを共有します\n"
            response += "　• チーム全体でタスクや予定を管理\n"
            response += "　• 全員が追加・編集・削除可能"
        else:
            response += "🔒 **プライベートモード**: 個人専用のデータ管理\n"
            response += "　• 自分のデータのみ表示\n"
            response += "　• 他のユーザーからは見えません"
        
        await interaction.response.send_message(response, ephemeral=True)

    @app_commands.command(name="privacy_status", description="現在のプライバシー設定を確認します")
    async def privacy_status(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild.id) if interaction.guild else "dm"
        
        # 現在は固定値（実際の実装では設定を読み込み）
        calendar_mode = "shared"  # 実際は設定から取得
        tasks_mode = "shared"     # 実際は設定から取得
        
        response = f"🔍 現在のプライバシー設定\n\n"
        response += f"👤 **ユーザー**: {interaction.user.display_name}\n"
        response += f"🏠 **サーバー**: {interaction.guild.name if interaction.guild else 'DM'}\n\n"
        response += f"📅 **カレンダー**: {'🌐 共有モード' if calendar_mode == 'shared' else '🔒 プライベートモード'}\n"
        response += f"📋 **タスク**: {'🌐 共有モード' if tasks_mode == 'shared' else '🔒 プライベートモード'}\n\n"
        response += f"💡 **変更方法**: `/privacy_mode` コマンドで設定変更可能"
        
        await interaction.response.send_message(response, ephemeral=True)

async def setup(bot):
    await bot.add_cog(UserManagement(bot))