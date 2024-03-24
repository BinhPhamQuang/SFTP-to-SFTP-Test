from airflow.models import BaseOperator
from typing import List, Any, Dict
from plugins.data_transfer.adaptable_data_transfer import AdaptableDataTransferBuilder
from plugins.data_transfer.model import BaseHook
from plugins.data_transfer.sink.sftp import SftpSink
from plugins.data_transfer.source.sftp import SftpSource


# This transformation will upper case all contents from each file
def example_transform(paths: Dict[str, str]) -> Dict[str, str]:
  for destination_path in paths.keys():
    with open(paths[destination_path], 'r+') as f:
      data = f.read()
      data = data.upper()
      f.seek(0)
      f.truncate()
      f.write(data)
  return paths


class SFTPToSFTP(BaseOperator):
  def __init__(
      self, *,
      source_hook: BaseHook,
      sink_hook: BaseHook,
      filepath: str,
      **kwargs,
  ) -> None:
    super().__init__(**kwargs)

    self.source_hook = source_hook
    self.sink_hook = sink_hook
    self.filepath = filepath
    self.chunk_size = 20

  """
    For the purpose of testing,
    Run inside airflow worker is being used instead of DockerExecutor to expedite deployment,
    as this is not intended for production.
  """

  def execute(self, context: Any) -> None:
    source = SftpSource(hook=self.source_hook)
    sink = SftpSink(hook=self.sink_hook)

    adapter = AdaptableDataTransferBuilder() \
      .with_source(source) \
      .with_sink(sink) \
      .with_chunk_size(self.chunk_size) \
      .add_transform(example_transform) \
      .build()

    adapter.run(self.filepath)
    adapter.close()
