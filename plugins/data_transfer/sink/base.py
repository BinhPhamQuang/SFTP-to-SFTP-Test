from abc import ABC, abstractmethod

from plugins.data_transfer.model import BaseHook
from typing import Dict, Any


class Sink(ABC):
  @abstractmethod
  def put_data(self, data: Dict[str, str]) -> None:
    raise NotImplementedError

  @abstractmethod
  def get_connection(self) -> Any:
    raise NotImplementedError

  @abstractmethod
  def create_connection(self):
    raise NotImplementedError

  @abstractmethod
  def create_directory(self, path: str, mode: int = 0o777) -> None:
    raise NotImplementedError

  def __init__(self, hook: BaseHook) -> None:
    self.hook = hook
    self.connection = None

  @abstractmethod
  def close(self):
    raise NotImplementedError
