import numpy as np
from typing import List, Tuple, Optional
import galois
import os

class RSCodec:
    def __init__(self, k: int, m: int):
        self.k = k
        self.m = m
        self.n = k + m
        self.field = galois.GF(2**8)
        self._generate_matrices()

    def _generate_matrices(self):
        vandermonde = np.array([[1] + [self.field(x)**(j) for j in range(1, self.k)]
                               for x in range(self.n)])
        self.encoding_matrix = self.field(vandermonde)
        self.decoding_matrices = {}

    def _prepare_data(self, data: bytes, chunk_size: int) -> np.ndarray:
        padding_size = (chunk_size - len(data) % chunk_size) % chunk_size
        padded_data = data + b'\0' * padding_size
        return np.frombuffer(padded_data, dtype=np.uint8).reshape(-1, chunk_size)

    def encode(self, data: bytes, chunk_size: int = 1024) -> List[bytes]:
        if not data:
            return []

        data_matrix = self._prepare_data(data, chunk_size)
        encoded_chunks = []

        for i in range(data_matrix.shape[0]):
            chunk = data_matrix[i]
            encoded = self.encoding_matrix.dot(chunk)
            encoded_chunks.extend(bytes(x) for x in encoded)

        return encoded_chunks

    def decode(self, chunks: List[bytes], available_indices: List[int], 
               original_size: int) -> Optional[bytes]:
        if len(chunks) < self.k or len(available_indices) < self.k:
            return None

        try:
            chunk_size = len(chunks[0])
            available_indices = available_indices[:self.k]
            chunks = chunks[:self.k]

            decoding_matrix = self.encoding_matrix[available_indices, :self.k]
            decoding_matrix = self.field(np.linalg.inv(decoding_matrix))

            chunk_matrix = np.vstack([np.frombuffer(chunk, dtype=np.uint8) 
                                    for chunk in chunks])
            decoded = decoding_matrix.dot(chunk_matrix)
            
            result = bytes(decoded.flatten())
            return result[:original_size]
        except Exception:
            return None

    def encode_file(self, input_path: str, output_dir: str, 
                   chunk_size: int = 1024) -> Tuple[List[str], List[bytes]]:
        if not os.path.exists(input_path):
            return [], []

        try:
            with open(input_path, 'rb') as f:
                data = f.read()

            encoded_chunks = self.encode(data, chunk_size)
            if not encoded_chunks:
                return [], []

            os.makedirs(output_dir, exist_ok=True)
            chunk_paths = []

            for i, chunk in enumerate(encoded_chunks):
                chunk_path = os.path.join(output_dir, f'chunk_{i}')
                with open(chunk_path, 'wb') as f:
                    f.write(chunk)
                chunk_paths.append(chunk_path)

            return chunk_paths, encoded_chunks
        except Exception:
            return [], []

    def decode_file(self, chunks: List[bytes], available_indices: List[int], 
                   original_size: int, output_path: str) -> bool:
        decoded_data = self.decode(chunks, available_indices, original_size)
        if decoded_data is None:
            return False

        try:
            with open(output_path, 'wb') as f:
                f.write(decoded_data)
            return True
        except Exception:
            return False

    def repair_chunks(self, available_chunks: List[bytes], 
                     available_indices: List[int]) -> List[bytes]:
        if len(available_chunks) < self.k:
            return []

        try:
            decoded_data = self.decode(available_chunks, available_indices, 
                                     len(available_chunks[0]) * self.k)
            if decoded_data is None:
                return []

            return self.encode(decoded_data, len(available_chunks[0]))
        except Exception:
            return []
