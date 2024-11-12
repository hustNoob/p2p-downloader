import aiohttp
import asyncio
from typing import List, Dict, Optional, Tuple
import time


class ChunkDownloader:
    def __init__(self, timeout: int = 30, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = None

    async def initialize(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()

    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None

    async def download_chunk(self, url: str, chunk_id: int,
                             start_byte: int = None, end_byte: int = None) -> Tuple[int, Optional[bytes]]:
        headers = {}
        if start_byte is not None and end_byte is not None:
            headers['Range'] = f'bytes={start_byte}-{end_byte}'

        retry_count = 0
        while retry_count < self.max_retries:
            try:
                async with self.session.get(url, headers=headers, timeout=self.timeout) as response:
                    if response.status in [200, 206]:
                        chunk_data = await response.read()
                        return chunk_id, chunk_data
                    elif response.status == 416:  # Range Not Satisfiable
                        return chunk_id, None
            except Exception as e:
                retry_count += 1
                if retry_count == self.max_retries:
                    print(f"Download failed for chunk {chunk_id}: {str(e)}")
                await asyncio.sleep(1)  # 失败后等待1秒再重试

        return chunk_id, None

    async def download_chunks(self, chunk_urls: Dict[int, List[str]],
                              progress_callback=None) -> Dict[int, bytes]:
        results = {}
        failed_chunks = set()

        async def download_with_progress(chunk_id: int, url: str):
            result = await self.download_chunk(url, chunk_id)
            if result[1] is not None:
                results[result[0]] = result[1]
                if progress_callback:
                    await progress_callback(len(results) / len(chunk_urls))
            else:
                failed_chunks.add(chunk_id)

        tasks = [
            asyncio.create_task(download_with_progress(chunk_id, urls[0]))
            for chunk_id, urls in chunk_urls.items() if urls
        ]

        await asyncio.gather(*tasks)
        return results