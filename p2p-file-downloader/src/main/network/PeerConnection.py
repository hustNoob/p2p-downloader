import asyncio
import aiohttp
from typing import Dict, Optional, List, Tuple
import time
import json

class PeerConnection:
    def __init__(self, peer_id: str, host: str, port: int):
        self.peer_id = peer_id
        self.host = host
        self.port = port
        self.session = None
        self.is_connected = False
        self.stats = {
            'bytes_sent': 0,
            'bytes_received': 0,
            'failed_attempts': 0,
            'last_error': None
        }

    async def connect(self) -> bool:
        if self.is_connected:
            return True

        try:
            self.session = aiohttp.ClientSession()
            async with self.session.get(f"http://{self.host}:{self.port}/ping") as response:
                if response.status == 200:
                    self.is_connected = True
                    return True
        except Exception as e:
            self.stats['failed_attempts'] += 1
            self.stats['last_error'] = str(e)
        return False

    async def disconnect(self):
        if self.session:
            await self.session.close()
        self.is_connected = False

    async def send_data(self, data: bytes) -> bool:
        if not self.is_connected:
            return False

        try:
            async with self.session.post(
                f"http://{self.host}:{self.port}/data",
                data=data
            ) as response:
                if response.status == 200:
                    self.stats['bytes_sent'] += len(data)
                    return True
        except Exception as e:
            self.stats['failed_attempts'] += 1
            self.stats['last_error'] = str(e)
        return False

    async def receive_data(self) -> Optional[bytes]:
        if not self.is_connected:
            return None

        try:
            async with self.session.get(
                f"http://{self.host}:{self.port}/data"
            ) as response:
                if response.status == 200:
                    data = await response.read()
                    self.stats['bytes_received'] += len(data)
                    return data
        except Exception as e:
            self.stats['failed_attempts'] += 1
            self.stats['last_error'] = str(e)
        return None

    async def ping(self) -> float:
        start_time = time.time()
        try:
            async with self.session.get(
                f"http://{self.host}:{self.port}/ping"
            ) as response:
                if response.status == 200:
                    return time.time() - start_time
        except Exception:
            pass
        return float('inf')

    async def get_peer_info(self) -> Optional[Dict]:
        try:
            async with self.session.get(
                f"http://{self.host}:{self.port}/info"
            ) as response:
                if response.status == 200:
                    return await response.json()
        except Exception:
            pass
        return None

    def reset_stats(self):
        self.stats = {
            'bytes_sent': 0,
            'bytes_received': 0,
            'failed_attempts': 0,
            'last_error': None
        }
