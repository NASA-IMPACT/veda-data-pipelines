from airflow.utils.task_group import TaskGroup
from airflow.providers.amazon.aws.operators.ecs import ECSOperator
from airflow.operators.python import PythonOperator, BranchPythonOperator
import time
import logging
from airflow.models.variable import Variable
group_kwgs = {
    "group_id": "Process",
    "tooltip": "Process"
}


def log_task(text: str):
    logging.info(text)


def submit_to_stac_ingestor_task(ti):
    print("Submit STAC ingestor")
    events = ti.xcom_pull(task_ids=f"{group_kwgs['group_id']}.build_stac")
    return events

def cogify_task(ti):
    payload = ti.dag_run.conf
    # print(f"======\n{payload}\n======")
    log_task("I am cogifying")
    time.sleep(5)
    log_task("Done cogifying")
    log_task("COGIFYING")


def cogify_choice(ti, **kwargs):
    # Only get the payload from the successful task
    payload = ti.dag_run.conf
    if payload['cogify']:
        return f"{group_kwgs['group_id']}.cogify"

    return f"{group_kwgs['group_id']}.build_stac"


def subdag_process():
    with TaskGroup(

            **group_kwgs
    ) as process_grp:
        cogify_branching = BranchPythonOperator(
            task_id="cogify_branching",
            trigger_rule='one_success',
            python_callable=cogify_choice
        )

        build_stac = ECSOperator(
            task_id='build_stac',
            cluster="veda-uah-dev-cluster",
            task_definition="veda_tasks",
            launch_type="FARGATE",
            do_xcom_push=True,
            overrides={
                "containerOverrides": [
                    {
                        "name": f"{Variable.get('PREFIX')}-veda-stac-build",
                        "command": ["/usr/local/bin/python", "handler.py", "--payload",
                                    '{}'.format("{{ task_instance.dag_run.conf }}")],
                        "environment": [{"name": "EXTERNAL_ROLE_ARN",
                                         "value": "arn:aws:iam::114506680961:role/veda-data-store-read-staging"},
                                        {"name": "BUCKET", "value": "veda-data-pipelines-staging-lambda-ndjson-bucket"},
                                        {"name": "EVENT_BUCKET", "value": Variable.get('EVENT_BUCKET')}
                                        ],
                        "memory": 2048,
                        "cpu": 1024
                    },
                ],
            },
            network_configuration={
                "awsvpcConfiguration": {
                    "securityGroups": ["sg-0a60e15209e381cef"],
                    "subnets": ["subnet-050c11a80c47b50e9", "subnet-0f3643ae200be05af"],
                },
            },
            awslogs_group=f"{Variable.get('PREFIX')}-stac_tasks",
            awslogs_stream_prefix=f"ecs/{Variable.get('PREFIX')}-veda-stac-build",  # prefix with container name
        )
        cogify = PythonOperator(
            task_id="cogify",
            python_callable=cogify_task

        )
        submit_to_stac_ingestor = PythonOperator(
            task_id="submit_to_stac_ingestor",
            python_callable=submit_to_stac_ingestor_task

        )
        cogify_branching >> build_stac >> submit_to_stac_ingestor
        cogify_branching >> cogify
        return process_grp