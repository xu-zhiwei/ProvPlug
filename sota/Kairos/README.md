# ProvPlug: Enhancing KAIROS with LLM-Driven Plugins

This project is a reproduction and enhancement of **KAIROS**, a state-of-the-art provenance graph-based intrusion detection system. 

Beyond standard reproduction, this project integrates **PROVPLUG**, a framework utilizing Large Language Models (LLMs) to bridge the gap between Data Provenance Graphs (DPGs) and Graph Neural Networks (GNNs), alongside other enhancement methods like **[R-CAID](https://ieeexplore.ieee.org/abstract/document/10646671)**.

> **KAIROS: Practical Intrusion Detection and Investigation using Whole-system Provenance**  
> Zijun Cheng, Qiujian Lv, Jinyuan Liang, Yang Wang, Degang Sun, Thomas Pasquier, Xueyuan Han  
> *2024 IEEE Symposium on Security and Privacy (SP)*  
> [Paper](https://arxiv.org/pdf/2308.05034) | [Official Repository](https://github.com/ubc-provenance/kairos)

## Environment Configuration

While the original implementation relies on specific settings, we have adapted this reproduction environment to support **PyTorch 2.5** with **CUDA 12.4**.

### Reference to Original Settings
For detailed insights into the original environment configuration and database details, please refer to the official KAIROS documentation:

**[kairos/DARPA/settings/environment-settings.md](./settings/environment-settings.md)**

**[kairos/DARPA/settings/database.md](./settings/database.md)**

---

###  Reproduction Dependencies

Below are the exact versions of the key packages used in our setup. Note that the geometric libraries are built specifically for `pt25` (PyTorch 2.5) and `cu124` (CUDA 12.4).

| Package             | Version            |
|---------------------|--------------------|
| `torch`             | `2.5.1`            |
| `torchvision`       | `0.20.1`           |
| `torch-geometric`   | `2.6.1`            |
| `torch_cluster`     | `1.6.3+pt25cu124`  |
| `torch_scatter`     | `2.1.2+pt25cu124`  |
| `torch_sparse`      | `0.6.18+pt25cu124` |
| `torch_spline_conv` | `1.2.2+pt25cu124`  |
| `pyg-lib`           | `0.4.0+pt25cu124`  |
| `psycopg2`          | `2.9.10`           |
| `tqdm`              | `4.67.1`           |
| `scikit-learn`      | `1.2.0`            |
| `networkx`          | `2.8.7`            |
| `xxhash`            | `3.2.0`            |
| `graphviz`          | `0.20.1`           |
| `pytz`              | `2025.2`           |



### Prerequisites
We use the following settings to run the experiments reported in the paper:
1. OS Version: 5.19.0-46-generic #47~22.04.1-Ubuntu
2. Anaconda: 23.3.1
3. PostgresSQL: Version 15.3, Ubuntu 15.3-1.pgdg22.04+1 ([installation guide](https://www.cherryservers.com/blog/how-to-install-and-setup-postgresql-server-on-ubuntu-20-04))
4. GraphViz: 2.43.0 
5. GPU (Driver Version: 530.41.03): CUDA Version 12.1

### Python Libraries
Install the following libraries, 
or use our [`requirements.txt`](requirements.txt):
```commandline
conda create -n kairos python=3.9
conda activate kairos
# Note: using "pip install psycopg2" to install may fail
conda install psycopg2
conda install tqdm
# We encountered a problem in feature hashing functions with version 1.2.2
pip install scikit-learn==1.2.0
pip install networkx==2.8.7
pip install xxhash==3.2.0
pip install graphviz==0.20.1

# PyTorch GPU version
conda install pytorch==1.13.1 torchvision==0.14.1 torchaudio==0.13.1 pytorch-cuda=11.7 -c pytorch -c nvidia
pip install torch_geometric==2.0.0
pip install pyg_lib torch_scatter torch_sparse torch_cluster torch_spline_conv -f https://data.pyg.org/whl/torch-1.13.0+cu117.html

```

### Troubleshooting

**Issue**: When running `psycopg2.connect()`, we received this error:
```
OperationalError: connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed: FATAL:  Peer authentication failed for user "postgres".
```

**Solution**: Follow the solution in [this](https://stackoverflow.com/questions/18664074/getting-error-peer-authentication-failed-for-user-postgres-when-trying-to-ge) Stack Overflow post.

**Issue**: When running `psycopg2.connect()`, we received this error:
```
OperationalError: could not connect to server: No such file or directory the server running locally and accepting connections on Unix domain socket "/XXX/.s.PGSQL.5432"?
```

**Solution**:
* Check if `postgres` is running. If not, start it, re-run the code, and see if the problem still exists.
* If the problem still exists when `postgres` is running, identify the location of the file `.s.PGSQL.5432`. 
Then set the `host` parameter in `psycopg2.connect()` to be `/the/location/of/the/file/`. The problem should be fixed then.



### CADETS database setup


```commandline
# execute the psql with postgres user
sudo -u postgres psql

# create the database
postgres=# create database tc_cadet_dataset_db;

# switch to the created database
postgres=# \connect tc_cadet_dataset_db;

# create the event table and grant the privileges to postgres
tc_cadet_dataset_db=# create table event_table
(
    src_node      varchar,
    src_index_id  varchar,
    operation     varchar,
    dst_node      varchar,
    dst_index_id  varchar,
    timestamp_rec bigint,
    _id           serial
);
tc_cadet_dataset_db=# alter table event_table owner to postgres;
tc_cadet_dataset_db=# create unique index event_table__id_uindex on event_table (_id); grant delete, insert, references, select, trigger, truncate, update on event_table to postgres;

# create the file table
tc_cadet_dataset_db=# create table file_node_table
(
    node_uuid varchar not null,
    hash_id   varchar not null,
    path      varchar,
    constraint file_node_table_pk
        primary key (node_uuid, hash_id)
);
tc_cadet_dataset_db=# alter table file_node_table owner to postgres;

# create the netflow table
tc_cadet_dataset_db=# create table netflow_node_table
(
    node_uuid varchar not null,
    hash_id   varchar not null,
    src_addr  varchar,
    src_port  varchar,
    dst_addr  varchar,
    dst_port  varchar,
    constraint netflow_node_table_pk
        primary key (node_uuid, hash_id)
);
tc_cadet_dataset_db=# alter table netflow_node_table owner to postgres;

# create the subject table
tc_cadet_dataset_db=# create table subject_node_table
(
    node_uuid varchar,
    hash_id   varchar,
    exec      varchar
);
tc_cadet_dataset_db=# alter table subject_node_table owner to postgres;

# create the node2id table
tc_cadet_dataset_db=# create table node2id
(
    hash_id   varchar not null
        constraint node2id_pk
            primary key,
    node_type varchar,
    msg       varchar,
    index_id  bigint
);
tc_cadet_dataset_db=# alter table node2id owner to postgres;
tc_cadet_dataset_db=# create unique index node2id_hash_id_uindex on node2id (hash_id);
```

### Source code for reproduction

The core reproduction of the KAIROS model is located in the **`CADETS_E3/`** directory.


## Results
The experimental results for the reproduction and plugin enhancements are organized by dataset and configuration.

- **Location**: Detailed metrics (Precision, Recall, F1 Score) can be found in the `/results` directory.

- **Format**: Refer to the `evaluation.log` file within each specific experiment subdirectory for raw output logs and performance summaries.
