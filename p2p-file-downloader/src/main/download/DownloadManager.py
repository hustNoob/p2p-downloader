import asyncio
import os
import time
from typing import List, Dict, Optional, Callable
from .ChunkDownloader import ChunkDownloader
from ..codec.RSCodec import RSCodec
from ..codec.ChunkValidator import ChunkValidator
from ..utils.FileUtils import FileUtils
from ..utils.Config import Config


class DownloadManager:
    def __init__(self, k: int = 4, m: int = 2, chunk_size: int = 1024 * 1024):
        self.chunk_size = chunk_size
        self.rs_codec = RSCodec(k, m)
        self.chunk_validator = ChunkValidator(chunk_size)
        self.chunk_downloader = ChunkDownloader()
        self.download_state = {}
        self.is_downloading = False

        # 新增属性
        self.max_speed = 0  # 0 表示不限速
        self.max_concurrent_downloads = 3
        self.current_speed = 0
        self.downloaded_bytes = 0
        self.last_speed_update = time.time()

        # 从配置文件加载设置
        self.load_settings()

    # 新增方法：加载设置
    def load_settings(self):
        config = Config()
        self.max_speed = config.get('download.max_speed', 0)
        self.max_concurrent_downloads = config.get('download.max_concurrent_downloads', 3)

    # 新增方法：保存设置
    def save_settings(self):
        config = Config()
        config.set('download.max_speed', self.max_speed)
        config.set('download.max_concurrent_downloads', self.max_concurrent_downloads)

    # 新增方法：获取和设置最大速度
    def get_max_speed(self) -> int:
        return self.max_speed

    def set_max_speed(self, speed: int):
        self.max_speed = speed

    # 新增方法：获取和设置并发下载数
    def get_concurrent_downloads(self) -> int:
        return self.max_concurrent_downloads

    def set_concurrent_downloads(self, count: int):
        self.max_concurrent_downloads = count

    # 新增方法：更新速度计算
    def update_speed(self, bytes_downloaded: int):
        current_time = time.time()
        time_diff = current_time - self.last_speed_update
        if time_diff >= 1.0:
            self.current_speed = bytes_downloaded / time_diff
            self.last_speed_update = current_time
            self.downloaded_bytes = 0
        else:
            self.downloaded_bytes += bytes_downloaded

    # 修改现有的 initialize 方法
    async def initialize(self):
        await self.chunk_downloader.initialize()
        self.load_settings()

    async def close(self):
        await self.chunk_downloader.close()

    # 修改现有的 start_download 方法
    async def start_download(self, url: str, output_path: str,
                             progress_callback: Optional[Callable] = None) -> bool:
        if self.is_downloading:
            return False

        self.is_downloading = True
        self.download_state = {
            'url': url,
            'output_path': output_path,
            'progress': 0.0,
            'status': 'downloading',
            'downloaded_bytes': 0
        }

        try:
            print(f"Starting download from {url}")
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            async with self.chunk_downloader.session.head(url) as response:
                if response.status != 200:
                    print(f"Failed to get file size, status: {response.status}")
                    return False

                file_size = int(response.headers.get('Content-Length', 0))
                if file_size == 0:
                    print("File size is 0 or unknown")
                    return False

                print(f"File size: {file_size} bytes")

            chunk_count = (file_size + self.chunk_size - 1) // self.chunk_size
            chunk_urls = {}

            for i in range(chunk_count):
                start_byte = i * self.chunk_size
                end_byte = min(start_byte + self.chunk_size - 1, file_size - 1)
                chunk_urls[i] = [url]

            print(f"Starting download of {chunk_count} chunks")

            async def progress_wrapper(progress: float, bytes_downloaded: int):
                self.update_speed(bytes_downloaded)
                self.download_state['downloaded_bytes'] += bytes_downloaded
                if progress_callback:
                    await progress_callback(progress, self.current_speed)

            chunks = await self.chunk_downloader.download_chunks(
                chunk_urls,
                progress_wrapper
            )

            if len(chunks) != chunk_count:
                print(f"Download incomplete: {len(chunks)}/{chunk_count} chunks")
                return False

            print("Merging chunks...")
            with open(output_path, 'wb') as f:
                for i in range(chunk_count):
                    if i in chunks:
                        f.write(chunks[i])
                    else:
                        print(f"Missing chunk {i}")
                        return False

            print("Download completed successfully")
            self.download_state['status'] = 'completed'
            return True

        except Exception as e:
            print(f"Download failed: {str(e)}")
            self.download_state['status'] = 'failed'
            return False
        finally:
            self.is_downloading = False