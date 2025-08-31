import asyncio
import subprocess
import tempfile
import os
from typing import AsyncIterator
from ..core.config import TTSConfig
from loguru import logger


class PiperTTS:
    def __init__(self, config: TTSConfig):
        self.config = config
        self.piper_bin = config.piper_bin
        self.voice_dir = config.voice_dir
        
        # Piperバイナリの存在確認
        try:
            subprocess.run([self.piper_bin, "--version"], 
                         capture_output=True, check=True, timeout=5)
            logger.info(f"Piper TTS initialized: {self.piper_bin}")
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            logger.warning(f"Piper binary not found: {self.piper_bin}")
            self.piper_bin = None

    async def speak_sentences(self, sentences: AsyncIterator[str]):
        """文ごとにTTS合成して再生"""
        if self.piper_bin is None:
            logger.warning("Piper not available, skipping TTS")
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
        try:
            # 一時ファイルを作成してPiperで合成
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                wav_path = tmp_file.name
            
            # Piperで合成
            piper_cmd = [
                self.piper_bin,
                "--model", os.path.join(self.voice_dir, "model.onnx"),
                "--config", os.path.join(self.voice_dir, "model.json"),
                "--output_file", wav_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *piper_cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate(input=text.encode('utf-8'))
            
            if process.returncode == 0:
                # 生成されたWAVファイルを再生
                await self._play_audio(wav_path)
            else:
                logger.error(f"Piper synthesis failed: {stderr.decode()}")
            
            # 一時ファイルを削除
            try:
                os.unlink(wav_path)
            except:
                pass
                
        except Exception as e:
            logger.error(f"TTS synthesis error: {e}")

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