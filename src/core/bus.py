import asyncio
from typing import NamedTuple, Any


class Event(NamedTuple):
    type: str
    payload: dict[str, Any]


class Bus:
    def __init__(self):
        self.q = asyncio.Queue()

    async def publish(self, event: Event):
        await self.q.put(event)

    async def subscribe(self):
        while True:
            yield await self.q.get()