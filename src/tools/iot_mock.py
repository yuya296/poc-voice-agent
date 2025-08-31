from .base import Tool
from loguru import logger


class IoTMockTool:
    name = "iot_mock"
    description = "IoTデバイスの制御（モック）"
    schema = {
        "type": "object",
        "properties": {
            "device": {
                "type": "string",
                "description": "制御するデバイス（light, aircon, tv等）"
            },
            "action": {
                "type": "string", 
                "description": "実行するアクション（on, off, toggle等）"
            }
        },
        "required": ["device", "action"]
    }

    async def run(self, device: str, action: str, **kwargs) -> str:
        logger.info(f"IoT Mock: {device} -> {action}")
        
        device_map = {
            "light": "電気",
            "lights": "電気", 
            "ライト": "電気",
            "電気": "電気",
            "aircon": "エアコン",
            "エアコン": "エアコン",
            "tv": "テレビ",
            "テレビ": "テレビ"
        }
        
        action_map = {
            "on": "をつけました",
            "off": "を消しました", 
            "toggle": "を切り替えました",
            "つけて": "をつけました",
            "消して": "を消しました"
        }
        
        device_name = device_map.get(device.lower(), device)
        action_result = action_map.get(action.lower(), f"で{action}を実行しました")
        
        return f"{device_name}{action_result}"