import re
import json
from typing import AsyncIterator
from ..nlp.llm import LocalLLM
from ..tools.base import Tool
from ..core.config import AgentConfig
from loguru import logger


class Agent:
    def __init__(self, llm: LocalLLM, tools: dict[str, Tool], system_prompt: str):
        self.llm = llm
        self.tools = tools
        self.system_prompt = system_prompt
        self.conversation_history = []
        
        logger.info(f"Agent initialized with {len(tools)} tools: {list(tools.keys())}")

    def _build_prompt(self, user_text: str) -> str:
        # 利用可能なツールの説明を生成
        tools_desc = ""
        if self.tools:
            tools_desc = "\n利用可能なツール:\n"
            for tool in self.tools.values():
                tools_desc += f"- {tool.name}: {tool.description}\n"
            tools_desc += "\nツールを使用する場合は <tool:ツール名 引数=値> の形式で記述してください。\n"

        # プロンプトを構築
        prompt = f"{self.system_prompt}\n\n{tools_desc}\n"
        
        # 会話履歴を追加
        for entry in self.conversation_history[-5:]:  # 直近5回のやり取りのみ
            prompt += f"Human: {entry['human']}\nAssistant: {entry['assistant']}\n\n"
        
        prompt += f"Human: {user_text}\nAssistant: "
        
        return prompt

    def _extract_tool_calls(self, text: str) -> list[tuple[str, dict]]:
        """テキストからツール呼び出しを抽出"""
        tool_pattern = r'<tool:(\w+)\s+([^>]+)>'
        matches = re.findall(tool_pattern, text)
        
        tool_calls = []
        for tool_name, args_str in matches:
            if tool_name not in self.tools:
                continue
                
            # 引数をパース（簡易版）
            args = {}
            arg_pattern = r'(\w+)=([^,>]+)'
            for arg_name, arg_value in re.findall(arg_pattern, args_str):
                args[arg_name] = arg_value.strip()
            
            tool_calls.append((tool_name, args))
        
        return tool_calls

    async def handle(self, user_text: str) -> AsyncIterator[str]:
        prompt = self._build_prompt(user_text)
        response_buffer = ""
        
        logger.debug(f"Agent processing: '{user_text}'")
        
        try:
            # LLMからストリーミング生成
            for token in self.llm.stream(prompt):
                response_buffer += token
                yield token
                
                # ツール呼び出しの検出と実行
                tool_calls = self._extract_tool_calls(response_buffer)
                if tool_calls:
                    for tool_name, args in tool_calls:
                        try:
                            logger.info(f"Executing tool: {tool_name} with args: {args}")
                            tool_result = await self.tools[tool_name].run(**args)
                            
                            # ツール結果をストリームに含める
                            result_text = f"\n[{tool_name}の結果: {tool_result}]\n"
                            for char in result_text:
                                yield char
                            response_buffer += result_text
                            
                        except Exception as e:
                            error_text = f"\n[ツール実行エラー: {e}]\n"
                            for char in error_text:
                                yield char
                            response_buffer += error_text
                            logger.error(f"Tool execution failed: {e}")
            
            # 会話履歴に追加
            self.conversation_history.append({
                "human": user_text,
                "assistant": response_buffer
            })
            
        except Exception as e:
            error_msg = "申し訳ありませんが、応答中にエラーが発生しました。"
            logger.error(f"Agent processing failed: {e}")
            for char in error_msg:
                yield char