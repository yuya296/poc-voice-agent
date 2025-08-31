from datetime import datetime
from .base import Tool


class ClockTool:
    name = "clock"
    description = "現在の時刻を取得する"
    schema = {
        "type": "object",
        "properties": {
            "time": {
                "type": "string",
                "description": "時刻の種類（now=現在時刻）"
            }
        },
        "required": ["time"]
    }

    async def run(self, time: str = "now", **kwargs) -> str:
        if time == "now":
            now = datetime.now()
            return f"{now.strftime('%Y年%m月%d日 %H時%M分')}"
        else:
            return "対応していない時刻形式です"