import os

from datetime import datetime

from airflow import DAG

from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

from ingest_script import ingest_callable


AIRFLOW_HOME = os.environ.get("AIRFLOW_HOME", "/opt/airflow/")


PG_HOST = os.getenv('PG_HOST')
PG_USER = os.getenv('PG_USER')
PG_PASSWORD = os.getenv('PG_PASSWORD')
PG_PORT = os.getenv('PG_PORT')
PG_DATABASE = os.getenv('PG_DATABASE')


local_workflow = DAG(
    "LocalIngestionDag",
    schedule_interval="0 6 2 * *",
    start_date=datetime(2019, 1, 1)
)

URL_PREFIX = 'https://github.com/DataTalksClub/nyc-tlc-data/releases/download' 
URL_TEMPLATE = URL_PREFIX + '/yellow/yellow_tripdata_{{ execution_date.strftime(\'%Y-%m\') }}.csv.gz'
COMPRESSED_FILE_TEMPLATE = AIRFLOW_HOME + '/output_{{ execution_date.strftime(\'%Y_%m\') }}.csv.gz'
CSV_FILE_TEMPLATE = AIRFLOW_HOME + '/output_{{ execution_date.strftime(\'%Y_%m\') }}.csv'
TABLE_NAME_TEMPLATE = 'yellow_taxi_{{ execution_date.strftime(\'%Y_%m\') }}'


with local_workflow:
    wget_task = BashOperator(
        task_id='wget',
        bash_command=f'curl -sSL {URL_TEMPLATE} > {COMPRESSED_FILE_TEMPLATE}'
    )

    decompress_task = BashOperator(
        task_id='decompress',
        bash_command=f'gzip -d {COMPRESSED_FILE_TEMPLATE}'
    )

    ingest_task = PythonOperator(
        task_id="ingest",
        python_callable=ingest_callable,
        op_kwargs=dict(
            user=PG_USER,
            password=PG_PASSWORD,
            host=PG_HOST,
            port=PG_PORT,
            db=PG_DATABASE,
            table_name=TABLE_NAME_TEMPLATE,
            csv_file=CSV_FILE_TEMPLATE
        )
    )

    wget_task >> decompress_task >> ingest_task