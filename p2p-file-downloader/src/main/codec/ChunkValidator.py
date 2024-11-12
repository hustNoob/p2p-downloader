import hashlib
import os
from typing import List, Tuple, Optional

class ChunkValidator:
    def __init__(self, chunk_size: int = 1024 * 1024):
        self.chunk_size = chunk_size
        self.hash_algorithm = hashlib.sha256

    def calculate_chunk_hash(self, chunk_data: bytes) -> str:
        return self.hash_algorithm(chunk_data).hexdigest()

    def validate_chunk(self, chunk_data: bytes, expected_hash: str) -> bool:
        if not chunk_data or not expected_hash:
            return False
        return self.calculate_chunk_hash(chunk_data) == expected_hash

    def validate_chunk_size(self, chunk_data: bytes) -> bool:
        return len(chunk_data) <= self.chunk_size

    def validate_file_chunks(self, file_path: str, chunk_hashes: List[str]) -> List[bool]:
        if not os.path.exists(file_path):
            return [False] * len(chunk_hashes)

        results = []
        with open(file_path, 'rb') as file:
            for expected_hash in chunk_hashes:
                chunk = file.read(self.chunk_size)
                if not chunk:
                    results.append(False)
                    continue
                results.append(self.validate_chunk(chunk, expected_hash))
        return results

    def merge_chunks(self, chunks: List[bytes], output_path: str) -> bool:
        try:
            with open(output_path, 'wb') as output_file:
                for chunk in chunks:
                    output_file.write(chunk)
            return True
        except Exception:
            return False

    def split_file(self, file_path: str) -> Tuple[List[bytes], List[str]]:
        if not os.path.exists(file_path):
            return [], []

        chunks = []
        hashes = []
        
        with open(file_path, 'rb') as file:
            while True:
                chunk = file.read(self.chunk_size)
                if not chunk:
                    break
                chunks.append(chunk)
                hashes.append(self.calculate_chunk_hash(chunk))

        return chunks, hashes
