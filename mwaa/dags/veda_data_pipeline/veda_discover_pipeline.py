from airflow import DAG
from airflow.operators.dummy_operator import DummyOperator
from veda_data_pipeline.groups.discover_group import subdag_discover
import pendulum



dag_args = {
    "start_date": pendulum.today('UTC').add(days=-1),
    "schedule_interval": None,
    "catchup": False
}
 

with DAG('veda_pipeline_discover', **dag_args) as dag:
    start = DummyOperator(
        task_id="Start",
        dag=dag
    )
    end = DummyOperator(
        task_id="End",
        trigger_rule = "one_success",
        dag=dag
    )
    

    discover_grp = subdag_discover()

    start >> discover_grp  >> end
