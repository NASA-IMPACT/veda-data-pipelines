from airflow import DAG
from airflow.operators.dummy_operator import DummyOperator
from veda_data_pipeline.groups.processing_group import subdag_process
from airflow.utils.trigger_rule import TriggerRule
import pendulum

dag_args = {
    "start_date": pendulum.today("UTC").add(days=-1),
    "schedule_interval": None,
    "catchup": False,
}

with DAG("veda_ingest", **dag_args) as dag:
    start = DummyOperator(task_id="Start", dag=dag)
    end = DummyOperator(task_id="End", trigger_rule=TriggerRule.ONE_SUCCESS, dag=dag)

    process_grp = subdag_process()

    start >> process_grp >> end
