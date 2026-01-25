import discord
from discord.ext import commands
from discord import app_commands
from app.services.translate_service import TranslateService

class TranslateCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.translate_service = TranslateService()

    @app_commands.command(name="translate", description="テキストを指定した言語に翻訳します")
    @app_commands.describe(
        language="翻訳先の言語を選択してください",
        text="翻訳したいテキスト",
        show_details="原文と言語情報を表示するかどうか (デフォルト: False)"
    )
    @app_commands.choices(language=TranslateService().get_language_choices())
    async def translate(self, interaction: discord.Interaction, language: str, text: str, show_details: bool = False):
        """翻訳コマンドのメイン処理"""
        await interaction.response.defer()
        
        # 翻訳実行
        result = await self.translate_service.translate_text(
            text=text,
            target_lang=language,
            user_id=interaction.user.id
        )
        
        if not result['success']:
            # エラー時の処理
            embed = discord.Embed(
                title="[ERROR] 翻訳エラー",
                description=result['error'],
                color=0xff4444
            )
            
            if result['error_type'] == 'invalid_language':
                # 対応言語一覧を表示
                lang_list = []
                for code, info in self.translate_service.LANGUAGES.items():
                    lang_list.append(f"{info['flag']} `{code}` - {info['name']}")
                
                embed.add_field(
                    name="対応言語",
                    value="\n".join(lang_list),
                    inline=False
                )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # 成功時の処理
        if show_details:
            # 詳細表示モード（従来の埋め込み形式）
            source_info = self.translate_service.get_language_info(result['source_lang'])
            target_info = self.translate_service.get_language_info(result['target_lang'])
            
            # 国旗絵文字取得（フォールバック付き）
            source_flag = source_info.get('flag', '🌐')
            target_flag = target_info.get('flag', '🌐')
            
            # 埋め込みメッセージ作成
            embed = discord.Embed(
                title="[TRANS] 翻訳結果",
                description=f"{source_flag} → {target_flag}",
                color=0x4285f4
            )
            
            # 原文（長い場合は省略）
            original_display = result['original_text']
            if len(original_display) > 200:
                original_display = original_display[:200] + "..."
            
            embed.add_field(
                name="原文",
                value=f"```{original_display}```",
                inline=False
            )
            
            # 翻訳結果
            translated_display = result['translated_text']
            if len(translated_display) > 200:
                translated_display = translated_display[:200] + "..."
            
            embed.add_field(
                name="翻訳",
                value=f"```{translated_display}```",
                inline=False
            )
            
            # 使用統計とフッター情報
            user_stats = self.translate_service.get_user_stats(interaction.user.id)
            cache_indicator = "💾" if result.get('cached', False) else ""
            
            footer_text = (
                f"今日の使用: {user_stats['daily']}/{self.translate_service.RATE_LIMITS['per_day']} | "
                f"処理時間: {result['process_time']:.1f}秒 {cache_indicator}"
            )
            embed.set_footer(text=footer_text)
            
            # 使用量警告
            warning_message = self._get_usage_warning(user_stats)
            if warning_message:
                embed.add_field(
                    name="[WARN] 使用量お知らせ",
                    value=warning_message,
                    inline=False
                )
            
            # 埋め込み表示後に翻訳結果をコピー用として送信
            await interaction.followup.send(embed=embed)
            await interaction.followup.send(f"[UTIL] **コピー用:**\n{result['translated_text']}")
        else:
            # シンプル表示モード（翻訳結果のみ）
            user_stats = self.translate_service.get_user_stats(interaction.user.id)
            
            # 使用制限が10回を切った場合は警告表示
            if user_stats['daily'] >= self.translate_service.RATE_LIMITS['per_day'] - 10:
                usage_info = f"\n\n[WARN] 今日の使用: {user_stats['daily']}/{self.translate_service.RATE_LIMITS['per_day']}"
                await interaction.followup.send(result['translated_text'] + usage_info)
            else:
                await interaction.followup.send(result['translated_text'])

    @app_commands.command(name="translate_help", description="翻訳機能のヘルプを表示します")
    async def translate_help(self, interaction: discord.Interaction):
        """翻訳機能のヘルプ"""
        embed = discord.Embed(
            title="[TRANS] 翻訳機能ヘルプ",
            description="サーバー内で簡単にテキスト翻訳ができます",
            color=0x4285f4
        )
        
        # 基本的な使い方
        embed.add_field(
            name="[INFO] 基本的な使い方",
            value=(
                "```\n"
                "/translate <言語> <テキスト> [詳細表示]\n"
                "```\n"
                "**例:**\n"
                "`/translate language:en text:今日はいい天気ですね` → 翻訳結果のみ\n"
                "`/translate language:[FLAG] 日本語 (ja) text:Hello` → 選択肢から選択\n"
                "`/translate language:ja text:Hello show_details:True` → 詳細+コピー用"
            ),
            inline=False
        )
        
        # 対応言語
        lang_list = []
        for code, info in self.translate_service.LANGUAGES.items():
            lang_list.append(f"{info['flag']} `{code}` - {info['name']}")
        
        embed.add_field(
            name="[TRANS] 対応言語",
            value="\n".join(lang_list),
            inline=False
        )
        
        # 制限事項
        limits = self.translate_service.RATE_LIMITS
        embed.add_field(
            name="[WARN] 使用制限",
            value=(
                f"• 1分間: {limits['per_minute']}回まで\n"
                f"• 1時間: {limits['per_hour']}回まで\n"
                f"• 1日: {limits['per_day']}回まで\n"
                f"• 最大文字数: {self.translate_service.MAX_TEXT_LENGTH}文字"
            ),
            inline=False
        )
        
        # 機能説明
        embed.add_field(
            name="[INFO] 機能",
            value=(
                "• 高精度な翻訳（Google翻訳ベース）\n"
                "• 柔軟な言語入力（選択肢・直接入力対応）\n"
                "• 自動言語検出\n"
                "• 翻訳結果キャッシュ（高速化）\n"
                "• シンプル表示（デフォルト）と詳細表示の選択\n"
                "• 詳細表示時のコピー用テキスト提供\n"
                "• 使用制限の早期警告表示\n"
                "• レート制限による負荷軽減"
            ),
            inline=False
        )
        
        embed.set_footer(text="[TIP] ヒント: 言語は選択肢から選ぶか、直接コード入力（ja, en等）も可能。詳細表示ではコピー用テキストも提供されます")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    def _get_usage_warning(self, user_stats: dict) -> str:
        """使用量に応じた警告メッセージを生成"""
        daily_limit = self.translate_service.RATE_LIMITS['per_day']
        hourly_limit = self.translate_service.RATE_LIMITS['per_hour']
        
        daily_usage = user_stats['daily']
        hourly_usage = user_stats['hourly']
        
        # 1日の使用量警告
        if daily_usage >= daily_limit * 0.9:  # 90%以上
            return f"1日の使用制限に近づいています ({daily_usage}/{daily_limit})"
        elif daily_usage >= daily_limit * 0.7:  # 70%以上
            return f"1日の使用量: {daily_usage}/{daily_limit} (残り{daily_limit - daily_usage}回)"
        
        # 1時間の使用量警告
        if hourly_usage >= hourly_limit * 0.8:  # 80%以上
            return f"1時間の使用制限に近づいています ({hourly_usage}/{hourly_limit})"
        
        return ""

async def setup(bot):
    await bot.add_cog(TranslateCog(bot))