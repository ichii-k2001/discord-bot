import discord
from discord.ext import commands
from discord import app_commands
import qrcode
from io import BytesIO
from datetime import datetime

class QRCodeGenerator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="qr", description="テキストやURLをQRコードに変換します")
    @app_commands.describe(text="QRコードに変換するテキストまたはURL")
    async def generate_qr(self, interaction: discord.Interaction, text: str):
        try:
            # QRコードを生成
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(text)
            qr.make(fit=True)

            # QRコード画像を作成
            qr_image = qr.make_image(fill_color="black", back_color="white")
            
            # BytesIOオブジェクトに保存
            img_buffer = BytesIO()
            qr_image.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            # Discordファイルオブジェクトを作成
            file = discord.File(img_buffer, filename="qrcode.png")
            
            # テキストの長さに応じてメッセージを調整
            if len(text) > 100:
                display_text = text[:97] + "..."
            else:
                display_text = text
            
            # 生成者情報を含むEmbed
            embed = discord.Embed(
                title="📱 QRコード生成完了",
                description=f"**変換内容:** `{display_text}`",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            embed.set_image(url="attachment://qrcode.png")
            embed.set_footer(
                text=f"生成者: {interaction.user.display_name} | QRコードをスキャンしてアクセスしてください",
                icon_url=interaction.user.display_avatar.url
            )
            
            await interaction.response.send_message(embed=embed, file=file)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ QRコード生成エラー",
                description=f"QRコードの生成に失敗しました。\n\n**エラー:** {str(e)}",
                color=0xff0000
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

class QRHelp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="qr_help", description="QRコード機能のヘルプを表示します")
    async def help(self, interaction: discord.Interaction):
        response = (
            "**📱 QRコード生成機能 コマンド一覧**\n\n"
            "👉 `/qr <テキスト>`\n"
            "　- テキストやURLをQRコードに変換します\n\n"
            "💡 **使用例:**\n"
            "• `/qr https://github.com` - URLをQRコードに変換\n"
            "• `/qr Hello World!` - テキストをQRコードに変換\n"
            "• `/qr WIFI:T:WPA;S:MyNetwork;P:MyPassword;;` - WiFi情報をQRコードに\n\n"
            "📋 **機能:**\n"
            "• 任意のテキストやURLをQRコードに変換\n"
            "• 高品質なPNG画像として出力\n"
            "• 生成者情報と生成時刻を記録\n"
            "• エラーハンドリング付き\n\n"
            "👉 `/qr_help`\n"
            "　- このヘルプを表示します"
        )
        await interaction.response.send_message(response, ephemeral=True)

async def setup(bot):
    await bot.add_cog(QRCodeGenerator(bot))
    await bot.add_cog(QRHelp(bot))