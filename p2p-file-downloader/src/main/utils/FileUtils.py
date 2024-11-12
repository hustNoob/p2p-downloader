import os
import shutil
from typing import List, Optional, Tuple
import hashlib

class FileUtils:
    @staticmethod
    def ensure_dir(directory: str):
        if not os.path.exists(directory):
            os.makedirs(directory)

    @staticmethod
    def remove_dir(directory: str):
        if os.path.exists(directory):
            shutil.rmtree(directory)

    @staticmethod
    def get_file_size(file_path: str) -> int:
        try:
            return os.path.getsize(file_path)
        except OSError:
            return 0

    @staticmethod
    def calculate_file_hash(file_path: str, chunk_size: int = 8192) -> Optional[str]:
        if not os.path.exists(file_path):
            return None

        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(chunk_size), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception:
            return None

    @staticmethod
    def split_file(file_path: str, chunk_size: int) -> List[str]:
        if not os.path.exists(file_path):
            return []

        chunk_files = []
        try:
            with open(file_path, 'rb') as f:
                chunk_number = 0
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break

                    chunk_file = f"{file_path}.{chunk_number}"
                    with open(chunk_file, 'wb') as chunk_f:
                        chunk_f.write(chunk)
                    chunk_files.append(chunk_file)
                    chunk_number += 1
        except Exception:
            for chunk_file in chunk_files:
                if os.path.exists(chunk_file):
                    os.remove(chunk_file)
            return []

        return chunk_files

    @staticmethod
    def merge_files(chunk_files: List[str], output_path: str) -> bool:
        try:
            with open(output_path, 'wb') as outfile:
                for chunk_file in sorted(chunk_files):
                    if os.path.exists(chunk_file):
                        with open(chunk_file, 'rb') as infile:
                            shutil.copyfileobj(infile, outfile)
            return True
        except Exception:
            if os.path.exists(output_path):
                os.remove(output_path)
            return False

    @staticmethod
    def clean_temp_files(file_pattern: str):
        try:
            directory = os.path.dirname(file_pattern)
            pattern = os.path.basename(file_pattern)
            for file in os.listdir(directory):
                if file.startswith(pattern):
                    os.remove(os.path.join(directory, file))
        except Exception:
            pass

    @staticmethod
    def move_file(src: str, dst: str) -> bool:
        try:
            shutil.move(src, dst)
            return True
        except Exception:
            return False

    @staticmethod
    def copy_file(src: str, dst: str) -> bool:
        try:
            shutil.copy2(src, dst)
            return True
        except Exception:
            return False
