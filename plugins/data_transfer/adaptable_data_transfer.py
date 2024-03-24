from plugins.data_transfer.model import BaseHook
from plugins.data_transfer.source.base import Source
from plugins.data_transfer.source.sftp import SftpSource
from plugins.data_transfer.sink.base import Sink
from plugins.data_transfer.sink.sftp import SftpSink
from typing import Callable, List, Dict
from concurrent.futures import ThreadPoolExecutor
from plugins.data_transfer.utils.common import divide_chunks, get_console_logger
import os

from plugins.data_transfer.utils.sftp_helper import SftpHelper

LOGGER = get_console_logger()


class AdaptableDataTransfer:

  def __init__(
      self,
      source: Source,
      sink: Sink,
      transformations: List[Callable],
      chunk_size,
      overwrite_data=False
  ):
    self.source = source
    self.sink = sink
    self.transformations = transformations
    self.chunk_size = chunk_size
    self.overwrite_data = overwrite_data

  def post_processing(self, files_mapping: Dict[str, str]):
    LOGGER.info(f"Deleting staging files")
    for destination_path in files_mapping.keys():
      staging_path = files_mapping[destination_path]
      os.remove(staging_path)

  def chain(self, paths: List[str]) -> None:
    # Source
    paths = self.source.get_data(paths)

    # Transformation
    for transformation in self.transformations:
      paths = transformation(paths)

    # Sink
    self.sink.put_data(paths)

    # Post-processing
    self.post_processing(paths)

  def run(self, path: str):
    files_from_source = SftpHelper.get_metadata(self.source.get_connection(), path)
    if not self.overwrite_data:
      # Fetch metadata from sink to detect which files is exists
      LOGGER.info(f"Get metadata from sink to ignore")
      files_from_sinks = SftpHelper.get_metadata(self.sink.get_connection(), SftpHelper.get_sink_path(path))
      files_from_sinks = [SftpHelper.get_origin_path(x) for x in files_from_sinks]

      # Remove all files existing in sink
      LOGGER.info(files_from_source)
      files_from_source = list(set(files_from_source) - set(files_from_sinks))

    LOGGER.info(f"Total files will be transferred: {len(files_from_source)}")

    # Divided data to chunk for multiprocessing purpose (not implement yet)

    for chunk in divide_chunks(files_from_source, self.chunk_size):
      self.chain(chunk)

  def close(self):
    self.source.close()
    self.sink.close()
    # self.executors.shutdown(wait=True)


class AdaptableDataTransferBuilder:
  def __init__(self) -> None:
    self.thread_pool_sizes = 1
    self.chunk_size = 1
    self.source = None
    self.sink = None
    self.transformations = []

  def with_source(self, source: Source):
    self.source = source
    return self

  def add_transform(self, func: Callable):
    self.transformations.append(func)
    return self

  def with_chunk_size(self, chunk_size: int):
    self.chunk_size = chunk_size
    return self

  def with_sink(self, sink: Sink):
    self.sink = sink
    return self

  def build(self) -> AdaptableDataTransfer:
    return AdaptableDataTransfer(
      source=self.source,
      sink=self.sink,
      transformations=self.transformations,
      chunk_size=self.chunk_size
    )