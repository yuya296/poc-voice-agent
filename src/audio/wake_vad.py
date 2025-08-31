import webrtcvad
import numpy as np
import asyncio
from typing import AsyncIterator
from collections import deque
from openwakeword import Model as WakeWordModel
from ..core.config import WakeConfig, VADConfig
from loguru import logger


class WakeAndVAD:
    def __init__(self, wake_config: WakeConfig, vad_config: VADConfig):
        self.wake_config = wake_config
        self.vad_config = vad_config
        
        # VAD初期化
        self.vad = webrtcvad.Vad(vad_config.aggressiveness)
        
        # Wake Word初期化
        if wake_config.enabled and not wake_config.use_simple_detection:
            try:
                self.wake_model = WakeWordModel()
                logger.info(f"Wake word initialized: {wake_config.keyword}")
            except Exception as e:
                logger.warning(f"Wake word model load failed: {e}")
                self.wake_model = None
        else:
            if wake_config.enabled:
                logger.info(f"Simple wake word detection enabled: '{wake_config.keyword}'")
            else:
                logger.info("Wake word detection disabled")
            self.wake_model = None
        
        self.is_awake = False
        self.speech_buffer = deque(maxlen=16000 * 5)  # 5秒分のバッファ
        self.silence_counter = 0
        self.silence_threshold = 30  # 30フレーム（約600ms）の無音で区間終了
        self.status_counter = 0  # ステータス表示用カウンタ

    def _detect_wake_word(self, audio_chunk: np.ndarray) -> bool:
        if self.wake_model is None:
            if self.wake_config.enabled and self.wake_config.use_simple_detection:
                # 簡易的な音声レベル検出（何か話したら起動）
                rms = np.sqrt(np.mean(audio_chunk ** 2))
                if rms > 0.01:  # 閾値は調整可能
                    return True
            return False
        
        try:
            # audio_chunkをint16に変換（openwakewordの要求形式）
            audio_int16 = (audio_chunk * 32767).astype(np.int16)
            prediction = self.wake_model.predict(audio_int16)
            
            # 閾値を超えた場合にwake
            for keyword, score in prediction.items():
                if score > 0.5:  # 閾値は調整可能
                    logger.info(f"Wake word detected: {keyword} (score: {score:.2f})")
                    return True
            return False
        except Exception as e:
            logger.debug(f"Wake word detection error: {e}")
            return False

    def _is_speech(self, audio_chunk: np.ndarray, sample_rate: int = 16000) -> bool:
        # WebRTC VADは特定のフレームサイズが必要（10/20/30ms）
        frame_duration = 20  # 20ms
        frame_size = int(sample_rate * frame_duration / 1000)
        
        if len(audio_chunk) < frame_size:
            return False
        
        # PCM16に変換
        pcm_data = (audio_chunk[:frame_size] * 32767).astype(np.int16).tobytes()
        
        try:
            return self.vad.is_speech(pcm_data, sample_rate)
        except Exception as e:
            logger.debug(f"VAD processing error: {e}")
            return False

    async def iter_utterances(self, audio_stream: AsyncIterator[np.ndarray]) -> AsyncIterator[np.ndarray]:
        logger.info("Starting wake word + VAD processing")
        
        async for chunk in audio_stream:
            # Wake word検出（未起動時のみ）
            if not self.is_awake:
                self.status_counter += 1
                # 10秒ごとに待機状態を表示（50チャンク * 20ms = 1秒, 500チャンク = 10秒）
                if self.status_counter % 500 == 0:
                    logger.debug(f"Waiting for wake word... ({self.status_counter} chunks processed)")
                
                if self._detect_wake_word(chunk):
                    self.is_awake = True
                    logger.info("Wake word triggered - listening for speech")
                continue
            
            # VADで音声区間検出
            is_speech = self._is_speech(chunk)
            
            if is_speech:
                self.speech_buffer.extend(chunk)
                self.silence_counter = 0
                # 最初の音声検出時のみログ出力
                if len(self.speech_buffer) < 1000:  # 約0.06秒分
                    logger.debug("Speech started")
            else:
                self.silence_counter += 1
            
            # 無音が閾値を超えたら発話終了
            if self.silence_counter >= self.silence_threshold and len(self.speech_buffer) > 0:
                utterance = np.array(list(self.speech_buffer))
                self.speech_buffer.clear()
                self.silence_counter = 0
                self.is_awake = False  # 一度処理したら再度wake wordを待つ
                
                logger.info(f"Utterance captured: {len(utterance)/16000:.2f}s")
                yield utterance