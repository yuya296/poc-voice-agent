import numpy as np
from faster_whisper import WhisperModel
from ..core.config import ASRConfig
from loguru import logger


class ASR:
    def __init__(self, config: ASRConfig):
        self.config = config
        logger.info(f"Loading Whisper model: {config.model_size}")
        
        self.model = WhisperModel(
            config.model_size,
            device="cpu",
            compute_type=config.compute_type
        )
        
        logger.info("Whisper model loaded successfully")

    async def transcribe(self, audio_data: np.ndarray) -> str:
        try:
            # faster-whisperは音声データを直接受け取れる
            segments, info = self.model.transcribe(
                audio_data,
                beam_size=self.config.beam_size,
                vad_filter=self.config.vad_filter,
                language="ja"  # 日本語に固定（設定可能にしても良い）
            )
            
            # 全セグメントを結合
            text_parts = []
            for segment in segments:
                text_parts.append(segment.text.strip())
            
            full_text = " ".join(text_parts).strip()
            
            if full_text:
                logger.info(f"Transcribed: '{full_text}' (confidence: {info.language_probability:.2f})")
            
            return full_text
            
        except Exception as e:
            logger.error(f"ASR transcription failed: {e}")
            return ""