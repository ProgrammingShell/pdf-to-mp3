from abc import ABC, abstractmethod
import asyncio
import edge_tts

class TTSEngine(ABC):
    @abstractmethod
    async def synthesize(self, text: str, voice: str, rate: str, output_path: str):
        pass

    @abstractmethod
    def list_voices(self):
        pass


class EdgeTTSEngine(TTSEngine):
    async def synthesize(self, text: str, voice: str, rate: str, output_path: str):
        communicate = edge_tts.Communicate(text, voice=voice, rate=rate)
        await communicate.save(output_path)

    async def list_voices(self):
        voices = await edge_tts.list_voices()
        return [v["ShortName"] for v in voices]