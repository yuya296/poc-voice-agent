import re
from typing import AsyncIterator


async def sentence_stream(token_iter: AsyncIterator[str]) -> AsyncIterator[str]:
    """
    トークンストリームを文単位に分割してyield
    句読点や「です/ます/ね/よ」などで文を区切る
    """
    buffer = ""
    
    # 文区切りパターン（日本語対応）
    sentence_endings = re.compile(r'[。！？]|です[。、]?|ます[。、]?|ね[。、]?|よ[。、]?|だ[。、]?')
    
    async for token in token_iter:
        buffer += token
        
        # 文の終わりを検出
        if sentence_endings.search(buffer):
            # 最後の文区切り位置を見つけて分割
            matches = list(sentence_endings.finditer(buffer))
            if matches:
                last_match = matches[-1]
                sentence = buffer[:last_match.end()].strip()
                buffer = buffer[last_match.end():].strip()
                
                if sentence:
                    yield sentence
    
    # 残りのバッファがあれば最後に出力
    if buffer.strip():
        yield buffer.strip()