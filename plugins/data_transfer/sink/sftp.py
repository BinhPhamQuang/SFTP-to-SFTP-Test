from plugins.data_transfer.sink.base import Sink
import paramiko

from plugins.data_transfer.utils.common import get_console_logger
from plugins.data_transfer.utils.sftp_helper import SftpHelper
from typing import Dict
import os

LOGGER = get_console_logger()


class SftpSink(Sink):

  def __init__(self, **kwargs) -> None:
    super().__init__(**kwargs)

  def create_connection(self):
    LOGGER.info("[Sink] Create new connection")
    self.connection: paramiko.SFTPClient = SftpHelper.create_sftp_connection(self.hook)

  def get_connection(self) -> paramiko.SFTPClient:
    if not self.connection:
      self.create_connection()
    return self.connection

  def create_directory(self, path: str, mode: int = 0o777) -> None:
    connection = self.get_connection()
    if path == '/':
      # absolute path so change directory to root
      connection.chdir('/')
      return
    if path == '':
      # top-level relative directory must exist
      return
    try:
      connection.chdir(path)  # subdirectory exists
    except IOError:
      dirname, basename = os.path.split(path.rstrip('/'))
      self.create_directory(dirname, mode)  # make parent directories
      connection.mkdir(basename, mode)  # subdirectory missing, so created it
      connection.chdir(basename)

  def put_data(self, files_mapping: Dict[str, str]) -> None:
    for destination_path in files_mapping.keys():
      staging_path = files_mapping[destination_path]
      destination_path = SftpHelper.get_sink_path(destination_path)
      file_msg = f"from [{staging_path}] to [{destination_path}]"
      LOGGER.info(f"[Sink] Starting to transfer {file_msg}")

      self.create_directory(os.path.dirname(destination_path))
      self.get_connection().put(staging_path, destination_path)

  def close(self):
    if self.connection is not None:
      self.connection.close()
      self.connection = None
