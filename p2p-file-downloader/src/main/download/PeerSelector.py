from typing import Dict, List, Tuple
import asyncio
import random
import time
from .ChunkDownloader import ChunkDownloader

class PeerSelector:
    def __init__(self, speed_test_size: int = 1024 * 1024):
        self.speed_test_size = speed_test_size
        self.peer_stats = {}
        self.chunk_downloader = ChunkDownloader()
        self.last_update = {}

    async def initialize(self):
        await self.chunk_downloader.initialize()

    async def test_peer_speed(self, peer_url: str) -> float:
        try:
            speed = await self.chunk_downloader.verify_download_speed(peer_url)
            self.peer_stats[peer_url] = {
                'speed': speed,
                'last_test': time.time(),
                'failures': 0
            }
            return speed
        except Exception:
            self.peer_stats[peer_url] = {
                'speed': 0,
                'last_test': time.time(),
                'failures': self.peer_stats.get(peer_url, {}).get('failures', 0) + 1
            }
            return 0.0

    async def select_optimal_peers(self, chunk_locations: Dict[int, List[str]]) -> Dict[int, List[str]]:
        if not chunk_locations:
            return {}

        all_peers = set()
        for peers in chunk_locations.values():
            all_peers.update(peers)

        test_tasks = [self.test_peer_speed(peer) for peer in all_peers 
                     if time.time() - self.last_update.get(peer, 0) > 300]
        if test_tasks:
            await asyncio.gather(*test_tasks)

        optimal_locations = {}
        for chunk_id, peers in chunk_locations.items():
            ranked_peers = sorted(
                [(peer, self.peer_stats.get(peer, {}).get('speed', 0)) 
                 for peer in peers if self.is_peer_reliable(peer)],
                key=lambda x: x[1],
                reverse=True
            )
            optimal_locations[chunk_id] = [peer for peer, _ in ranked_peers[:3]]

        return optimal_locations

    def get_peer_ranking(self) -> List[Tuple[str, float]]:
        return sorted(
            [(peer, stats.get('speed', 0)) 
             for peer, stats in self.peer_stats.items()],
            key=lambda x: x[1],
            reverse=True
        )

    def reset_stats(self):
        self.peer_stats.clear()
        self.last_update.clear()

    def get_best_peers(self, count: int = 5) -> List[str]:
        ranked_peers = self.get_peer_ranking()
        return [peer for peer, _ in ranked_peers[:count]]

    def is_peer_reliable(self, peer_url: str) -> bool:
        stats = self.peer_stats.get(peer_url, {})
        return stats.get('failures', 0) < 3 and stats.get('speed', 0) > 0

    async def retest_slow_peers(self, speed_threshold: float = 100 * 1024):
        slow_peers = [
            peer for peer, stats in self.peer_stats.items()
            if stats.get('speed', 0) < speed_threshold
        ]
        
        test_tasks = [self.test_peer_speed(peer) for peer in slow_peers]
        if test_tasks:
            await asyncio.gather(*test_tasks)
