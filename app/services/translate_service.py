import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor
from googletrans import Translator

class TranslateService:
    def __init__(self):
        self.translator = Translator()
        self.cache = {}  # 翻訳結果キャッシュ
        self.user_usage = {}  # ユーザー使用統計
        self.stats = {
            'total_translations': 0,
            'daily_translations': {},
            'popular_languages': {},
            'average_response_time': 0
        }
        
        # 設定
        self.MAX_TEXT_LENGTH = 300
        self.CACHE_SIZE = 1000
        self.RATE_LIMITS = {
            'per_minute': 3,
            'per_hour': 20,
            'per_day': 50
        }
        
        # 対応言語
        self.LANGUAGES = {
            'ja': {'name': '日本語', 'flag': '🇯🇵'},
            'en': {'name': 'English', 'flag': '🇺🇸'},
            'zh': {'name': '中文', 'flag': '🇨🇳'},
            'fr': {'name': 'Français', 'flag': '🇫🇷'},
            'de': {'name': 'Deutsch', 'flag': '🇩🇪'},
            'es': {'name': 'Español', 'flag': '🇪🇸'}
        }

    def is_valid_language(self, lang_code: str) -> bool:
        """言語コードの有効性をチェック"""
        return lang_code.lower() in self.LANGUAGES

    def get_language_info(self, lang_code: str) -> Dict[str, str]:
        """言語情報を取得"""
        return self.LANGUAGES.get(lang_code.lower(), {})

    def check_rate_limit(self, user_id: int) -> Tuple[bool, str]:
        """レート制限をチェック"""
        now = datetime.now()
        user_key = str(user_id)
        
        if user_key not in self.user_usage:
            self.user_usage[user_key] = {
                'minute': [],
                'hour': [],
                'day': []
            }
        
        usage = self.user_usage[user_key]
        
        # 古い記録を削除
        usage['minute'] = [t for t in usage['minute'] if now - t < timedelta(minutes=1)]
        usage['hour'] = [t for t in usage['hour'] if now - t < timedelta(hours=1)]
        usage['day'] = [t for t in usage['day'] if now - t < timedelta(days=1)]
        
        # 制限チェック
        if len(usage['minute']) >= self.RATE_LIMITS['per_minute']:
            return False, f"1分間の制限に達しました ({self.RATE_LIMITS['per_minute']}回/分)"
        if len(usage['hour']) >= self.RATE_LIMITS['per_hour']:
            return False, f"1時間の制限に達しました ({self.RATE_LIMITS['per_hour']}回/時)"
        if len(usage['day']) >= self.RATE_LIMITS['per_day']:
            return False, f"1日の制限に達しました ({self.RATE_LIMITS['per_day']}回/日)"
        
        return True, ""

    def record_usage(self, user_id: int):
        """使用記録を追加"""
        now = datetime.now()
        user_key = str(user_id)
        
        if user_key not in self.user_usage:
            self.user_usage[user_key] = {
                'minute': [],
                'hour': [],
                'day': []
            }
        
        usage = self.user_usage[user_key]
        usage['minute'].append(now)
        usage['hour'].append(now)
        usage['day'].append(now)

    def get_user_stats(self, user_id: int) -> Dict[str, int]:
        """ユーザーの使用統計を取得"""
        user_key = str(user_id)
        if user_key not in self.user_usage:
            return {'daily': 0, 'hourly': 0}
        
        now = datetime.now()
        usage = self.user_usage[user_key]
        
        # 古い記録を削除してカウント
        daily_count = len([t for t in usage['day'] if now - t < timedelta(days=1)])
        hourly_count = len([t for t in usage['hour'] if now - t < timedelta(hours=1)])
        
        return {'daily': daily_count, 'hourly': hourly_count}

    def get_cache_key(self, text: str, target_lang: str) -> str:
        """キャッシュキーを生成"""
        return f"{text.lower().strip()}:{target_lang.lower()}"

    def get_cached_translation(self, text: str, target_lang: str) -> Optional[str]:
        """キャッシュから翻訳結果を取得"""
        cache_key = self.get_cache_key(text, target_lang)
        return self.cache.get(cache_key)

    def cache_translation(self, text: str, target_lang: str, result: str):
        """翻訳結果をキャッシュ"""
        if len(self.cache) >= self.CACHE_SIZE:
            # 古いキャッシュを削除（簡単なLRU）
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        
        cache_key = self.get_cache_key(text, target_lang)
        self.cache[cache_key] = result

    async def translate_text(self, text: str, target_lang: str, user_id: int) -> Dict:
        """テキストを翻訳"""
        start_time = time.time()
        
        # 入力検証
        if len(text) > self.MAX_TEXT_LENGTH:
            return {
                'success': False,
                'error': f'テキストが長すぎます (最大{self.MAX_TEXT_LENGTH}文字)',
                'error_type': 'text_too_long'
            }
        
        if not self.is_valid_language(target_lang):
            return {
                'success': False,
                'error': f'無効な言語コードです。対応言語: {", ".join(self.LANGUAGES.keys())}',
                'error_type': 'invalid_language'
            }
        
        # レート制限チェック
        can_proceed, limit_message = self.check_rate_limit(user_id)
        if not can_proceed:
            return {
                'success': False,
                'error': f'🚫 {limit_message}',
                'error_type': 'rate_limit'
            }
        
        # キャッシュチェック
        cached_result = self.get_cached_translation(text, target_lang)
        if cached_result:
            self.record_usage(user_id)
            return {
                'success': True,
                'original_text': text,
                'translated_text': cached_result,
                'target_lang': target_lang,
                'source_lang': 'auto',
                'cached': True,
                'process_time': time.time() - start_time
            }
        
        try:
            # 非同期で翻訳実行
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                result = await asyncio.wait_for(
                    loop.run_in_executor(
                        executor, 
                        self._translate_sync, 
                        text, 
                        target_lang
                    ),
                    timeout=8.0
                )
            
            # 成功時の処理
            self.record_usage(user_id)
            self.cache_translation(text, target_lang, result.text)
            self._update_stats(target_lang, time.time() - start_time)
            
            return {
                'success': True,
                'original_text': text,
                'translated_text': result.text,
                'target_lang': target_lang,
                'source_lang': result.src,
                'cached': False,
                'process_time': time.time() - start_time
            }
            
        except asyncio.TimeoutError:
            return {
                'success': False,
                'error': '⏱️ 翻訳処理がタイムアウトしました。テキストを短くして再試行してください',
                'error_type': 'timeout'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'🔧 翻訳サービスエラー: {str(e)}',
                'error_type': 'api_error'
            }

    def _translate_sync(self, text: str, target_lang: str):
        """同期翻訳処理（ThreadPoolExecutor用）"""
        return self.translator.translate(text, dest=target_lang)

    def _update_stats(self, target_lang: str, process_time: float):
        """統計情報を更新"""
        self.stats['total_translations'] += 1
        
        # 人気言語統計
        if target_lang not in self.stats['popular_languages']:
            self.stats['popular_languages'][target_lang] = 0
        self.stats['popular_languages'][target_lang] += 1
        
        # 平均処理時間更新
        total = self.stats['total_translations']
        current_avg = self.stats['average_response_time']
        self.stats['average_response_time'] = (current_avg * (total - 1) + process_time) / total

    def get_global_stats(self) -> Dict:
        """グローバル統計を取得"""
        return self.stats.copy()