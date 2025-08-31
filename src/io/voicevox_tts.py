import asyncio
import tempfile
import os
import hashlib
import aiohttp
from typing import AsyncIterator
from ..core.config import TTSConfig
from loguru import logger


class VoicevoxTTS:
    def __init__(self, config: TTSConfig):
        self.config = config
        self.base_url = "http://127.0.0.1:50021"  # VOICEVOX Engine URL
        self.speaker_id = 3  # ずんだもん（ノーマル）
        self.audio_cache = {}  # 音声キャッシュ
        self.session = None  # aiohttp session
        self.available = False
        
        # 非同期初期化は後で行う
        asyncio.create_task(self._async_init())

    async def _async_init(self):
        """非同期初期化"""
        try:
            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10))
            async with self.session.get(f"{self.base_url}/version") as response:
                if response.status == 200:
                    self.available = True
                    logger.info("VOICEVOX TTS initialized with aiohttp")
                else:
                    logger.warning("VOICEVOX Engine not available")
        except Exception as e:
            logger.warning(f"VOICEVOX Engine connection failed: {e}")
            if self.session:
                await self.session.close()
                self.session = None

    async def speak_sentences(self, sentences: AsyncIterator[str]):
        """文ごとにTTS合成して再生（高速化版）"""
        if not self.available or not self.session:
            logger.warning("VOICEVOX not available, showing text output")
            async for sentence in sentences:
                if sentence.strip():
                    print(f"[VOICEVOX] {sentence.strip()}")
            return

        # 文を収集
        sentence_list = []
        async for sentence in sentences:
            if sentence.strip():
                sentence_list.append(sentence.strip())
        
        if not sentence_list:
            return
            
        # 並列で音声合成
        tasks = [self._synthesize_cached(text) for text in sentence_list]
        audio_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 順番に再生
        for i, (text, result) in enumerate(zip(sentence_list, audio_results)):
            if isinstance(result, Exception):
                logger.error(f"TTS failed for '{text}': {result}")
                continue
                
            if result:  # 音声データがある場合
                await self._play_audio_data(result)
                
            # 文間の間隔（最後の文以外）
            if i < len(sentence_list) - 1:
                await asyncio.sleep(self.config.sentence_pause_ms / 1000.0)

    async def _synthesize_cached(self, text: str) -> bytes:
        """キャッシュ付き音声合成"""
        # キャッシュキー生成
        cache_key = hashlib.md5(f"{text}:{self.speaker_id}".encode()).hexdigest()
        
        if cache_key in self.audio_cache:
            logger.debug(f"Cache hit for: {text}")
            return self.audio_cache[cache_key]
        
        try:
            # 音声クエリ生成
            async with self.session.post(
                f"{self.base_url}/audio_query",
                params={"text": text, "speaker": self.speaker_id}
            ) as response:
                if response.status != 200:
                    logger.error(f"Audio query failed: {response.status}")
                    return b''
                audio_query = await response.json()
            
            # 音声合成
            async with self.session.post(
                f"{self.base_url}/synthesis",
                params={"speaker": self.speaker_id},
                json=audio_query
            ) as response:
                if response.status != 200:
                    logger.error(f"Synthesis failed: {response.status}")
                    return b''
                audio_data = await response.read()
            
            # キャッシュに保存（最大50個まで）
            if len(self.audio_cache) >= 50:
                # 最古のエントリを削除
                oldest_key = next(iter(self.audio_cache))
                del self.audio_cache[oldest_key]
            
            self.audio_cache[cache_key] = audio_data
            logger.debug(f"Cached audio for: {text}")
            return audio_data
            
        except Exception as e:
            logger.error(f"Synthesis error: {e}")
            return b''

    async def _play_audio_data(self, audio_data: bytes):
        """音声データを直接再生"""
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                tmp_file.write(audio_data)
                wav_path = tmp_file.name
            
            # 再生
            process = await asyncio.create_subprocess_exec(
                "afplay", wav_path,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.communicate()
            
            # 一時ファイル削除
            try:
                os.unlink(wav_path)
            except:
                pass
                
        except Exception as e:
            logger.error(f"Audio playback error: {e}")


    async def close(self):
        """リソースクリーンアップ"""
        if self.session:
            await self.session.close()
            self.session = None
            logger.debug("VOICEVOX TTS session closed")
    
    def __del__(self):
        """デストラクタでセッションクローズ"""
        if self.session and not self.session.closed:
            try:
                asyncio.create_task(self.session.close())
            except:
                pass