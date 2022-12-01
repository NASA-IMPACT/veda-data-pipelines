from airflow.utils.task_group import TaskGroup
from airflow.operators.python import PythonOperator, BranchPythonOperator
from veda_data_pipeline.src.s3_discovery import s3_discovery_handler
import os
import json
import time



group_kwgs = {
    "group_id": "Discover",
    "tooltip": "Discover"
}

def get_payload(ti_xcom_pull):
    task_ids=[f"{group_kwgs['group_id']}.discover_from_s3", f"{group_kwgs['group_id']}.discover_from_cmr"]
    return [ payload for payload in ti_xcom_pull(task_ids=task_ids) if payload is not None][0]


def discover_from_cmr_task(ti, text):

    payload = {
    "collection": "lis-tws-nonstationarity-index",
    "prefix": "EIS/Global_TWS_data/DATWS_nonstationarity_index_v2.cog.tif",
    "bucket": "veda-data-store-staging",
    "filename_regex": "^(.*).tif$",
    "discovery": "cmr",
    "start_datetime": "2003-01-01T00:00:00Z",
    "end_datetime": "2020-01-01T00:00:00Z",
    "upload": False,
    "cogify": True,
    "objects": [
      {
        "collection": "lis-tws-nonstationarity-index",
        "s3_filename": "s3://veda-data-store-staging/EIS/Global_TWS_data/DATWS_nonstationarity_index_v2.cog.tif",
        "upload": False,
        "properties": {},
        "start_datetime": "2003-01-01T00:00:00Z",
        "end_datetime": "2020-01-01T00:00:00Z"
      }
    ]
  }
    ti.xcom_push(key="payload", value = payload)
    return {"text": text}

def discover_from_s3_task(ti):
    config = ti.dag_run.conf
    return s3_discovery_handler(config)

def run_process_task(ti):
    payload = get_payload(ti.xcom_pull)

    payloads_xcom = payload.pop('payload', [])
    for payload_xcom in payloads_xcom:
        event = {**payload, 'payload': [payload_xcom]}
        os.system(f"airflow dags trigger --conf \'{json.dumps(event)}\' veda_ingest_pipeline")
        time.sleep(2)

    return 

def discover_choice(ti):

    config = ti.dag_run.conf

    supported_discoveries = {
        "s3": "discover_from_s3",
        "cmr": "discover_from_cmr"
    }
    
    
    return f"{group_kwgs['group_id']}.{supported_discoveries[config['discovery']]}"


def subdag_discover():
    with TaskGroup(
        **group_kwgs
    ) as discover_grp:
        discover_branching = BranchPythonOperator(
        task_id="discover_branching",
        python_callable = discover_choice
    )

        discover_from_cmr = PythonOperator(
            task_id="discover_from_cmr",
            python_callable=discover_from_cmr_task,
            op_kwargs={'text': "Discover from CMR"}

    )
        discover_from_s3 = PythonOperator(
            task_id="discover_from_s3",
            python_callable=discover_from_s3_task,
            op_kwargs={'text': "Discover from S3"}
      
    )


        discover_branching >> [discover_from_cmr, discover_from_s3]
        return discover_grp