import asyncio
import time
import psutil
from typing import Dict, List, Optional
import socket
import platform

class NetworkMonitor:
    def __init__(self, update_interval: float = 1.0):
        self.update_interval = update_interval
        self.network_stats = {}
        self.last_update = time.time()
        self.is_monitoring = False
        self._initialize_interfaces()

    def _initialize_interfaces(self):
        self.interfaces = {}
        try:
            addrs = psutil.net_if_addrs()
            for interface, addresses in addrs.items():
                for addr in addresses:
                    if addr.family == socket.AF_INET:
                        self.interfaces[interface] = addr.address
        except Exception:
            pass

    async def start_monitoring(self):
        if self.is_monitoring:
            return

        self.is_monitoring = True
        while self.is_monitoring:
            self._update_stats()
            await asyncio.sleep(self.update_interval)

    async def stop_monitoring(self):
        self.is_monitoring = False

    def _update_stats(self):
        try:
            current_time = time.time()
            counters = psutil.net_io_counters(pernic=True)
            
            for interface, stats in counters.items():
                if interface not in self.network_stats:
                    self.network_stats[interface] = {
                        'bytes_sent': stats.bytes_sent,
                        'bytes_recv': stats.bytes_recv,
                        'last_update': current_time,
                        'send_speed': 0,
                        'recv_speed': 0
                    }
                else:
                    time_diff = current_time - self.network_stats[interface]['last_update']
                    if time_diff > 0:
                        bytes_sent_diff = stats.bytes_sent - self.network_stats[interface]['bytes_sent']
                        bytes_recv_diff = stats.bytes_recv - self.network_stats[interface]['bytes_recv']
                        
                        self.network_stats[interface].update({
                            'bytes_sent': stats.bytes_sent,
                            'bytes_recv': stats.bytes_recv,
                            'last_update': current_time,
                            'send_speed': bytes_sent_diff / time_diff,
                            'recv_speed': bytes_recv_diff / time_diff
                        })
        except Exception:
            pass

    def get_network_stats(self) -> Dict:
        return self.network_stats.copy()

    def get_total_bandwidth(self) -> Dict[str, float]:
        total_send = 0.0
        total_recv = 0.0
        
        for stats in self.network_stats.values():
            total_send += stats.get('send_speed', 0)
            total_recv += stats.get('recv_speed', 0)
            
        return {
            'send_speed': total_send,
            'recv_speed': total_recv
        }

    def get_interface_addresses(self) -> Dict[str, str]:
        return self.interfaces.copy()

    def get_active_interfaces(self) -> List[str]:
        return list(self.network_stats.keys())

    def get_connection_count(self) -> int:
        try:
            return len(psutil.net_connections())
        except Exception:
            return 0

    def reset_stats(self):
        self.network_stats.clear()
        self.last_update = time.time()
        self._initialize_interfaces()
