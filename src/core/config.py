import yaml
from pydantic import BaseModel
from typing import Optional


class AudioConfig(BaseModel):
    device: Optional[str] = None
    rate: int = 16000
    chunk_ms: int = 20
    pre_roll_ms: int = 300


class WakeConfig(BaseModel):
    enabled: bool = True
    model_path: str = "models/openwakeword/hey_nova.tflite"
    keyword: str = "hello"
    use_simple_detection: bool = True  # 簡易音声レベル検出を使用


class VADConfig(BaseModel):
    aggressiveness: int = 2


class ASRConfig(BaseModel):
    model_size: str = "small"
    compute_type: str = "int8"
    beam_size: int = 1
    vad_filter: bool = True


class LLMConfig(BaseModel):
    gguf_path: str = "models/llm/tinyllama-1.1b-chat-q4_K_M.gguf"
    ctx_size: int = 2048
    n_threads: int = 4
    n_gpu_layers: int = 0
    top_p: float = 0.9
    top_k: int = 40
    temp: float = 0.7
    max_tokens: int = 256


class AgentConfig(BaseModel):
    tools_enabled: list[str] = ["clock", "iot_mock"]
    system_prompt_path: str = "config/prompts/system_ja.txt"


class TTSConfig(BaseModel):
    piper_bin: str = "piper"
    voice_dir: str = "models/piper/ja-JP-voice"
    sentence_pause_ms: int = 120


class LoggingConfig(BaseModel):
    level: str = "INFO"
    json_format: bool = False


class PrivacyConfig(BaseModel):
    save_audio: bool = False
    save_text: bool = True


class Config(BaseModel):
    audio: AudioConfig = AudioConfig()
    wake: WakeConfig = WakeConfig()
    vad: VADConfig = VADConfig()
    asr: ASRConfig = ASRConfig()
    llm: LLMConfig = LLMConfig()
    agent: AgentConfig = AgentConfig()
    tts: TTSConfig = TTSConfig()
    logging: LoggingConfig = LoggingConfig()
    privacy: PrivacyConfig = PrivacyConfig()


def load_config(config_path: str) -> Config:
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return Config(**data)
    except FileNotFoundError:
        return Config()  # デフォルト設定を使用