from plugins.data_transfer.source.base import Source
import paramiko

from plugins.data_transfer.utils.common import get_console_logger
from plugins.data_transfer.utils.sftp_helper import SftpHelper
from plugins.data_transfer.utils.constants import STAGING_PATH
from typing import Any, Dict, List
import os


def build_local_path(remote_path: str) -> str:
  return STAGING_PATH + remote_path


LOGGER = get_console_logger()


class SftpSource(Source):

  def __init__(self, **kwargs) -> None:
    super().__init__(**kwargs)

  def create_connection(self):
    LOGGER.info("[Source] Create new connection")
    self.connection: paramiko.SFTPClient = SftpHelper.create_sftp_connection(self.hook)

  def get_connection(self) -> paramiko.SFTPClient:
    if not self.connection:
      self.create_connection()
    return self.connection

  def get_data(self, remote_paths: List[str]) -> Dict[str, Any]:
    result = {}
    connection = self.get_connection()
    for remote_path in remote_paths:
      local_path = build_local_path(remote_path)
      os.makedirs(os.path.dirname(local_path), exist_ok=True)
      file_msg = f"from [{remote_path}] to [{local_path}]"
      LOGGER.info(f"[Source] Starting to transfer {file_msg}")
      connection.get(remote_path, local_path)
      result[remote_path] = local_path
    return result

  def close(self):
    if self.connection is not None:
      self.connection.close()
      self.connection = None
