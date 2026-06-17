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