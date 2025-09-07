import json
import os
from typing import Dict, Optional

class UserSettingsService:
    def __init__(self):
        self.settings_file = "data/user_settings.json"
        self.ensure_data_dir()

    def ensure_data_dir(self):
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(self.settings_file):
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False, indent=2)

    def load_settings(self) -> Dict:
        try:
            with open(self.settings_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}

    def save_settings(self, settings: Dict):
        with open(self.settings_file, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)

    def get_user_setting(self, user_id: str, guild_id: str, feature: str, default: str = "shared") -> str:
        """ユーザーの設定を取得"""
        settings = self.load_settings()
        key = f"{guild_id}:{user_id}"
        
        if key in settings and feature in settings[key]:
            return settings[key][feature]
        
        return default

    def set_user_setting(self, user_id: str, guild_id: str, feature: str, mode: str):
        """ユーザーの設定を保存"""
        settings = self.load_settings()
        key = f"{guild_id}:{user_id}"
        
        if key not in settings:
            settings[key] = {}
        
        settings[key][feature] = mode
        self.save_settings(settings)

    def get_privacy_mode(self, user_id: str, guild_id: str, feature: str) -> str:
        """プライバシーモードを取得（shared/private）"""
        return self.get_user_setting(user_id, guild_id, feature, "shared")

    def is_private_mode(self, user_id: str, guild_id: str, feature: str) -> bool:
        """プライベートモードかどうかを判定"""
        return self.get_privacy_mode(user_id, guild_id, feature) == "private"

    def get_filtered_data(self, data: list, user_id: str, guild_id: str, feature: str) -> list:
        """プライバシー設定に基づいてデータをフィルタリング"""
        if self.is_private_mode(user_id, guild_id, feature):
            # プライベートモード：自分のデータのみ
            return [item for item in data if item.get('created_by') == user_id]
        else:
            # 共有モード：全データ
            return data