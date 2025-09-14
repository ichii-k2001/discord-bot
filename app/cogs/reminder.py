import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import re
import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Set

class ReminderManager:
    def __init__(self, file_path: str = "data/reminders.json"):
        self.file_path = file_path
        self.ensure_data_dir()
    
    def ensure_data_dir(self):
        """データディレクトリとファイルの存在を確認"""
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(self.file_path):
            self.save_reminders([])
    
    def load_reminders(self) -> List[Dict]:
        """リマインダーデータを読み込み"""
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("reminders", [])
        except Exception as e:
            print(f"リマインダー読み込みエラー: {e}")
            return []
    
    def save_reminders(self, reminders: List[Dict]):
        """リマインダーデータを保存"""
        try:
            data = {"reminders": reminders}
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"リマインダー保存エラー: {e}")
    
    def add_reminder(self, user_id: int, channel_id: int, message: str, 
                    target_time: datetime, mention_thread_users: bool = False, 
                    thread_users: Set[int] = None) -> str:
        """新しいリマインダーを追加"""
        reminder_id = str(uuid.uuid4())
        reminder = {
            "id": reminder_id,
            "user_id": user_id,
            "channel_id": channel_id,
            "message": message,
            "target_time": target_time.isoformat(),
            "mention_thread_users": mention_thread_users,
            "thread_users": list(thread_users) if thread_users else [],
            "created_at": datetime.now().isoformat()
        }
        
        reminders = self.load_reminders()
        reminders.append(reminder)
        self.save_reminders(reminders)
        return reminder_id
    
    def get_due_reminders(self) -> List[Dict]:
        """期限切れのリマインダーを取得"""
        now = datetime.now()
        reminders = self.load_reminders()
        due_reminders = []
        
        for reminder in reminders:
            target_time = datetime.fromisoformat(reminder["target_time"])
            if target_time <= now:
                due_reminders.append(reminder)
        
        return due_reminders
    
    def remove_reminder(self, reminder_id: str):
        """リマインダーを削除"""
        reminders = self.load_reminders()
        reminders = [r for r in reminders if r["id"] != reminder_id]
        self.save_reminders(reminders)
    
    def cleanup_old_reminders(self, days: int = 7):
        """古いリマインダーをクリーンアップ"""
        cutoff_date = datetime.now() - timedelta(days=days)
        reminders = self.load_reminders()
        
        cleaned_reminders = []
        for reminder in reminders:
            target_time = datetime.fromisoformat(reminder["target_time"])
            if target_time > cutoff_date:
                cleaned_reminders.append(reminder)
        
        if len(cleaned_reminders) != len(reminders):
            self.save_reminders(cleaned_reminders)
            print(f"古いリマインダー {len(reminders) - len(cleaned_reminders)} 件をクリーンアップしました")


class ReminderCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reminder_manager = ReminderManager()
        self.check_reminders.start()  # バックグラウンドタスク開始
    
    def cog_unload(self):
        """Cog終了時にタスクを停止"""
        self.check_reminders.cancel()
    
    @tasks.loop(minutes=1)
    async def check_reminders(self):
        """1分ごとにリマインダーをチェック"""
        try:
            due_reminders = self.reminder_manager.get_due_reminders()
            
            for reminder in due_reminders:
                await self.execute_reminder(reminder)
                self.reminder_manager.remove_reminder(reminder["id"])
            
            # 週1回古いリマインダーをクリーンアップ
            if datetime.now().hour == 3 and datetime.now().minute == 0:
                self.reminder_manager.cleanup_old_reminders()
                
        except Exception as e:
            print(f"リマインダーチェックエラー: {e}")
    
    @check_reminders.before_loop
    async def before_check_reminders(self):
        """Bot起動完了まで待機"""
        await self.bot.wait_until_ready()
    
    async def execute_reminder(self, reminder: Dict):
        """リマインダーを実行"""
        try:
            channel = self.bot.get_channel(reminder["channel_id"])
            if not channel:
                print(f"チャンネルが見つかりません: {reminder['channel_id']}")
                return
            
            # メンション文字列を構築
            mentions = f"<@{reminder['user_id']}>"
            
            if reminder["mention_thread_users"] and reminder["thread_users"]:
                # 設定者を除外してスレッドユーザーを追加
                other_users = set(reminder["thread_users"]) - {reminder["user_id"]}
                if other_users:
                    thread_mentions = " ".join([f"<@{uid}>" for uid in other_users])
                    mentions += f" {thread_mentions}"
            
            await channel.send(f"⏰ {mentions} リマインダー: {reminder['message']}")
            
        except Exception as e:
            print(f"リマインダー実行エラー: {e}")
    
    @app_commands.command(name="remind", description="指定した時間後にリマインダーを設定します")
    @app_commands.describe(
        time="リマインダーまでの時間 (例: 5m, 1h, 2d)",
        message="リマインダーメッセージ",
        mention_thread_users="スレッド内の過去の返信者もメンションするか (デフォルト: False)"
    )
    async def remind(self, interaction: discord.Interaction, time: str, message: str = "リマインダー！", mention_thread_users: bool = False):
        """指定した時間後にリマインダーを設定"""
        try:
            # 時間文字列を解析
            seconds = self.parse_time(time)
            if seconds is None:
                await interaction.response.send_message(
                    "❌ 時間形式が無効です。以下の形式を使用してください: 5m, 1h, 2d", 
                    ephemeral=True
                )
                return
            
            if seconds > 86400 * 30:  # 30日間が上限
                await interaction.response.send_message(
                    "❌ リマインダーは30日以内で設定してください", 
                    ephemeral=True
                )
                return
            
            # 目標時刻を計算
            target_time = datetime.now() + timedelta(seconds=seconds)
            user_id = interaction.user.id
            channel_id = interaction.channel.id
            
            # スレッドユーザーの情報を取得
            thread_users = set()
            if mention_thread_users and hasattr(interaction.channel, 'parent'):
                thread_users = await self.get_thread_users(interaction.channel)
                thread_count = len(thread_users)
                if thread_count > 0:
                    await interaction.response.send_message(
                        f"⏰ {time}後にリマインダーを設定しました: {message}\n"
                        f"📝 スレッド内の{thread_count}人のユーザーにもメンションします\n"
                        f"🔄 Bot再起動後も継続されます"
                    )
                else:
                    await interaction.response.send_message(
                        f"⏰ {time}後にリマインダーを設定しました: {message}\n"
                        f"📝 スレッド内に他のユーザーが見つかりませんでした\n"
                        f"🔄 Bot再起動後も継続されます"
                    )
            else:
                await interaction.response.send_message(
                    f"⏰ {time}後にリマインダーを設定しました: {message}\n"
                    f"🔄 Bot再起動後も継続されます"
                )
            
            # リマインダーをJSONに保存
            self.reminder_manager.add_reminder(
                user_id=user_id,
                channel_id=channel_id,
                message=message,
                target_time=target_time,
                mention_thread_users=mention_thread_users,
                thread_users=thread_users
            )
                
        except Exception as e:
            await interaction.response.send_message(
                f"❌ リマインダー設定エラー: {str(e)}", 
                ephemeral=True
            )
    
    def parse_time(self, time_str: str) -> Optional[int]:
        """時間文字列を解析して秒数を返す"""
        time_str = time_str.lower().strip()
        
        # Regex patterns for different time formats
        patterns = {
            r'(\d+)s': 1,           # seconds
            r'(\d+)m': 60,          # minutes
            r'(\d+)h': 3600,        # hours
            r'(\d+)d': 86400,       # days
        }
        
        total_seconds = 0
        
        for pattern, multiplier in patterns.items():
            matches = re.findall(pattern, time_str)
            for match in matches:
                total_seconds += int(match) * multiplier
        
        return total_seconds if total_seconds > 0 else None
    
    async def get_thread_users(self, channel, limit: int = 50) -> Set[int]:
        """スレッド内の過去のメッセージ送信者を取得"""
        thread_users = set()
        
        try:
            # スレッドかどうかを確認
            if not hasattr(channel, 'parent'):
                return thread_users
            
            # 過去のメッセージを取得
            async for message in channel.history(limit=limit):
                if not message.author.bot:  # Botは除外
                    thread_users.add(message.author.id)
            
            return thread_users
        except Exception as e:
            print(f"スレッドユーザー取得エラー: {e}")
            return thread_users
    
    @app_commands.command(name="remind_at", description="指定した日時にリマインダーを設定します")
    @app_commands.describe(
        date="日付 (例: 2024-12-25, 12/25, 明日)",
        time="時刻 (例: 14:30, 2:30pm)",
        message="リマインダーメッセージ",
        mention_thread_users="スレッド内の過去の返信者もメンションするか (デフォルト: False)"
    )
    async def remind_at(self, interaction: discord.Interaction, date: str, time: str, message: str = "リマインダー！", mention_thread_users: bool = False):
        """指定した日時にリマインダーを設定"""
        try:
            # 日時を解析
            target_datetime = self.parse_datetime(date, time)
            if target_datetime is None:
                await interaction.response.send_message(
                    "❌ 日時形式が無効です。\n"
                    "**日付例:** 2024-12-25, 12/25, 今日, 明日\n"
                    "**時刻例:** 14:30, 2:30pm, 9:00",
                    ephemeral=True
                )
                return
            
            now = datetime.now()
            if target_datetime <= now:
                await interaction.response.send_message(
                    "❌ 過去の日時は指定できません", 
                    ephemeral=True
                )
                return
            
            # 30日以内の制限
            if (target_datetime - now).days > 30:
                await interaction.response.send_message(
                    "❌ リマインダーは30日以内で設定してください", 
                    ephemeral=True
                )
                return
            
            user_id = interaction.user.id
            channel_id = interaction.channel.id
            
            # 日時をフォーマット
            formatted_datetime = target_datetime.strftime("%Y年%m月%d日 %H:%M")
            
            # スレッドユーザーの情報を取得
            thread_users = set()
            if mention_thread_users and hasattr(interaction.channel, 'parent'):
                thread_users = await self.get_thread_users(interaction.channel)
                thread_count = len(thread_users)
                if thread_count > 0:
                    await interaction.response.send_message(
                        f"⏰ {formatted_datetime}にリマインダーを設定しました: {message}\n"
                        f"📝 スレッド内の{thread_count}人のユーザーにもメンションします\n"
                        f"🔄 Bot再起動後も継続されます"
                    )
                else:
                    await interaction.response.send_message(
                        f"⏰ {formatted_datetime}にリマインダーを設定しました: {message}\n"
                        f"📝 スレッド内に他のユーザーが見つかりませんでした\n"
                        f"🔄 Bot再起動後も継続されます"
                    )
            else:
                await interaction.response.send_message(
                    f"⏰ {formatted_datetime}にリマインダーを設定しました: {message}\n"
                    f"🔄 Bot再起動後も継続されます"
                )
            
            # リマインダーをJSONに保存
            self.reminder_manager.add_reminder(
                user_id=user_id,
                channel_id=channel_id,
                message=message,
                target_time=target_datetime,
                mention_thread_users=mention_thread_users,
                thread_users=thread_users
            )
                
        except Exception as e:
            await interaction.response.send_message(
                f"❌ リマインダー設定エラー: {str(e)}", 
                ephemeral=True
            )
    
    def parse_datetime(self, date_str: str, time_str: str) -> Optional[datetime]:
        """日付と時刻文字列を解析してdatetimeオブジェクトを返す"""
        try:
            now = datetime.now()
            target_date = None
            
            # 日付の解析
            date_str = date_str.strip().lower()
            
            if date_str in ["今日", "today"]:
                target_date = now.date()
            elif date_str in ["明日", "tomorrow"]:
                target_date = (now + timedelta(days=1)).date()
            elif date_str in ["明後日"]:
                target_date = (now + timedelta(days=2)).date()
            else:
                # 様々な日付形式を試行
                date_formats = [
                    "%Y-%m-%d",     # 2024-12-25
                    "%Y/%m/%d",     # 2024/12/25
                    "%m/%d",        # 12/25 (今年)
                    "%m-%d",        # 12-25 (今年)
                ]
                
                for fmt in date_formats:
                    try:
                        if fmt in ["%m/%d", "%m-%d"]:
                            # 年を追加
                            parsed_date = datetime.strptime(f"{now.year}-{date_str.replace('/', '-')}", "%Y-%m-%d").date()
                            # 過去の日付の場合は来年にする
                            if parsed_date < now.date():
                                parsed_date = parsed_date.replace(year=now.year + 1)
                            target_date = parsed_date
                        else:
                            target_date = datetime.strptime(date_str, fmt).date()
                        break
                    except ValueError:
                        continue
            
            if target_date is None:
                return None
            
            # 時刻の解析
            time_str = time_str.strip().lower()
            target_time = None
            
            # 様々な時刻形式を試行
            time_formats = [
                "%H:%M",        # 14:30
                "%H:%M:%S",     # 14:30:00
                "%I:%M%p",      # 2:30PM
                "%I%p",         # 2PM
            ]
            
            # AM/PM表記の正規化
            time_str = time_str.replace("am", "AM").replace("pm", "PM")
            if not ("AM" in time_str or "PM" in time_str):
                # AM/PMがない場合は24時間形式として扱う
                time_formats = ["%H:%M", "%H:%M:%S"] + time_formats
            
            for fmt in time_formats:
                try:
                    target_time = datetime.strptime(time_str, fmt).time()
                    break
                except ValueError:
                    continue
            
            if target_time is None:
                return None
            
            # 日付と時刻を結合
            target_datetime = datetime.combine(target_date, target_time)
            return target_datetime
            
        except Exception:
            return None

    @app_commands.command(name="remind_list", description="設定中のリマインダー一覧を表示します")
    async def remind_list(self, interaction: discord.Interaction):
        """設定中のリマインダー一覧を表示"""
        try:
            reminders = self.reminder_manager.load_reminders()
            user_reminders = [r for r in reminders if r["user_id"] == interaction.user.id]
            
            if not user_reminders:
                await interaction.response.send_message(
                    "📝 設定中のリマインダーはありません", 
                    ephemeral=True
                )
                return
            
            # リマインダーを時刻順にソート
            user_reminders.sort(key=lambda x: x["target_time"])
            
            response = "**⏰ あなたのリマインダー一覧**\n\n"
            
            for i, reminder in enumerate(user_reminders[:10], 1):  # 最大10件表示
                target_time = datetime.fromisoformat(reminder["target_time"])
                formatted_time = target_time.strftime("%m/%d %H:%M")
                
                thread_info = ""
                if reminder["mention_thread_users"] and reminder["thread_users"]:
                    thread_info = f" (スレッド{len(reminder['thread_users'])}人)"
                
                response += f"{i}. **{formatted_time}** - {reminder['message']}{thread_info}\n"
            
            if len(user_reminders) > 10:
                response += f"\n... 他 {len(user_reminders) - 10} 件"
            
            await interaction.response.send_message(response, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ リマインダー一覧取得エラー: {str(e)}", 
                ephemeral=True
            )


class ReminderHelp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="remind_help", description="リマインダー機能のヘルプを表示します")
    async def help(self, interaction: discord.Interaction):
        response = (
            "**⏰ リマインダー機能 コマンド一覧**\n\n"
            "**📅 相対時間リマインダー**\n"
            "👉 `/remind <時間> [メッセージ] [スレッドユーザーメンション]`\n"
            "　- 指定した時間後にリマインダーを設定します\n\n"
            "💡 **時間の指定方法:**\n"
            "• `s` - 秒 (例: 30s = 30秒後)\n"
            "• `m` - 分 (例: 5m = 5分後)\n"
            "• `h` - 時間 (例: 2h = 2時間後)\n"
            "• `d` - 日 (例: 1d = 1日後)\n\n"
            "**🕐 絶対時間リマインダー**\n"
            "👉 `/remind_at <日付> <時刻> [メッセージ] [スレッドユーザーメンション]`\n"
            "　- 指定した日時にリマインダーを設定します\n\n"
            "💡 **日付の指定方法:**\n"
            "• `今日`, `明日`, `明後日`\n"
            "• `2024-12-25`, `12/25`, `12-25`\n\n"
            "💡 **時刻の指定方法:**\n"
            "• `14:30` (24時間形式)\n"
            "• `2:30pm`, `9:00am` (12時間形式)\n\n"
            "💡 **スレッドユーザーメンション:**\n"
            "• `True` - スレッド内の過去の返信者もメンション\n"
            "• `False` - 設定者のみメンション (デフォルト)\n"
            "• スレッド以外では無効\n\n"
            "**📋 管理コマンド**\n"
            "👉 `/remind_list`\n"
            "　- 設定中のリマインダー一覧を表示\n\n"
            "📋 **使用例:**\n"
            "**相対時間:**\n"
            "• `/remind 5m 会議の準備` - 5分後に会議の準備をリマインド\n"
            "• `/remind 1h` - 1時間後にデフォルトメッセージでリマインド\n"
            "• `/remind 2d 締切確認` - 2日後に締切確認をリマインド\n\n"
            "**絶対時間:**\n"
            "• `/remind_at 明日 9:00 朝の会議` - 明日の9時に朝の会議をリマインド\n"
            "• `/remind_at 12/25 2:30pm クリスマス` - 12月25日14:30にクリスマスをリマインド\n"
            "• `/remind_at 今日 18:00 帰宅準備` - 今日の18時に帰宅準備をリマインド\n\n"
            "**スレッドメンション:**\n"
            "• `/remind 30m 会議開始 True` - 30分後、スレッド参加者全員にリマインド\n"
            "• `/remind_at 明日 14:00 プレゼン準備 True` - 明日14時、スレッド参加者全員にリマインド\n\n"
            "✅ **新機能:**\n"
            "• Bot再起動後もリマインダーが継続されます\n"
            "• 1分間隔での正確な実行チェック\n"
            "• 設定中のリマインダー一覧表示\n\n"
            "⚠️ **制限事項:**\n"
            "• 最大30日間まで設定可能\n"
            "• 過去の日時は指定できません\n"
            "• スレッドユーザーメンションはスレッド内でのみ有効\n"
            "• 過去50件のメッセージから参加者を取得\n\n"
            "👉 `/remind_help`\n"
            "　- このヘルプを表示します"
        )
        await interaction.response.send_message(response, ephemeral=True)


async def setup(bot):
    await bot.add_cog(ReminderCog(bot))
    await bot.add_cog(ReminderHelp(bot))