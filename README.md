# Airflow SFTP to SFTP
## TD;LR

Overview about my solution:

- Create a plugin(library) to migrate data from SFTP to SFTP with source and sink components that are independent of
  each other which are buffering data to local.
- Create an Airflow operator based on this plugin and execute this program directly inside the Airflow Worker.

This repository provides an operator/plugin to facilitate data migration between SFTP servers with local buffer.This
solution offers the following benefits:

- Support multiple source and multiple sink: This code is implemented base on abstract class -> adaptable if the data
  source
  transitions from SFTP to Object Storage or changing buffer data from local to minio,gcs,...
- The extensibility: Assess whether it is feasible to incorporate
  additional transformations before loading files into the target.
- Structure of code can easy to switch to multiprocessing in case business scale up to handle file sizes increase

## Prerequisites

Before you begin, ensure you have met the following requirements:

- Install [Docker Community Edition (CE)](https://docs.docker.com/get-docker/) on your workstation.
- Install [Docker Compose](https://docs.docker.com/compose/install/) v2.14.0 or newer on your workstation.

## Service infomations

| Service      | Address        | Username | Password | Port    | 
|--------------|----------------|----------|----------|---------|
| Airflow web  | localhost:8080 | airflow  | airflow  | 8080    |
| SFTP (souce) | localhost:2222 | sftp     | sftp     | 2222:22 |
| SFTP (sink)  | localhost:2223 | sftp     | sftp     | 2223:22 |

## Installation + usages

Follow these steps to install and setup the project:

1. Create necessary directories and setup environment variables:

    ```bash
    mkdir -p ./resources/{config,db,logs}
    touch ./resources/db/airflow.db
    chmod -R 777 ./resources/
    echo -e "AIRFLOW_UID=$(id -u)" > .env
    echo "Initialization complete."
    ```

2. Run this command to start all services:

    ```bash
    docker compose up -d
    ```
   or
    ```bash
   docker-compose up -d
    ```

   After initialization is complete, you should see a message like this:

    ```
    ❯ docker-compose  up -d      
    Starting sftp-source         ... done
    Starting sftp-sink           ... done
    Starting cake_airflow-init_1 ... done
    Starting cake_airflow-scheduler_1 ... done
    Starting cake_airflow-webserver_1 ... done
    ```

4. Login the Airflow web brower with table services information above:
  - Open your web browser and navigate to the Airflow UI. The default address is `localhost:8080` if you're running
    Airflow locally.
  - Find dag with name `example_sftp_to_sftp` and trigger this dag.
  - Waiting the dag running to success. (This DAG will migrate full data from `cake/sftp-data/source`
    to `cake/sftp-data/sink`)
  - Find the output result in `cake/sftp-data/sink/source`

## Assumptions
1. The directory structure in the source SFTP server is replicated in the destination SFTP server. If a directory does
   not exist in the destination, it is created.
2. The `transfer_files` function is designed to be idempotent. If a file already exists in the destination, it is not
   transferred again. This assumes that files with the same name are identical and when trigger send again, the files
   existing in target server must be ignored.
## Module Functionality

### plugins/data_transfer

This plugin is the core of this repository. It separates the flow into three steps.

- source
- transformations (optional)
- sink

A base class will be implemented for source and sink. This class will facilitate the support of multiple source and sink
implementations.

`AdaptableDataTransfer` is the class that glues the three components mentioned above into a single unit. The flow of
this class is:

1. Get metadata from source
2. Get metadata from sink
3. Ignores all file from source which are existing in sink
4. Split all path files to chunks (for easy to switch to multiprocessing purpose)
5. Process data chunks in a chain function (for easy switching to multiprocessing):
  - Read data from source save to local (staging).
  - Apply transformations to the data in the staging area and save the transformed data back to staging.
  - Save data from staging to sink.
6. Remove all files from local (staging)

#### How the transformations works?

I implemented the builder class for `AdaptableDataTransfer` to allow adding any functions to the builder class itself.
The logic follows a pipeline pattern with multiple steps: source -> [transformations] -> sink:

1. Add custom transformation. This function must be followed two rules:
  - Ony take one parameter: Files mapping directory. key: destination_path (path will be saved in sink); value:
    staging_path (path in local)
  - This function must return the files mapping directory.
2. Read data from staging path, rewrite data to this file, or somewhere in staging
3. Update the staging path to Files mapping directory
4. Return the files mapping directory

## Trade-offs
1. Skipping existing files during transfer saves bandwidth and time. But there's a trade-off: updated source files won't 
automatically overwrite the destination versions. This means you might need a separate process to ensure both locations have the latest files.
2. Using the `CustomOperator` with `BaseOperator` for transferring files can be efficient. With `paramiko`
   library which is designed to handle large files efficiently. However, the performance can still be impacted. This solution read data to RAM and save it to local as buffer
   before writing it to the destination, this could still consume a significant amount of resources. If we have a large number of files
   to transfer, it may have a chance to OOMkill. -> Create a new source/sink to store data to S3,GCS or MinIO instead of local like buffering area.
3. My approach can solve a problems bigdata based on split data to multiples chunks and change the loop to multiprocessing based on chain function. But this approach have 2 weakness:
   - This approach requires code modifications, hindering automatic detection and handling of anomalies -> MTTD + MTTR will incease
   - Before split data to a chunk, I must read all metadata from folder to get a list of file (for source) and metadata from sink to detect which files are exists. This happens in a single thread, which becomes a bottleneck for large data with millions of files.
3. The `SFTP Client` does not make sure the `Consistency` aspect; This library does not resume file transfers if they are interrupted. If a file transfer is interrupted,
   the entire file will need to be transferred again from the beginning -> This will be costly
4. For faster deployment purpose, my initial approach ran tasks directly within the Airflow Worker. However, this compromises worker stability by lacking isolated environments for tasks and resource control. This can lead to Airflow Worker crashes due to insufficient memory, disk space, or other resource limitations. -> use DockerExecutor instead