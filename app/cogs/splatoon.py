import discord
from discord.ext import commands
from discord import app_commands
import json
import random

def load_weapon_data():
    with open("data/weapon_to_groups.json", "r", encoding="utf-8") as f:
        return json.load(f)

def load_team_patterns():
    with open("data/team_patterns.json", "r", encoding="utf-8") as f:
        return json.load(f)

class WeaponFormation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="splatoon_team", description="チームにブキを編成します（パターン省略時はdefault）")
    @app_commands.describe(pattern="チーム編成パターンの名前（省略するとdefault）")
    async def formation(self, interaction: discord.Interaction, pattern: str = "default"):
        data = load_weapon_data()
        weapon_names = list(data.keys())
        team_patterns = load_team_patterns()

        if pattern in team_patterns:
            selected_structure = team_patterns[pattern]
        else:
            await interaction.response.send_message(f"⚠️ 指定されたパターン **{pattern}** は存在しません。", ephemeral=True)
            return

        used_weapons = set()

        def assign_weapons():
            assigned = []
            for role in selected_structure:
                candidates = [name for name in weapon_names if role in data[name] and name not in used_weapons]
                if not candidates:
                    candidates = [name for name in weapon_names if name not in used_weapons]
                chosen = random.choice(candidates)
                used_weapons.add(chosen)
                assigned.append((chosen, role.replace("role:", "")))
            return assigned

        alpha = assign_weapons()
        bravo = assign_weapons()

        def format_team(team, name):
            lines = [f"{name}"]
            for weapon, role in team:
                lines.append(f"・{weapon}（{role}）")
            return "\n".join(lines)

        response = f"🎲 ブキ編成結果【{pattern}】\n\n"
        response += format_team(alpha, "アルファチーム") + "\n\n"
        response += format_team(bravo, "ブラボチーム")
        await interaction.response.send_message(response)

    @formation.autocomplete("pattern")
    async def pattern_autocomplete(self, interaction: discord.Interaction, current: str):
        patterns = load_team_patterns()
        matches = [p for p in patterns.keys() if current.lower() in p.lower()]
        return [app_commands.Choice(name=m, value=m) for m in matches[:25]]

class WeaponLookup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.weapon_data = load_weapon_data()

    @app_commands.command(name="splatoon_weapon", description="指定したブキのロールとタイプを表示します")
    @app_commands.describe(weapon_name="調べたいブキ名を入力してください")
    async def lookup_weapon(self, interaction: discord.Interaction, weapon_name: str):
        data = self.weapon_data
        if weapon_name in data:
            roles = [entry for entry in data[weapon_name] if entry.startswith("role:")]
            types = [entry for entry in data[weapon_name] if entry.startswith("type:")]
            response = f"🔎 **{weapon_name}** の情報\n\n"
            response += f"🪪 **Role:** {'、'.join(roles)}\n"
            response += f"📦 **Type:** {'、'.join(types)}"
        else:
            response = f"⚠️ ブキ名 **{weapon_name}** は見つかりませんでした。"
        await interaction.response.send_message(response, ephemeral=True)

    @lookup_weapon.autocomplete("weapon_name")
    async def weapon_autocomplete(self, interaction: discord.Interaction, current: str):
        data = load_weapon_data()
        matches = [w for w in data.keys() if current.lower() in w.lower()]
        return [app_commands.Choice(name=w, value=w) for w in matches[:25]]

    @app_commands.command(name="splatoon_role", description="指定したロールに含まれる全ブキを表示します")
    @app_commands.describe(role_name="調べたいロール名（例: 前衛キル特化ブキ）")
    async def list_by_role(self, interaction: discord.Interaction, role_name: str):
        target_role = f"role:{role_name}"
        data = self.weapon_data
        matches = [name for name, tags in data.items() if target_role in tags]
        if matches:
            response = f"🔎 ロール **{role_name}** に該当するブキ一覧（{len(matches)}個）:\n" + "\n".join(f"・{m}" for m in matches)
        else:
            response = f"⚠️ ロール **{role_name}** に該当するブキは見つかりませんでした。"
        await interaction.response.send_message(response, ephemeral=True)

    @list_by_role.autocomplete("role_name")
    async def role_autocomplete(self, interaction: discord.Interaction, current: str):
        data = self.weapon_data
        all_roles = set()
        for tags in data.values():
            all_roles.update(tag.replace("role:", "") for tag in tags if tag.startswith("role:"))
        matches = [r for r in all_roles if current.lower() in r.lower()]
        return [app_commands.Choice(name=r, value=r) for r in sorted(matches)[:25]]

    @app_commands.command(name="splatoon_pattern", description="編成パターンの一覧または詳細を表示します")
    @app_commands.describe(pattern="（オプション）表示したいパターン名")
    async def show_pattern(self, interaction: discord.Interaction, pattern: str = None):
        patterns = load_team_patterns()
        if pattern:
            if pattern in patterns:
                roles = [r.replace("role:", "") for r in patterns[pattern]]
                response = f"📋 パターン **{pattern}** の内容:\n" + "\n".join(roles)
            else:
                response = f"⚠️ パターン **{pattern}** は見つかりませんでした。"
        else:
            response = "📋 利用可能な編成パターン一覧:\n" + "\n".join(f"・{name}" for name in patterns.keys())
        await interaction.response.send_message(response, ephemeral=True)

    @show_pattern.autocomplete("pattern")
    async def pattern_autocomplete(self, interaction: discord.Interaction, current: str):
        patterns = load_team_patterns()
        matches = [p for p in patterns.keys() if current.lower() in p.lower()]
        return [app_commands.Choice(name=m, value=m) for m in matches[:25]]

class SplatoonHelp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="splatoon_help", description="スプラトゥーン機能のコマンド一覧を表示します")
    async def help(self, interaction: discord.Interaction):
        response = (
            "**🎮 スプラトゥーン機能 コマンド一覧**\n\n"
            "👉 `/splatoon_team [pattern]`\n"
            "　- チームごとにランダムなブキを編成します（pattern省略でdefault）\n\n"
            "👉 `/splatoon_weapon <ブキ名>`\n"
            "　- 指定したブキのロールとタイプを表示します（補完あり）\n\n"
            "👉 `/splatoon_role <ロール名>`\n"
            "　- 指定したロールに属するブキをすべて表示します（補完あり）\n\n"
            "👉 `/splatoon_pattern [パターン名]`\n"
            "　- 登録済みの編成パターンを確認できます（補完あり）\n\n"
            "👉 `/splatoon_help`\n"
            "　- このコマンド一覧を表示します"
        )
        await interaction.response.send_message(response, ephemeral=True)

async def setup(bot):
    await bot.add_cog(WeaponFormation(bot))
    await bot.add_cog(WeaponLookup(bot))
    await bot.add_cog(SplatoonHelp(bot))