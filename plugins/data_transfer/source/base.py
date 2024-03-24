from abc import ABC, abstractmethod
from plugins.data_transfer.model import BaseHook
from typing import List, Any, Dict


class Source(ABC):

  def __init__(self, hook: BaseHook) -> None:
    self.hook = hook
    self.connection = None

  @abstractmethod
  def create_connection(self):
    raise NotImplementedError

  @abstractmethod
  def get_connection(self) -> Any:
    raise NotImplementedError

  @abstractmethod
  def get_data(self, paths: List[str]) -> Dict[str, Any]:
    raise NotImplementedError

  @abstractmethod
  def close(self):
    raise NotImplementedError
