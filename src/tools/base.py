from typing import Protocol, Any


class Tool(Protocol):
    name: str
    description: str
    schema: dict[str, Any]
    
    async def run(self, **kwargs) -> str:
        ...