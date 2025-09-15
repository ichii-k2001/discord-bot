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
        print("🔄 Initializing ReminderCog...")
        try:
            self.reminder_manager = ReminderManager()
            print("✅ ReminderManager initialized")
        except Exception as e:
            print(f"❌ ReminderManager initialization failed: {e}")
            raise
        
        try:
            if not self.check_reminders.is_running():
                self.check_reminders.start()  # バックグラウンドタスク開始
                print("✅ Background task started")
            else:
                print("⚠️ Background task already running")
        except Exception as e:
            print(f"❌ Background task start failed: {e}")
            # タスク開始に失敗してもCogの読み込みは継続
            pass
        
        print("✅ ReminderCog initialization complete")
    
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
                        f"✅ **リマインダー設定完了**\n\n"
                        f"⏰ **実行時刻:** {time}後\n"
                        f"💬 **メッセージ:** {message}\n"
                        f"📝 **スレッドメンション:** {thread_count}人\n"
                        f"🆔 **ID:** `{target_time.strftime('%m%d%H%M')}` (削除時に使用)"
                    )
                else:
                    await interaction.response.send_message(
                        f"✅ **リマインダー設定完了**\n\n"
                        f"⏰ **実行時刻:** {time}後\n"
                        f"💬 **メッセージ:** {message}\n"
                        f"📝 **スレッドメンション:** なし（他のユーザーが見つかりませんでした）\n"
                        f"🆔 **ID:** `{target_time.strftime('%m%d%H%M')}` (削除時に使用)"
                    )
            else:
                await interaction.response.send_message(
                    f"✅ **リマインダー設定完了**\n\n"
                    f"⏰ **実行時刻:** {time}後\n"
                    f"💬 **メッセージ:** {message}\n"
                    f"🆔 **ID:** `{target_time.strftime('%m%d%H%M')}` (削除時に使用)"
                )
            
            # リマインダーをJSONに保存
            reminder_id = self.reminder_manager.add_reminder(
                user_id=user_id,
                channel_id=channel_id,
                message=message,
                target_time=target_time,
                mention_thread_users=mention_thread_users,
                thread_users=thread_users
            )
            
            # 設定完了メッセージにIDを追加
            short_id = reminder_id[:8]
            if mention_thread_users and hasattr(interaction.channel, 'parent'):
                if thread_users:
                    await interaction.edit_original_response(content=
                        f"✅ **リマインダー設定完了**\n\n"
                        f"⏰ **実行時刻:** {time}後\n"
                        f"💬 **メッセージ:** {message}\n"
                        f"📝 **スレッドメンション:** {len(thread_users)}人\n"
                        f"🆔 **ID:** `{short_id}` (削除時に使用)"
                    )
                else:
                    await interaction.edit_original_response(content=
                        f"✅ **リマインダー設定完了**\n\n"
                        f"⏰ **実行時刻:** {time}後\n"
                        f"💬 **メッセージ:** {message}\n"
                        f"📝 **スレッドメンション:** なし（他のユーザーが見つかりませんでした）\n"
                        f"🆔 **ID:** `{short_id}` (削除時に使用)"
                    )
            else:
                await interaction.edit_original_response(content=
                    f"✅ **リマインダー設定完了**\n\n"
                    f"⏰ **実行時刻:** {time}後\n"
                    f"💬 **メッセージ:** {message}\n"
                    f"🆔 **ID:** `{short_id}` (削除時に使用)"
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
                        f"✅ **リマインダー設定完了**\n\n"
                        f"⏰ **実行時刻:** {formatted_datetime}\n"
                        f"💬 **メッセージ:** {message}\n"
                        f"📝 **スレッドメンション:** {thread_count}人\n"
                        f"🆔 **ID:** 設定中..."
                    )
                else:
                    await interaction.response.send_message(
                        f"✅ **リマインダー設定完了**\n\n"
                        f"⏰ **実行時刻:** {formatted_datetime}\n"
                        f"💬 **メッセージ:** {message}\n"
                        f"📝 **スレッドメンション:** なし（他のユーザーが見つかりませんでした）\n"
                        f"🆔 **ID:** 設定中..."
                    )
            else:
                await interaction.response.send_message(
                    f"✅ **リマインダー設定完了**\n\n"
                    f"⏰ **実行時刻:** {formatted_datetime}\n"
                    f"💬 **メッセージ:** {message}\n"
                    f"🆔 **ID:** 設定中..."
                )
            
            # リマインダーをJSONに保存
            reminder_id = self.reminder_manager.add_reminder(
                user_id=user_id,
                channel_id=channel_id,
                message=message,
                target_time=target_datetime,
                mention_thread_users=mention_thread_users,
                thread_users=thread_users
            )
            
            # 設定完了メッセージにIDを追加
            short_id = reminder_id[:8]
            if mention_thread_users and hasattr(interaction.channel, 'parent'):
                if thread_users:
                    await interaction.edit_original_response(content=
                        f"✅ **リマインダー設定完了**\n\n"
                        f"⏰ **実行時刻:** {formatted_datetime}\n"
                        f"💬 **メッセージ:** {message}\n"
                        f"📝 **スレッドメンション:** {len(thread_users)}人\n"
                        f"🆔 **ID:** `{short_id}` (削除時に使用)"
                    )
                else:
                    await interaction.edit_original_response(content=
                        f"✅ **リマインダー設定完了**\n\n"
                        f"⏰ **実行時刻:** {formatted_datetime}\n"
                        f"💬 **メッセージ:** {message}\n"
                        f"📝 **スレッドメンション:** なし（他のユーザーが見つかりませんでした）\n"
                        f"🆔 **ID:** `{short_id}` (削除時に使用)"
                    )
            else:
                await interaction.edit_original_response(content=
                    f"✅ **リマインダー設定完了**\n\n"
                    f"⏰ **実行時刻:** {formatted_datetime}\n"
                    f"💬 **メッセージ:** {message}\n"
                    f"🆔 **ID:** `{short_id}` (削除時に使用)"
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
                    thread_info = f"📝 スレッド{len(reminder['thread_users'])}人"
                else:
                    thread_info = "👤 個人"
                
                # UUIDの最初の8文字を表示
                short_id = reminder["id"][:8]
                response += (
                    f"**{i}.** `{short_id}`\n"
                    f"⏰ **{formatted_time}** | {thread_info}\n"
                    f"💬 {reminder['message']}\n\n"
                )
            
            if len(user_reminders) > 10:
                response += f"\n... 他 {len(user_reminders) - 10} 件"
            
            response += "\n💡 削除するには `/remind_delete <ID>` を使用してください"
            
            await interaction.response.send_message(response, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ リマインダー一覧取得エラー: {str(e)}", 
                ephemeral=True
            )

    @app_commands.command(name="remind_delete", description="指定したリマインダーを削除します")
    @app_commands.describe(
        reminder_id="削除するリマインダーのID（/remind_listで確認）"
    )
    async def remind_delete(self, interaction: discord.Interaction, reminder_id: str):
        """指定したリマインダーを削除"""
        try:
            reminders = self.reminder_manager.load_reminders()
            user_reminders = [r for r in reminders if r["user_id"] == interaction.user.id]
            
            # 短縮IDまたは完全IDで検索
            target_reminder = None
            for reminder in user_reminders:
                if reminder["id"].startswith(reminder_id) or reminder["id"] == reminder_id:
                    target_reminder = reminder
                    break
            
            if not target_reminder:
                await interaction.response.send_message(
                    f"❌ ID `{reminder_id}` のリマインダーが見つかりません。\n"
                    f"💡 `/remind_list` でIDを確認してください。",
                    ephemeral=True
                )
                return
            
            # リマインダーを削除
            self.reminder_manager.remove_reminder(target_reminder["id"])
            
            target_time = datetime.fromisoformat(target_reminder["target_time"])
            formatted_time = target_time.strftime("%Y年%m月%d日 %H:%M")
            
            await interaction.response.send_message(
                f"✅ リマインダーを削除しました\n"
                f"**時刻:** {formatted_time}\n"
                f"**メッセージ:** {target_reminder['message']}",
                ephemeral=True
            )
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ リマインダー削除エラー: {str(e)}", 
                ephemeral=True
            )

    @app_commands.command(name="remind_clear", description="設定中のリマインダーを全て削除します")
    async def remind_clear(self, interaction: discord.Interaction):
        """設定中のリマインダーを全て削除"""
        try:
            reminders = self.reminder_manager.load_reminders()
            user_reminders = [r for r in reminders if r["user_id"] == interaction.user.id]
            
            if not user_reminders:
                await interaction.response.send_message(
                    "📝 削除するリマインダーがありません", 
                    ephemeral=True
                )
                return
            
            # 確認メッセージを表示
            count = len(user_reminders)
            view = ClearConfirmView(self.reminder_manager, interaction.user.id, count)
            
            await interaction.response.send_message(
                f"⚠️ **確認**\n"
                f"設定中のリマインダー **{count}件** を全て削除しますか？\n"
                f"この操作は取り消せません。",
                view=view,
                ephemeral=True
            )
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ リマインダー全削除エラー: {str(e)}", 
                ephemeral=True
            )


class ReminderHelp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="remind_help", description="リマインダー機能のヘルプを表示します")
    async def help(self, interaction: discord.Interaction):
        response = (
            "**⏰ リマインダー機能**\n\n"
            "**基本コマンド:**\n"
            "• `/remind <時間> [メッセージ]` - 相対時間リマインダー\n"
            "• `/remind_at <日付> <時刻> [メッセージ]` - 絶対時間リマインダー\n"
            "• `/remind_list` - リマインダー一覧表示\n"
            "• `/remind_delete <ID>` - リマインダー削除\n"
            "• `/remind_clear` - 全リマインダー削除\n\n"
            "**時間指定:**\n"
            "• 相対: `5m`, `1h`, `2d` (分/時間/日)\n"
            "• 絶対: `明日 9:00`, `12/25 14:30`\n\n"
            "**使用例:**\n"
            "• `/remind 30m 会議準備` → ID表示\n"
            "• `/remind_at 明日 9:00 朝の会議` → ID表示\n"
            "• `/remind_delete a1b2c3d4` (表示されたIDで削除)\n"
            "• `/remind 1h 休憩 True` (スレッド全員にメンション)\n\n"
            "**特徴:**\n"
            "• スレッド参加者一括メンション対応（過去50件のメッセージから取得）\n"
            "• 最大30日間設定可能"
        )
        await interaction.response.send_message(response, ephemeral=True)


class ClearConfirmView(discord.ui.View):
    def __init__(self, reminder_manager: ReminderManager, user_id: int, count: int):
        super().__init__(timeout=30)
        self.reminder_manager = reminder_manager
        self.user_id = user_id
        self.count = count

    @discord.ui.button(label="削除する", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def confirm_clear(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ この操作は実行できません", ephemeral=True)
            return
        
        try:
            # 全てのリマインダーを取得
            all_reminders = self.reminder_manager.load_reminders()
            # 他のユーザーのリマインダーのみ残す
            other_reminders = [r for r in all_reminders if r["user_id"] != self.user_id]
            # 保存
            self.reminder_manager.save_reminders(other_reminders)
            
            await interaction.response.edit_message(
                content=f"✅ リマインダー **{self.count}件** を全て削除しました",
                view=None
            )
        except Exception as e:
            await interaction.response.edit_message(
                content=f"❌ 削除に失敗しました: {str(e)}",
                view=None
            )

    @discord.ui.button(label="キャンセル", style=discord.ButtonStyle.secondary, emoji="❌")
    async def cancel_clear(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ この操作は実行できません", ephemeral=True)
            return
        
        await interaction.response.edit_message(
            content="❌ リマインダーの全削除をキャンセルしました",
            view=None
        )

    async def on_timeout(self):
        # タイムアウト時にボタンを無効化
        for item in self.children:
            item.disabled = True


async def setup(bot):
    try:
        print("🔄 Setting up ReminderCog...")
        await bot.add_cog(ReminderCog(bot))
        print("✅ ReminderCog added successfully")
        
        print("🔄 Setting up ReminderHelp...")
        await bot.add_cog(ReminderHelp(bot))
        print("✅ ReminderHelp added successfully")
        
        print("✅ Reminder module setup complete")
    except Exception as e:
        print(f"❌ Reminder module setup failed: {e}")
        raise