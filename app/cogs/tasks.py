import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
import json
import os
from typing import Optional
from app.services.google_sheets import GoogleSheetsService


class TaskManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tasks_file = "data/tasks.json"
        self.google_sheets = GoogleSheetsService()

        self.use_google_sheets = self.google_sheets.is_available()
        self.ensure_data_dir()

    def ensure_data_dir(self):
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(self.tasks_file):
            with open(self.tasks_file, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)

    def load_tasks(self):
        try:
            with open(self.tasks_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []

    def save_tasks(self, tasks):
        with open(self.tasks_file, "w", encoding="utf-8") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)

    @app_commands.command(name="task_add", description="タスクを追加します")
    @app_commands.describe(
        title="タスクのタイトル",
        due_date="期限（YYYY-MM-DD形式、省略可）",
        priority="優先度（high/medium/low、デフォルト: medium）",
        description="詳細説明（省略可）"
    )
    @app_commands.choices(priority=[
        app_commands.Choice(name="高", value="high"),
        app_commands.Choice(name="中", value="medium"),
        app_commands.Choice(name="低", value="low")
    ])
    async def add_task(self, interaction: discord.Interaction, title: str, due_date: Optional[str] = None, priority: Optional[str] = "medium", description: Optional[str] = None):
        try:
            # 期限の検証
            if due_date:
                datetime.strptime(due_date, "%Y-%m-%d")
            
            # Googleスプレッドシート連携が有効な場合
            if self.use_google_sheets:
                task_id = self.google_sheets.add_task(
                    title=title,
                    due_date=due_date,
                    priority=priority,
                    description=description,
                    created_by=str(interaction.user.id)
                )
                
                if task_id:
                    priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}
                    due_str = f"\n⏰ 期限: {due_date}" if due_date else ""
                    desc_str = f"\n📝 {description}" if description else ""
                    sheet_url = self.google_sheets.get_sheet_url()
                    link_str = f"\n🔗 [スプレッドシートで開く]({sheet_url})" if sheet_url else ""
                    
                    response = f"✅ タスクを追加しました！（Googleスプレッドシートと同期済み）\n\n"
                    response += f"**{title}** {priority_emoji.get(priority, '🟡')}\n"
                    response += f"🆔 ID: {task_id}{due_str}{desc_str}{link_str}"
                    
                    await interaction.response.send_message(response)
                    return
                else:
                    # Googleスプレッドシートへの追加に失敗した場合はローカルのみ
                    await interaction.followup.send("⚠️ Googleスプレッドシートへの追加に失敗しました。ローカルのみに保存します。", ephemeral=True)
            
            # ローカルのみの場合
            task = {
                "id": len(self.load_tasks()) + 1,
                "title": title,
                "description": description,
                "due_date": due_date,
                "priority": priority,
                "status": "pending",
                "created_by": str(interaction.user.id),
                "created_at": datetime.now().isoformat(),
                "completed_at": None
            }
            
            tasks = self.load_tasks()
            tasks.append(task)
            self.save_tasks(tasks)
            
            priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}
            due_str = f"\n⏰ 期限: {due_date}" if due_date else ""
            desc_str = f"\n📝 {description}" if description else ""
            
            response = f"✅ タスクを追加しました！\n\n"
            response += f"**{title}** {priority_emoji.get(priority, '🟡')}\n"
            response += f"🆔 ID: {task['id']}{due_str}{desc_str}"
            
            await interaction.response.send_message(response)
            
        except ValueError:
            await interaction.response.send_message("⚠️ 日付の形式が正しくありません。YYYY-MM-DD形式で入力してください。", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"⚠️ エラーが発生しました: {str(e)}", ephemeral=True)

    @app_commands.command(name="task_list", description="タスク一覧を表示します")
    @app_commands.describe(
        status="表示するタスクの状態（all/pending/completed、デフォルト: pending）",
        priority="表示する優先度（all/high/medium/low、デフォルト: all）"
    )
    @app_commands.choices(
        status=[
            app_commands.Choice(name="すべて", value="all"),
            app_commands.Choice(name="未完了", value="pending"),
            app_commands.Choice(name="完了済み", value="completed")
        ],
        priority=[
            app_commands.Choice(name="すべて", value="all"),
            app_commands.Choice(name="高", value="high"),
            app_commands.Choice(name="中", value="medium"),
            app_commands.Choice(name="低", value="low")
        ]
    )
    async def list_tasks(self, interaction: discord.Interaction, status: Optional[str] = "pending", priority: Optional[str] = "all"):
        # Googleスプレッドシート連携が有効な場合はGoogleから取得
        if self.use_google_sheets:
            filtered_tasks = self.google_sheets.get_tasks(status, priority)
        else:
            # ローカルのみの場合
            tasks = self.load_tasks()
            
            # フィルタリング
            filtered_tasks = []
            for task in tasks:
                if status != "all" and task["status"] != status:
                    continue
                if priority != "all" and task["priority"] != priority:
                    continue
                filtered_tasks.append(task)
        

        
        # ソート（優先度 > 期限 > 作成日時）
        priority_order = {"high": 0, "medium": 1, "low": 2}
        filtered_tasks.sort(key=lambda x: (
            priority_order.get(x["priority"], 1),
            x["due_date"] or "9999-12-31",
            x["created_at"]
        ))
        
        if not filtered_tasks:
            response = "📋 該当するタスクはありません。"
        else:
            status_text = {"all": "すべて", "pending": "未完了", "completed": "完了済み"}
            priority_text = {"all": "すべて", "high": "高", "medium": "中", "low": "低"}
            sync_status = "（Googleスプレッドシートと同期）" if self.use_google_sheets else ""
            response = f"📋 タスク一覧（状態: {status_text.get(status, status)}, 優先度: {priority_text.get(priority, priority)}）{sync_status}\n\n"
            
            for task in filtered_tasks:
                priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}
                status_emoji = "✅" if task["status"] == "completed" else "⏳"
                due_str = f" ⏰{task['due_date']}" if task['due_date'] else ""
                desc_str = f"\n　📝 {task['description']}" if task['description'] else ""
                
                # 期限チェック
                overdue_str = ""
                if task['due_date'] and task['status'] == 'pending':
                    due_date = datetime.strptime(task['due_date'], "%Y-%m-%d").date()
                    if due_date < datetime.now().date():
                        overdue_str = " ⚠️期限切れ"
                
                sheet_link = ""
                if self.use_google_sheets:
                    sheet_url = self.google_sheets.get_sheet_url()
                    sheet_link = f"\n　🔗 [スプレッドシートで開く]({sheet_url})" if sheet_url else ""
                
                response += f"{status_emoji} **{task['title']}** {priority_emoji.get(task['priority'], '🟡')}\n"
                response += f"　🆔 ID: {task['id']}{due_str}{overdue_str}{desc_str}{sheet_link}\n\n"
        
        await interaction.response.send_message(response)

    @app_commands.command(name="task_complete", description="タスクを完了にします")
    @app_commands.describe(task_id="完了するタスクのID")
    async def complete_task(self, interaction: discord.Interaction, task_id: int):
        # Googleスプレッドシート連携が有効な場合
        if self.use_google_sheets:
            # まずタスクが存在するかチェック
            tasks = self.google_sheets.get_tasks()
            task_to_complete = None
            
            for task in tasks:
                if task["id"] == task_id:
                    task_to_complete = task
                    break
            
            if not task_to_complete:
                await interaction.response.send_message(f"⚠️ ID {task_id} のタスクが見つかりませんでした。", ephemeral=True)
                return
            
            if task_to_complete["status"] == "completed":
                await interaction.response.send_message(f"⚠️ タスク「**{task_to_complete['title']}**」は既に完了済みです。", ephemeral=True)
                return
            
            # ステータスを更新
            if self.google_sheets.update_task_status(task_id, "completed"):
                response = f"🎉 タスク「**{task_to_complete['title']}**」を完了しました！"
                await interaction.response.send_message(response)
            else:
                await interaction.response.send_message("⚠️ タスクの完了処理に失敗しました。", ephemeral=True)
        else:
            # ローカルのみの場合
            tasks = self.load_tasks()
            task_found = False
            
            for task in tasks:
                if task["id"] == task_id:
                    if task["status"] == "completed":
                        await interaction.response.send_message(f"⚠️ タスク「**{task['title']}**」は既に完了済みです。", ephemeral=True)
                        return
                    
                    task["status"] = "completed"
                    task["completed_at"] = datetime.now().isoformat()
                    task_found = True
                    self.save_tasks(tasks)
                    
                    response = f"🎉 タスク「**{task['title']}**」を完了しました！"
                    await interaction.response.send_message(response)
                    break
            
            if not task_found:
                await interaction.response.send_message(f"⚠️ ID {task_id} のタスクが見つかりませんでした。", ephemeral=True)

    @app_commands.command(name="task_delete", description="タスクを削除します")
    @app_commands.describe(task_id="削除するタスクのID")
    async def delete_task(self, interaction: discord.Interaction, task_id: int):
        # Googleスプレッドシート連携が有効な場合
        if self.use_google_sheets:
            # まずタスクが存在するかチェック
            tasks = self.google_sheets.get_tasks()
            task_to_delete = None
            
            for task in tasks:
                if task["id"] == task_id:
                    task_to_delete = task
                    break
            
            if not task_to_delete:
                await interaction.response.send_message(f"⚠️ ID {task_id} のタスクが見つかりませんでした。", ephemeral=True)
                return
            
            # タスクを削除
            if self.google_sheets.delete_task(task_id):
                response = f"🗑️ タスク「**{task_to_delete['title']}**」を削除しました。"
                await interaction.response.send_message(response)
            else:
                await interaction.response.send_message("⚠️ タスクの削除に失敗しました。", ephemeral=True)
        else:
            # ローカルのみの場合
            tasks = self.load_tasks()
            task_to_delete = None
            
            for i, task in enumerate(tasks):
                if task["id"] == task_id:
                    task_to_delete = tasks.pop(i)
                    break
            
            if task_to_delete:
                self.save_tasks(tasks)
                response = f"🗑️ タスク「**{task_to_delete['title']}**」を削除しました。"
            else:
                response = f"⚠️ ID {task_id} のタスクが見つかりませんでした。"
            
            await interaction.response.send_message(response)

    @app_commands.command(name="task_due", description="期限が近いタスクを表示します")
    @app_commands.describe(days="何日以内の期限を表示するか（デフォルト: 3日）")
    async def due_tasks(self, interaction: discord.Interaction, days: Optional[int] = 3):
        # Googleスプレッドシート連携が有効な場合はGoogleから取得
        if self.use_google_sheets:
            tasks = self.google_sheets.get_tasks(status="pending")
        else:
            tasks = self.load_tasks()
        today = datetime.now().date()
        target_date = today + timedelta(days=days)
        
        due_tasks = []
        overdue_tasks = []
        
        for task in tasks:
            if task["status"] == "pending" and task["due_date"]:
                due_date = datetime.strptime(task["due_date"], "%Y-%m-%d").date()
                if due_date < today:
                    overdue_tasks.append(task)
                elif due_date <= target_date:
                    due_tasks.append(task)
        
        response = f"⏰ 期限確認（{days}日以内）\n\n"
        
        if overdue_tasks:
            response += "🚨 **期限切れタスク**\n"
            for task in overdue_tasks:
                priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}
                response += f"　⚠️ **{task['title']}** {priority_emoji.get(task['priority'], '🟡')}\n"
                response += f"　　🆔 ID: {task['id']} ⏰ {task['due_date']}\n"
            response += "\n"
        
        if due_tasks:
            response += f"📅 **{days}日以内の期限**\n"
            due_tasks.sort(key=lambda x: x["due_date"])
            for task in due_tasks:
                priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}
                response += f"　📌 **{task['title']}** {priority_emoji.get(task['priority'], '🟡')}\n"
                response += f"　　🆔 ID: {task['id']} ⏰ {task['due_date']}\n"
        
        if not overdue_tasks and not due_tasks:
            response += "✨ 期限が近いタスクはありません！"
        
        await interaction.response.send_message(response)

    @app_commands.command(name="task_sync", description="Googleスプレッドシートとの同期状態を確認・設定します")
    async def sync_status(self, interaction: discord.Interaction):
        if self.use_google_sheets:
            if self.google_sheets.authenticate():
                response = "✅ Googleスプレッドシートと連携中です！\n\n"
                response += "📊 **連携状態**: 有効\n"
                response += "🔄 **同期**: 自動\n"
                response += f"📋 **スプレッドシートID**: {self.google_sheets.spreadsheet_id}\n"
                response += f"📄 **シート名**: {self.google_sheets.sheet_name}\n"
                
                sheet_url = self.google_sheets.get_sheet_url()
                if sheet_url:
                    response += f"🔗 [スプレッドシートを開く]({sheet_url})"
            else:
                response = "⚠️ Googleスプレッドシートの認証に問題があります。\n\n"
                response += "🔧 認証情報を確認してください。"
        else:
            response = "📋 現在はローカルモードで動作中です。\n\n"
            response += "🔧 **Googleスプレッドシート連携を有効にするには:**\n"
            response += "1. Google Cloud Consoleで認証情報を取得\n"
            response += "2. `credentials.json` をプロジェクトルートに配置\n"
            response += "3. 環境変数を設定:\n"
            response += "   - `GOOGLE_CREDENTIALS_PATH=credentials.json`\n"
            response += "   - `GOOGLE_SPREADSHEET_ID=your_spreadsheet_id`\n"
            response += "   - `GOOGLE_SHEET_NAME=Tasks` (オプション)\n"
            response += "4. Botを再起動"
        
        await interaction.response.send_message(response, ephemeral=True)

class TaskHelp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="task_help", description="タスク管理機能のコマンド一覧を表示します")
    async def help(self, interaction: discord.Interaction):
        response = (
            "**📋 タスク管理機能 コマンド一覧**\n\n"
            "👉 `/task_add <タイトル> [期限] [優先度] [説明]`\n"
            "　- タスクを追加します（期限: YYYY-MM-DD、優先度: high/medium/low）\n\n"
            "👉 `/task_list [状態] [優先度]`\n"
            "　- タスク一覧を表示します（状態: all/pending/completed）\n\n"
            "👉 `/task_complete <タスクID>`\n"
            "　- タスクを完了にします\n\n"
            "👉 `/task_delete <タスクID>`\n"
            "　- タスクを削除します\n\n"
            "👉 `/task_due [日数]`\n"
            "　- 期限が近いタスクを表示します（デフォルト: 3日以内）\n\n"
            "👉 `/task_sync`\n"
            "　- Googleスプレッドシートとの同期状態を確認します\n\n"
            "👉 `/task_help`\n"
            "　- このコマンド一覧を表示します\n\n"

            "💡 **使用例:**\n"
            "`/task_add レポート作成 2025-01-20 high 月次売上レポートの作成`\n\n"
            "🔄 **Googleスプレッドシート連携**: " + ("有効" if self.bot.get_cog('TaskManager').use_google_sheets else "無効")
        )
        await interaction.response.send_message(response, ephemeral=True)

async def setup(bot):
    await bot.add_cog(TaskManager(bot))
    await bot.add_cog(TaskHelp(bot))