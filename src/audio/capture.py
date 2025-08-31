import sounddevice as sd
import numpy as np
import asyncio
from typing import AsyncIterator
from collections import deque
from ..core.config import AudioConfig
from loguru import logger


class AudioCapture:
    def __init__(self, config: AudioConfig):
        self.config = config
        self.ring_buffer = deque(maxlen=config.rate * 10)  # 10秒分のリングバッファ
        self.is_recording = False

    def _audio_callback(self, indata, frames, time, status):
        if status:
            logger.warning(f"Audio input overflow: {status}")
        
        # モノラル16kHzに変換
        audio_data = indata[:, 0] if indata.ndim > 1 else indata
        audio_data = audio_data.astype(np.float32)
        
        # リングバッファに追加
        self.ring_buffer.extend(audio_data)

    async def stream(self) -> AsyncIterator[np.ndarray]:
        chunk_size = int(self.config.rate * self.config.chunk_ms / 1000)
        
        with sd.InputStream(
            samplerate=self.config.rate,
            channels=1,
            dtype=np.float32,
            blocksize=chunk_size,
            device=self.config.device,
            callback=self._audio_callback
        ):
            self.is_recording = True
            logger.info(f"Audio capture started (device: {self.config.device}, rate: {self.config.rate}Hz)")
            
            while self.is_recording:
                if len(self.ring_buffer) >= chunk_size:
                    # チャンクサイズ分のデータを取り出し
                    chunk = np.array([self.ring_buffer.popleft() for _ in range(chunk_size)])
                    yield chunk
                else:
                    await asyncio.sleep(0.001)  # 短時間待機

    def stop(self):
        self.is_recording = False
        logger.info("Audio capture stopped")