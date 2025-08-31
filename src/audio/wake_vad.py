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
                # パッケージ内の主要wake wordモデルを指定
                import os
                model_dir = "/Users/yuya/dev/poc-voice-agent/.venv/lib/python3.13/site-packages/openwakeword/resources/models"
                wake_models = [
                    os.path.join(model_dir, "alexa_v0.1.onnx"),
                    os.path.join(model_dir, "hey_jarvis_v0.1.onnx"),
                ]
                
                self.wake_model = WakeWordModel(wake_models)
                # 利用可能なwake wordリストを取得
                available_keywords = list(self.wake_model.prediction_buffer.keys()) if hasattr(self.wake_model, 'prediction_buffer') else []
                logger.info(f"OpenWakeWord model initialized successfully")
                logger.info(f"Available wake words: {available_keywords}")
                
                # modelsディクショナリからも確認
                if hasattr(self.wake_model, 'models'):
                    model_names = list(self.wake_model.models.keys())
                    logger.info(f"Loaded models: {model_names}")
                    
            except Exception as e:
                logger.error(f"Wake word model load failed: {e}")
                logger.error("Falling back to disabled wake word detection")
                self.wake_model = None
        else:
            if wake_config.enabled and wake_config.use_simple_detection:
                logger.info(f"Simple wake word detection enabled: '{wake_config.keyword}'")
            else:
                logger.info("Wake word detection disabled")
            self.wake_model = None
        
        self.is_awake = False
        self.speech_buffer = deque(maxlen=16000 * 5)  # 5秒分のバッファ
        self.silence_counter = 0
        self.silence_threshold = 75  # 75フレーム（約1.5秒）の無音で区間終了
        self.status_counter = 0  # ステータス表示用カウンタ
        self.speech_detected = False  # 音声検知フラグ

    def _detect_wake_word(self, audio_chunk: np.ndarray) -> bool:
        # 簡易検出モードの場合
        if self.wake_config.enabled and self.wake_config.use_simple_detection:
            rms = np.sqrt(np.mean(audio_chunk ** 2))
            if rms > 0.01:  # 閾値は調整可能
                return True
            return False
        
        # OpenWakeWordモデル使用の場合
        if self.wake_model is None:
            return False  # モデルが初期化されていない場合は検知しない
        
        try:
            # OpenWakeWordの最小サンプル数をチェック（400サンプル = 25ms @ 16kHz）
            if len(audio_chunk) < 400:
                return False
                
            # audio_chunkをint16に変換（openwakewordの要求形式）
            audio_int16 = (audio_chunk * 32767).astype(np.int16)
            prediction = self.wake_model.predict(audio_int16)
            
            # デバッグ用：全ての予測結果をログ出力（高スコアのみ）
            for keyword, score in prediction.items():
                if score > 0.05:  # 0.05以上の場合のみログ
                    logger.debug(f"Wake word prediction: {keyword} (score: {score:.3f})")
                
                if score > 0.3:  # 閾値を0.3に下げる
                    logger.info(f"Wake word detected: {keyword} (score: {score:.2f})")
                    return True
            return False
        except Exception as e:
            logger.error(f"Wake word detection error: {e}")
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
                if not self.speech_detected:
                    self.speech_detected = True
                    logger.info("Speech detection started")
                self.speech_buffer.extend(chunk)
                self.silence_counter = 0
            else:
                if self.speech_detected:
                    self.silence_counter += 1
            
            # 無音が閾値を超えたら発話終了
            if self.speech_detected and self.silence_counter >= self.silence_threshold and len(self.speech_buffer) > 0:
                utterance = np.array(list(self.speech_buffer))
                self.speech_buffer.clear()
                self.silence_counter = 0
                self.speech_detected = False
                self.is_awake = False  # 一度処理したら再度wake wordを待つ
                
                logger.info(f"Utterance completed: {len(utterance)/16000:.2f}s - returning to wake word detection")
                yield utterance