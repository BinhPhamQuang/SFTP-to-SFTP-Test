from typing import List, Any
import logging


def divide_chunks(data: List[Any], chunk_size: int) -> List[List[Any]]:
  for i in range(0, len(data), chunk_size):
    yield data[i:i + chunk_size]


def get_console_logger() -> logging.Logger:
  logging.basicConfig()
  logger = logging.getLogger()
  logger.setLevel(logging.INFO)
  return logger
