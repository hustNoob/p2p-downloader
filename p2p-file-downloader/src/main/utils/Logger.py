import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional

class Logger:
    def __init__(self, name: str, log_file: str = "logs/p2p_downloader.log", level: str = "INFO",
                max_size: int = 10*1024*1024, backup_count: int = 5):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))

        formatter = logging.Formatter(
           '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        if log_file:
           os.makedirs(os.path.dirname(log_file), exist_ok=True)
           file_handler = RotatingFileHandler(
               log_file,
               maxBytes=max_size,
               backupCount=backup_count
           )
           file_handler.setFormatter(formatter)
           self.logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def debug(self, message: str):
        self.logger.debug(message)

    def info(self, message: str):
        self.logger.info(message)

    def warning(self, message: str):
        self.logger.warning(message)

    def error(self, message: str):
        self.logger.error(message)

    def critical(self, message: str):
        self.logger.critical(message)

    def exception(self, message: str):
        self.logger.exception(message)

    def set_level(self, level: str):
        self.logger.setLevel(getattr(logging, level.upper()))

    def get_level(self) -> str:
        return logging.getLevelName(self.logger.getEffectiveLevel())

    def close(self):
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)
