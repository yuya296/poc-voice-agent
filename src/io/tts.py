import asyncio
import tempfile
import os
import wave
from typing import AsyncIterator
from ..core.config import TTSConfig
from loguru import logger

try:
    from piper import PiperVoice
    PIPER_AVAILABLE = True
except ImportError:
    PIPER_AVAILABLE = False
    logger.warning("piper-tts not available, install with: uv add piper-tts")


class PiperTTS:
    def __init__(self, config: TTSConfig):
        self.config = config
        self.voice = None
        
        if PIPER_AVAILABLE:
            try:
                # Python版Piperを初期化
                model_path = os.path.join(config.voice_dir, "model.onnx")
                config_path = os.path.join(config.voice_dir, "model.json")
                
                if os.path.exists(model_path) and os.path.exists(config_path):
                    self.voice = PiperVoice.load(model_path, config_path)
                    logger.info(f"Piper TTS (Python) initialized: {config.voice_dir}")
                else:
                    logger.warning(f"Piper model files not found in: {config.voice_dir}")
                    logger.info("Download models first. See README.md for instructions.")
            except Exception as e:
                logger.error(f"Failed to initialize Piper TTS: {e}")
        else:
            logger.warning("Piper TTS not available")

    async def speak_sentences(self, sentences: AsyncIterator[str]):
        """文ごとにTTS合成して再生"""
        if self.voice is None:
            logger.warning("Piper voice not available, skipping TTS")
            async for sentence in sentences:  # ストリームを消費
                print(f"[TTS] {sentence}", end='', flush=True)
            print()
            return

        async for sentence in sentences:
            if not sentence.strip():
                continue
                
            try:
                await self._speak_text(sentence.strip())
                # 文間の間隔
                await asyncio.sleep(self.config.sentence_pause_ms / 1000.0)
                
            except Exception as e:
                logger.error(f"TTS failed for sentence '{sentence}': {e}")

    async def _speak_text(self, text: str):
        """単一テキストをTTS合成して再生"""
        if self.voice is None:
            print(f"[TTS] {text}")
            return
            
        try:
            # 音声合成（非同期実行）
            audio_data = await asyncio.get_event_loop().run_in_executor(
                None, self._synthesize_audio, text
            )
            
            if audio_data:
                # 一時WAVファイルに保存して再生
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                    wav_path = tmp_file.name
                
                # WAVファイルに書き込み
                with wave.open(wav_path, 'wb') as wav_file:
                    wav_file.setnchannels(1)  # モノラル
                    wav_file.setsampwidth(2)  # 16bit
                    wav_file.setframerate(22050)  # サンプリングレート
                    wav_file.writeframes(audio_data)
                
                # 再生
                await self._play_audio(wav_path)
                
                # 一時ファイル削除
                try:
                    os.unlink(wav_path)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"TTS synthesis error: {e}")

    def _synthesize_audio(self, text: str) -> bytes:
        """音声合成（同期処理）"""
        try:
            audio_stream = self.voice.synthesize(text)
            return b''.join(audio_stream)
        except Exception as e:
            logger.error(f"Audio synthesis failed: {e}")
            return b''

    async def _play_audio(self, wav_path: str):
        """WAVファイルを再生（macOS用）"""
        try:
            # macOSのafplayコマンドを使用
            process = await asyncio.create_subprocess_exec(
                "afplay", wav_path,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"Audio playback failed: {stderr.decode()}")
                
        except Exception as e:
            logger.error(f"Audio playback error: {e}")