import time
from typing import Dict, Optional
import asyncio
from collections import deque

class BandwidthManager:
    def __init__(self, max_bandwidth: float = float('inf'), window_size: int = 10):
        self.max_bandwidth = max_bandwidth
        self.window_size = window_size
        self.transfer_history = deque(maxlen=window_size)
        self.active_transfers = {}
        self.total_bytes_transferred = 0
        self.last_update = time.time()

    def start_transfer(self, transfer_id: str):
        self.active_transfers[transfer_id] = {
            'bytes_transferred': 0,
            'start_time': time.time(),
            'last_update': time.time(),
            'speed': 0.0
        }

    def update_transfer(self, transfer_id: str, bytes_transferred: int):
        if transfer_id not in self.active_transfers:
            return

        current_time = time.time()
        transfer = self.active_transfers[transfer_id]
        time_diff = current_time - transfer['last_update']

        if time_diff > 0:
            transfer['speed'] = bytes_transferred / time_diff
            transfer['bytes_transferred'] += bytes_transferred
            transfer['last_update'] = current_time
            self.total_bytes_transferred += bytes_transferred

            self.transfer_history.append({
                'timestamp': current_time,
                'bytes': bytes_transferred
            })

    def end_transfer(self, transfer_id: str):
        if transfer_id in self.active_transfers:
            del self.active_transfers[transfer_id]

    def get_current_bandwidth(self) -> float:
        if not self.transfer_history:
            return 0.0

        current_time = time.time()
        window_start = current_time - self.window_size
        recent_transfers = [t for t in self.transfer_history 
                          if t['timestamp'] > window_start]

        if not recent_transfers:
            return 0.0

        total_bytes = sum(t['bytes'] for t in recent_transfers)
        time_span = current_time - recent_transfers[0]['timestamp']
        return total_bytes / time_span if time_span > 0 else 0.0

    async def throttle_if_needed(self):
        current_bandwidth = self.get_current_bandwidth()
        if current_bandwidth > self.max_bandwidth:
            await asyncio.sleep(0.1)

    def get_transfer_stats(self, transfer_id: str) -> Optional[Dict]:
        return self.active_transfers.get(transfer_id)

    def reset_stats(self):
        self.transfer_history.clear()
        self.active_transfers.clear()
        self.total_bytes_transferred = 0
        self.last_update = time.time()
