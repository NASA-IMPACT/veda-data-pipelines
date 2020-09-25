import datetime
import json
import boto3

batch_client = boto3.client("batch")

# TODO: DRY with discover granules cmr lambda
def submit_job(job):
    response = batch_client.submit_job(
        jobName=f'{job.get("jobName")}-retry',
        jobQueue=job.get("jobQueue"),
        jobDefinition=job.get("jobDefinition"),
        containerOverrides={
            "command": job.get("container").get("command")
        }     
    )
    return response

response = batch_client.list_jobs(
    jobQueue='default-job-queue',
    jobStatus='FAILED',
    maxResults=100,
    #nextToken='string'
)

# parameters for job query
jobName = 'imerg-conversion-lambda'
hours_ago = 2
timenow = datetime.datetime.now()
timeago = 1000*(timenow - datetime.timedelta(hours=hours_ago)).timestamp()

job_ids_to_rerun = []
for job in response['jobSummaryList']:
    if job.get('jobName') == jobName and job.get('startedAt') > timeago:
        job_ids_to_rerun.append(job.get('jobId'))

response = batch_client.describe_jobs(jobs=job_ids_to_rerun)
jobs_to_rerun = response['jobs']
statuses = []
for job in jobs_to_rerun:
    response = submit_job(job)
    statuses.append(response["ResponseMetadata"]["HTTPStatusCode"])

print(statuses)
