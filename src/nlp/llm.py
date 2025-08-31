from typing import Iterator
from llama_cpp import Llama
from ..core.config import LLMConfig
from loguru import logger


class LocalLLM:
    def __init__(self, config: LLMConfig):
        self.config = config
        logger.info(f"Loading LLM model from: {config.gguf_path}")
        
        # モデルファイルの存在確認
        import os
        if not os.path.exists(config.gguf_path):
            logger.error(f"LLM model file not found: {config.gguf_path}")
            logger.info("Please download a model file first. See README.md for instructions.")
            self.llm = None
            return
        
        try:
            self.llm = Llama(
                model_path=config.gguf_path,
                n_ctx=config.ctx_size,
                n_threads=config.n_threads,
                n_gpu_layers=config.n_gpu_layers,
                verbose=False
            )
            logger.info("LLM model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load LLM model: {e}")
            self.llm = None

    def stream(self, prompt: str) -> Iterator[str]:
        if self.llm is None:
            yield "LLMモデルが利用できません。README.mdの手順に従ってモデルをダウンロードしてください。"
            return
            
        try:
            logger.debug(f"LLM generation started for prompt length: {len(prompt)}")
            
            for output in self.llm.create_completion(
                prompt,
                stream=True,
                temperature=self.config.temp,
                top_p=self.config.top_p,
                top_k=self.config.top_k,
                max_tokens=self.config.max_tokens,
                stop=["</tool>", "\n\n", "Human:", "Assistant:"]
            ):
                token = output["choices"][0]["text"]
                if token:
                    yield token
                    
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            yield "申し訳ありませんが、応答の生成中にエラーが発生しました。"

    def generate(self, prompt: str) -> str:
        tokens = list(self.stream(prompt))
        return "".join(tokens)