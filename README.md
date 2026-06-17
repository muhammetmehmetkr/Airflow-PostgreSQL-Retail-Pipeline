## Project Architecture

![arch](images/arch.png)

## Project Structure

```text
homework#13
├── airflow
│   └── airflow
│       └── dags
│           └── airflow_hw1_dag.py
├── images
├── .env
├── airflow_homework1_solution.md
└── docker-compose.yaml
```

## Docker Setup

- docker-compose.yaml file:

```yaml
x-airflow-common:
  &airflow-common
  image: ${AIRFLOW_IMAGE_NAME:-apache/airflow:2.7.1}
  env_file: .env
  volumes:
    - ${AIRFLOW_PROJ_DIR:-.}/airflow/dags:/opt/airflow/dags
    - ${AIRFLOW_PROJ_DIR:-.}/airflow/logs:/opt/airflow/logs
    - ${AIRFLOW_PROJ_DIR:-.}/airflow/config:/opt/airflow/config
    - ${AIRFLOW_PROJ_DIR:-.}/airflow/plugins:/opt/airflow/plugins
    - /var/run/docker.sock:/var/run/docker.sock
  user: "${AIRFLOW_UID:-50000}:0"
  depends_on:
    &airflow-common-depends-on
    postgres:
      condition: service_healthy

services:
  postgres:
    image: postgres:15
    container_name: postgres
    networks:
      - airflow
    env_file: .env
    ports: 
      - 5432:5432
    volumes:
      - postgres-db-volume:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "airflow"]
      interval: 10s
      retries: 5
      start_period: 5s
    restart: always

  # Airflow
  airflow-webserver:
    <<: *airflow-common
    command: webserver
    container_name: airflow-webserver
    networks:
      - airflow
    ports:
      - "8080:8080"
    healthcheck:
      test: ["CMD", "curl", "--fail", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s
    restart: always
    depends_on:
      <<: *airflow-common-depends-on
      airflow-init:
        condition: service_completed_successfully

  airflow-scheduler:
    <<: *airflow-common
    command: scheduler
    container_name: airflow-scheduler
    healthcheck:
      test: ["CMD", "curl", "--fail", "http://localhost:8974/health"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s
    restart: always
    networks:
      - airflow
    depends_on:
      <<: *airflow-common-depends-on
      airflow-init:
        condition: service_completed_successfully

  airflow-init:
    <<: *airflow-common
    entrypoint: /bin/bash
    container_name: airflow-init
    networks:
      - airflow
    # yamllint disable rule:line-length
    command:
      - -c
      - |
        function ver() {
          printf "%04d%04d%04d%04d" $${1//./ }
        }
        airflow_version=$$(AIRFLOW__LOGGING__LOGGING_LEVEL=INFO && gosu airflow airflow version)
        airflow_version_comparable=$$(ver $${airflow_version})
        min_airflow_version=2.2.0
        min_airflow_version_comparable=$$(ver $${min_airflow_version})
        if (( airflow_version_comparable < min_airflow_version_comparable )); then
          echo
          echo -e "\033[1;31mERROR!!!: Too old Airflow version $${airflow_version}!\e[0m"
          echo "The minimum Airflow version supported: $${min_airflow_version}. Only use this or higher!"
          echo
          exit 1
        fi
        if [[ -z "${AIRFLOW_UID}" ]]; then
          echo
          echo -e "\033[1;33mWARNING!!!: AIRFLOW_UID not set!\e[0m"
          echo "If you are on Linux, you SHOULD follow the instructions below to set "
          echo "AIRFLOW_UID environment variable, otherwise files will be owned by root."
          echo "For other operating systems you can get rid of the warning with manually created .env file:"
          echo "    See: https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html#setting-the-right-airflow-user"
          echo
        fi
        one_meg=1048576
        mem_available=$$(($$(getconf _PHYS_PAGES) * $$(getconf PAGE_SIZE) / one_meg))
        cpus_available=$$(grep -cE 'cpu[0-9]+' /proc/stat)
        disk_available=$$(df / | tail -1 | awk '{print $$4}')
        warning_resources="false"
        if (( mem_available < 4000 )) ; then
          echo
          echo -e "\033[1;33mWARNING!!!: Not enough memory available for Docker.\e[0m"
          echo "At least 4GB of memory required. You have $$(numfmt --to iec $$((mem_available * one_meg)))"
          echo
          warning_resources="true"
        fi
        if (( cpus_available < 2 )); then
          echo
          echo -e "\033[1;33mWARNING!!!: Not enough CPUS available for Docker.\e[0m"
          echo "At least 2 CPUs recommended. You have $${cpus_available}"
          echo
          warning_resources="true"
        fi
        if (( disk_available < one_meg * 10 )); then
          echo
          echo -e "\033[1;33mWARNING!!!: Not enough Disk space available for Docker.\e[0m"
          echo "At least 10 GBs recommended. You have $$(numfmt --to iec $$((disk_available * 1024 )))"
          echo
          warning_resources="true"
        fi
        if [[ $${warning_resources} == "true" ]]; then
          echo
          echo -e "\033[1;33mWARNING!!!: You have not enough resources to run Airflow (see above)!\e[0m"
          echo "Please follow the instructions to increase amount of resources available:"
          echo "   https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html#before-you-begin"
          echo
        fi
        mkdir -p /sources/logs /sources/dags /sources/plugins
        chown -R "${AIRFLOW_UID}:0" /sources/{logs,dags,plugins}
        exec /entrypoint airflow version
    # yamllint enable rule:line-length
    environment:
      _AIRFLOW_DB_UPGRADE: 'true'
      _AIRFLOW_WWW_USER_CREATE: 'true'
      _AIRFLOW_WWW_USER_USERNAME: ${_AIRFLOW_WWW_USER_USERNAME:-airflow}
      _AIRFLOW_WWW_USER_PASSWORD: ${_AIRFLOW_WWW_USER_PASSWORD:-airflow}
      _PIP_ADDITIONAL_REQUIREMENTS: ''
    user: "0:0"
    volumes:
      - ${AIRFLOW_PROJ_DIR:-.}/airflow/:/sources
  rustfs:
    restart: always
    container_name: rustfs
    image: rustfs/rustfs:latest
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
        - RUSTFS_ACCESS_KEY=dataops
        - RUSTFS_SECRET_KEY=Ankara06
        - RUSTFS_VOLUMES=/data
        - RUSTFS_ADDRESS=:9000
    volumes:
      - rustfs_data:/data
    networks:
      - airflow

  # Spark
  spark_client:  
    container_name: spark_client
    image: veribilimiokulu/pyspark:3.5.3_python-3.12_java17
    ports:
      - 8888:8888
      - 4040:4040
    networks:
      - airflow
    volumes:
      - spark:/dataops
    command:
      - /bin/bash
      - -c
      - |
        apt update && \
        apt install openssh-server sudo sshpass -y && \
        useradd -rm -d /home/ssh_train -s /bin/bash -g root -G sudo -u 1000 ssh_train && \
        echo 'ssh_train:Ankara06' | chpasswd && \
        service ssh start && \
        tail -f /dev/null

volumes:
  postgres-db-volume:
  airflow:
  rustfs_data:
  spark:

networks:
  airflow:
    driver: bridge
```

```bash
docker-compose up -d
```

## Create User and Database (PostgreSQL)

```bash
docker exec -it postgres psql -U airflow
```

```bash
create database traindb;
create user train with password 'Ankara06';
grant all privileges on database traindb to train;
grant all on schema public to train;
```

## Airflow Database Registration
![registration](images/1.png)

- Update and install packages

```bash
docker exec -it -u root airflow-scheduler bash
apt update
apt install -y wget
```

## Creating DAG

- `airflow_hw1_dag.py`

```python
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.operators.python import PythonOperator
from sqlalchemy import create_engine
import pandas as pd

def load_orders():
    df = pd.read_csv(
        "https://raw.githubusercontent.com/erkansirin78/datasets/master/retail_db/orders.csv"
    )

    engine = create_engine(
        "postgresql+psycopg2://train:Ankara06@postgres:5432/traindb"
    )

    df.to_sql(
        name="orders",
        schema="staging",
        con=engine,
        if_exists="replace",
        index=False
    )

def load_order_items():
    df = pd.read_csv(
        "https://raw.githubusercontent.com/erkansirin78/datasets/master/retail_db/order_items.csv"
    )

    engine = create_engine(
        "postgresql+psycopg2://train:Ankara06@postgres:5432/traindb"
    )

    df.to_sql(
        name="order_items",
        schema="staging",
        con=engine,
        if_exists="replace",
        index=False
    )

def load_products():
    df = pd.read_csv(
        "https://raw.githubusercontent.com/erkansirin78/datasets/master/retail_db/products.csv"
    )

    engine = create_engine(
        "postgresql+psycopg2://train:Ankara06@postgres:5432/traindb"
    )

    df.to_sql(
        name="products",
        schema="staging",
        con=engine,
        if_exists="replace",
        index=False
    )

start_date = datetime(2026, 6, 6)

default_args = {
    'owner': 'airflow',
    'start_date': start_date,
    'retries': 1,
    'retry_delay': timedelta(seconds=5)
}

with DAG('airflow_hw1_dag', default_args=default_args, schedule_interval='@hourly', catchup=False) as dag:

    t1 = SQLExecuteQueryOperator(
        task_id="create_schema_staging",
        conn_id='postgresql_conn',
        sql="""CREATE SCHEMA IF NOT EXISTS staging;"""
    )

    t2 = PythonOperator(
        task_id="load_orders",
        python_callable=load_orders
    )

    t3 = PythonOperator(
        task_id="load_order_items",
        python_callable=load_order_items
    )

    t4 = PythonOperator(
        task_id="load_products",
        python_callable=load_products
    )

    t5 = SQLExecuteQueryOperator(
        task_id="create_schema_serving",
        conn_id='postgresql_conn',
        sql="""CREATE SCHEMA IF NOT EXISTS serving;"""
    )

    t6 = SQLExecuteQueryOperator(
        task_id="create_view",
        conn_id="postgresql_conn",
        sql="""
            CREATE OR REPLACE VIEW serving.v_product_status_track AS
            SELECT *
            FROM staging.orders o
            JOIN staging.order_items oi
            ON oi."orderItemOrderId" = o."orderId"
            JOIN staging.products p
            ON p."productId" = oi."orderItemProductId";
        """
    )

    t1 >> t2 >> t3 >> t4 >> t5 >> t6
```
- Airflow Web UI:

![airflow_dag](images/2.png)

- Trigger (Run) Script

![airflow_dag_graph](images/3.png)

## Verification on DBeaver

```sql
SELECT COUNT(*) FROM serving.v_product_status_track;
```

![sql_count](images/4.png)

```sql
SELECT * FROM serving.v_product_status_track LIMIT 5;
```

![sql_sample](images/5.png)