import datetime

from airflow import DAG
from airflow.models import Variable
from operators.sftp import SFTPToSFTP
from plugins.data_transfer.model import BaseHook

with DAG(
    dag_id="example_sftp_to_sftp",
    start_date=datetime.datetime(2023, 3, 23),
    catchup=False,
    concurrency=1,
    schedule="@daily",
):
  sftp_username = Variable.get("sftp_username")
  sftp_password = Variable.get("sftp_password")

  source_hook = BaseHook(hostname='sftp-source', username=sftp_username, password=sftp_password, port=22)
  sink_hook = BaseHook(hostname='sftp-sink', username=sftp_username, password=sftp_password, port=22)

  task1 = SFTPToSFTP(
    task_id="task",
    source_hook=source_hook,
    sink_hook=sink_hook,
    filepath='/source'
  )
