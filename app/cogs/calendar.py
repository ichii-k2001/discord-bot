import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
import json
import os
from typing import Optional
from app.services.google_calendar import GoogleCalendarService
from app.services.user_settings import UserSettingsService

class CalendarManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.events_file = "data/events.json"
        self.google_calendar = GoogleCalendarService()
        self.user_settings = UserSettingsService()
        self.use_google_calendar = self.google_calendar.is_available()
        self.ensure_data_dir()

    def ensure_data_dir(self):
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(self.events_file):
            with open(self.events_file, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)

    def load_events(self):
        try:
            with open(self.events_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []

    def save_events(self, events):
        with open(self.events_file, "w", encoding="utf-8") as f:
            json.dump(events, f, ensure_ascii=False, indent=2)

    @app_commands.command(name="calendar_add", description="予定を追加します")
    @app_commands.describe(
        title="予定のタイトル",
        date="日付（YYYY-MM-DD形式）",
        time="時刻（HH:MM形式、省略可）",
        description="詳細説明（省略可）"
    )
    async def add_event(self, interaction: discord.Interaction, title: str, date: str, time: Optional[str] = None, description: Optional[str] = None):
        try:
            # 日付の検証
            event_date = datetime.strptime(date, "%Y-%m-%d")
            
            # Googleカレンダー連携が有効な場合
            if self.use_google_calendar:
                google_event = self.google_calendar.create_event(title, date, time, description)
                if google_event:
                    event = {
                        "id": len(self.load_events()) + 1,
                        "title": title,
                        "date": date,
                        "time": time,
                        "description": description,
                        "created_by": str(interaction.user.id),
                        "created_at": datetime.now().isoformat(),
                        "google_event_id": google_event.get("google_event_id"),
                        "html_link": google_event.get("html_link", "")
                    }
                    
                    events = self.load_events()
                    events.append(event)
                    self.save_events(events)
                    
                    time_str = f" {time}" if time else ""
                    desc_str = f"\n📝 {description}" if description else ""
                    link_str = f"\n🔗 [Googleカレンダーで開く]({google_event.get('html_link', '')})" if google_event.get('html_link') else ""
                    
                    response = f"📅 予定を追加しました！（Googleカレンダーと同期済み）\n\n"
                    response += f"**{title}**\n"
                    response += f"📆 {date}{time_str}{desc_str}{link_str}"
                    
                    await interaction.response.send_message(response)
                    return
                else:
                    # Googleカレンダーへの追加に失敗した場合はローカルのみ
                    await interaction.followup.send("⚠️ Googleカレンダーへの追加に失敗しました。ローカルのみに保存します。", ephemeral=True)
            
            # ローカルのみの場合
            event = {
                "id": len(self.load_events()) + 1,
                "title": title,
                "date": date,
                "time": time,
                "description": description,
                "created_by": str(interaction.user.id),
                "created_at": datetime.now().isoformat()
            }
            
            events = self.load_events()
            events.append(event)
            self.save_events(events)
            
            time_str = f" {time}" if time else ""
            desc_str = f"\n📝 {description}" if description else ""
            
            response = f"📅 予定を追加しました！\n\n"
            response += f"**{title}**\n"
            response += f"📆 {date}{time_str}{desc_str}"
            
            await interaction.response.send_message(response)
            
        except ValueError:
            await interaction.response.send_message("⚠️ 日付の形式が正しくありません。YYYY-MM-DD形式で入力してください。", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"⚠️ エラーが発生しました: {str(e)}", ephemeral=True)

    @app_commands.command(name="calendar_list", description="予定一覧を表示します")
    @app_commands.describe(days="何日後まで表示するか（デフォルト: 7日）")
    async def list_events(self, interaction: discord.Interaction, days: Optional[int] = 7):
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild.id) if interaction.guild else "dm"
        
        # Googleカレンダー連携が有効な場合はGoogleから取得
        if self.use_google_calendar:
            google_events = self.google_calendar.get_events(days)
            if google_events:
                upcoming_events = google_events
            else:
                # Googleから取得できない場合はローカルを使用
                events = self.load_events()
                today = datetime.now().date()
                end_date = today + timedelta(days=days)
                
                upcoming_events = []
                for event in events:
                    event_date = datetime.strptime(event["date"], "%Y-%m-%d").date()
                    if today <= event_date <= end_date:
                        upcoming_events.append(event)
        else:
            # ローカルのみの場合
            events = self.load_events()
            today = datetime.now().date()
            end_date = today + timedelta(days=days)
            
            upcoming_events = []
            for event in events:
                event_date = datetime.strptime(event["date"], "%Y-%m-%d").date()
                if today <= event_date <= end_date:
                    upcoming_events.append(event)
        
        # プライバシー設定に基づいてフィルタリング
        upcoming_events = self.user_settings.get_filtered_data(upcoming_events, user_id, guild_id, "calendar")
        
        upcoming_events.sort(key=lambda x: (x["date"], x["time"] or "00:00"))
        
        if not upcoming_events:
            response = f"📅 今後{days}日間の予定はありません。"
        else:
            sync_status = "（Googleカレンダーと同期）" if self.use_google_calendar else ""
            privacy_status = "（プライベートモード）" if self.user_settings.is_private_mode(user_id, guild_id, "calendar") else "（共有モード）"
            response = f"📅 今後{days}日間の予定一覧{sync_status}{privacy_status}\n\n"
            for event in upcoming_events:
                time_str = f" {event['time']}" if event['time'] else ""
                desc_str = f"\n　📝 {event['description']}" if event['description'] and event['description'].strip() else ""
                link_str = f"\n　🔗 [Googleカレンダーで開く]({event['html_link']})" if event.get('html_link') else ""
                response += f"**{event['title']}**\n"
                response += f"　📆 {event['date']}{time_str}{desc_str}{link_str}\n\n"
        
        await interaction.response.send_message(response)

    @app_commands.command(name="calendar_delete", description="予定を削除します")
    @app_commands.describe(event_id="削除する予定のID")
    async def delete_event(self, interaction: discord.Interaction, event_id: int):
        events = self.load_events()
        event_to_delete = None
        
        for i, event in enumerate(events):
            if event["id"] == event_id:
                event_to_delete = events.pop(i)
                break
        
        if event_to_delete:
            self.save_events(events)
            response = f"🗑️ 予定「**{event_to_delete['title']}**」を削除しました。"
        else:
            response = f"⚠️ ID {event_id} の予定が見つかりませんでした。"
        
        await interaction.response.send_message(response)

    @app_commands.command(name="calendar_today", description="今日の予定を表示します")
    async def today_events(self, interaction: discord.Interaction):
        events = self.load_events()
        today = datetime.now().strftime("%Y-%m-%d")
        
        today_events = [event for event in events if event["date"] == today]
        today_events.sort(key=lambda x: x["time"] or "00:00")
        
        if not today_events:
            response = "📅 今日の予定はありません。"
        else:
            response = "📅 今日の予定\n\n"
            for event in today_events:
                time_str = f" {event['time']}" if event['time'] else ""
                desc_str = f"\n　📝 {event['description']}" if event['description'] else ""
                response += f"**{event['title']}**\n"
                response += f"　📆 {event['date']}{time_str}{desc_str}\n\n"
        
        await interaction.response.send_message(response)

    @app_commands.command(name="calendar_sync", description="Googleカレンダーとの同期状態を確認・設定します")
    async def sync_status(self, interaction: discord.Interaction):
        if self.use_google_calendar:
            if self.google_calendar.authenticate():
                response = "✅ Googleカレンダーと連携中です！\n\n"
                response += "📊 **連携状態**: 有効\n"
                response += "🔄 **同期**: 自動\n"
                response += "📅 **カレンダーID**: " + self.google_calendar.calendar_id
            else:
                response = "⚠️ Googleカレンダーの認証に問題があります。\n\n"
                response += "🔧 認証情報を確認してください。"
        else:
            response = "📋 現在はローカルモードで動作中です。\n\n"
            response += "🔧 **Googleカレンダー連携を有効にするには:**\n"
            response += "1. Google Cloud Consoleで認証情報を取得\n"
            response += "2. `credentials.json` をプロジェクトルートに配置\n"
            response += "3. 環境変数 `GOOGLE_CREDENTIALS_PATH` を設定\n"
            response += "4. Botを再起動"
        
        await interaction.response.send_message(response, ephemeral=True)

class CalendarHelp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="calendar_help", description="カレンダー機能のコマンド一覧を表示します")
    async def help(self, interaction: discord.Interaction):
        response = (
            "**📅 カレンダー機能 コマンド一覧**\n\n"
            "👉 `/calendar_add <タイトル> <日付> [時刻] [説明]`\n"
            "　- 予定を追加します（日付: YYYY-MM-DD、時刻: HH:MM）\n\n"
            "👉 `/calendar_list [日数]`\n"
            "　- 予定一覧を表示します（デフォルト: 7日後まで）\n\n"
            "👉 `/calendar_today`\n"
            "　- 今日の予定を表示します\n\n"
            "👉 `/calendar_delete <予定ID>`\n"
            "　- 予定を削除します\n\n"
            "👉 `/calendar_sync`\n"
            "　- Googleカレンダーとの同期状態を確認します\n\n"
            "👉 `/calendar_help`\n"
            "　- このコマンド一覧を表示します\n\n"
            "🔒 **プライバシー設定**\n"
            "👉 `/privacy_mode` - 共有/プライベートモードの切り替え\n"
            "👉 `/privacy_status` - 現在の設定確認\n\n"
            "💡 **使用例:**\n"
            "`/calendar_add 会議 2025-01-15 14:30 プロジェクト進捗確認`\n\n"
            "🔄 **Googleカレンダー連携**: " + ("有効" if self.bot.get_cog('CalendarManager').use_google_calendar else "無効")
        )
        await interaction.response.send_message(response, ephemeral=True)

async def setup(bot):
    await bot.add_cog(CalendarManager(bot))
    await bot.add_cog(CalendarHelp(bot))