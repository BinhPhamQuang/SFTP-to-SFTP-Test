import stat
from pathlib import Path

import paramiko
from plugins.data_transfer.model import BaseHook
from plugins.data_transfer.utils.common import get_console_logger
from typing import List, Any

from plugins.data_transfer.utils.constants import BASE_FOLDER_SFTP_SINK

LOGGER = get_console_logger()


class SftpHelper:
  @classmethod
  def create_sftp_connection(cls, hook: BaseHook) -> paramiko.SFTPClient:
    LOGGER.info(f"Create SFTP connection")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=hook.hostname, username=hook.username, password=hook.password, port=hook.port)
    return client.open_sftp()

  @classmethod
  def get_sink_path(cls, path: str) -> str:
    return BASE_FOLDER_SFTP_SINK + path

  @classmethod
  def get_origin_path(cls, path: str) -> str:
    return path.replace(BASE_FOLDER_SFTP_SINK,"")

  @classmethod
  def get_metadata(cls, client: paramiko.SFTPClient, path: str) -> List[Any]:
    try:
      LOGGER.info(f"Get metadata from path: {path}")
      files = []
      flist = client.listdir_attr(path)
      flist = sorted(flist, key=lambda x: x.filename)
      for f in flist:
        if stat.S_ISDIR(f.st_mode):
          files.extend(cls.get_metadata(client, "{}/{}".format(Path(path), f.filename)))
        else:
          files.append("{}/{}".format(Path(path), f.filename))
      return files
    except:
      return []
