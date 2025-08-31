import asyncio
import sys
import signal
from pathlib import Path

from .core.config import load_config
from .core.logging import setup_logging
from .audio.capture import AudioCapture
from .audio.wake_vad import WakeAndVAD
from .audio.asr import ASR
from .nlp.llm import LocalLLM
from .nlp.agent import Agent
from .nlp.splitter import sentence_stream
from .io.tts import PiperTTS
from .tools.clock import ClockTool
from .tools.iot_mock import IoTMockTool

from loguru import logger


class VoiceAgent:
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config = load_config(config_path)
        self.running = False
        
        # ログ設定
        setup_logging(
            level=self.config.logging.level,
            json_format=self.config.logging.json_format
        )
        
        logger.info("Voice Agent initializing...")

    async def initialize(self):
        """各コンポーネントの初期化"""
        try:
            # 音声キャプチャ
            self.audio_capture = AudioCapture(self.config.audio)
            
            # Wake Word + VAD
            self.wake_vad = WakeAndVAD(self.config.wake, self.config.vad)
            
            # ASR
            self.asr = ASR(self.config.asr)
            
            # LLM
            self.llm = LocalLLM(self.config.llm)
            if self.llm.llm is None:
                logger.warning("LLM is not available - continuing without LLM functionality")
            
            # TTS
            self.tts = PiperTTS(self.config.tts)
            
            # ツール初期化
            available_tools = {
                "clock": ClockTool(),
                "iot_mock": IoTMockTool()
            }
            
            enabled_tools = {
                name: tool for name, tool in available_tools.items()
                if name in self.config.agent.tools_enabled
            }
            
            # Agent
            try:
                with open(self.config.agent.system_prompt_path, 'r', encoding='utf-8') as f:
                    system_prompt = f.read()
            except FileNotFoundError:
                system_prompt = "あなたは親しみやすい音声アシスタントです。"
                logger.warning("System prompt file not found, using default")
            
            self.agent = Agent(
                llm=self.llm,
                tools=enabled_tools,
                system_prompt=system_prompt
            )
            
            logger.info("Voice Agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            raise

    async def run(self):
        """メインループ"""
        self.running = True
        logger.info("Voice Agent starting main loop")
        
        try:
            async for utterance_pcm in self.wake_vad.iter_utterances(self.audio_capture.stream()):
                if not self.running:
                    break
                    
                # ASRで文字起こし
                text = await self.asr.transcribe(utterance_pcm)
                if not text.strip():
                    continue
                
                logger.info(f"User said: '{text}'")
                
                # Agentで処理
                logger.info("Processing with Agent...")
                token_iter = self.agent.handle(text)
                
                # レスポンスをコンソールにも出力
                response_text = ""
                async for token in token_iter:
                    response_text += token
                    print(token, end='', flush=True)
                
                print()  # 改行
                logger.info(f"Agent response: {response_text}")
                
                # 文単位に分割してTTS（テキストから再生成）
                async def text_to_tokens():
                    for char in response_text:
                        yield char
                
                sent_iter = sentence_stream(text_to_tokens())
                await self.tts.speak_sentences(sent_iter)
                
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        except Exception as e:
            logger.error(f"Main loop error: {e}")
        finally:
            await self.shutdown()

    async def shutdown(self):
        """終了処理"""
        logger.info("Shutting down Voice Agent")
        self.running = False
        
        if hasattr(self, 'audio_capture'):
            self.audio_capture.stop()


async def main():
    agent = VoiceAgent()
    
    try:
        await agent.initialize()
        await agent.run()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received - shutting down")
        await agent.shutdown()
    except Exception as e:
        logger.error(f"Application error: {e}")
        await agent.shutdown()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())