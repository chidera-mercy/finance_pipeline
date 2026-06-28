from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.standard.operators.python import PythonOperator

default_args = {
    "owner": "mercy",
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
    "email_on_failure": False
}

def _run_exchange_rates():
    from ingest.exchange_rates import run
    run()

def _run_inflation():
    from ingest.inflation import run
    run()

def _run_interest_rates():
    from ingest.interest_rates import run
    run()

def _run_ngx_asi():
    from ingest.ngx_asi import run
    run()

def _run_gold_prices():
    from ingest.gold_prices import run
    run()


with DAG(
    dag_id="finance_pipeline",
    default_args=default_args,
    description="Ingest FX, inflation, interest rates, NGX ASI, and gold, then run dbt",
    schedule="0 6 * * *",
    start_date=datetime(2026, 6, 20),
    catchup=False,
    tags=["finance", "data_engineering"]
) as dag:

    ingest_exchange_rates = PythonOperator(
        task_id="ingest_exchange_rates",
        python_callable=_run_exchange_rates
    )

    ingest_inflation = PythonOperator(
        task_id="ingest_inflation",
        python_callable=_run_inflation
    )

    ingest_interest_rates = PythonOperator(
        task_id="ingest_interest_rates",
        python_callable=_run_interest_rates
    )

    ingest_ngx_asi = PythonOperator(
        task_id="ingest_ngx_asi",
        python_callable=_run_ngx_asi
    )

    ingest_gold_prices = PythonOperator(
        task_id="ingest_gold_prices",
        python_callable=_run_gold_prices
    )

    run_dbt = BashOperator(
        task_id="run_dbt_transformations",
        bash_command="cd /opt/airflow/finance_dbt && dbt run --profiles-dir /opt/airflow",
        retries=0
    )

    test_dbt = BashOperator(
        task_id="test_dbt_models",
        bash_command="cd /opt/airflow/finance_dbt && dbt test --profiles-dir /opt/airflow",
        retries=0
    )

    ingestion_tasks = [
        ingest_exchange_rates,
        ingest_inflation,
        ingest_interest_rates,
        ingest_ngx_asi,
        ingest_gold_prices
    ]

    ingestion_tasks >> run_dbt >> test_dbt
