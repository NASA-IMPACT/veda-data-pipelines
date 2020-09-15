from cmr import CollectionQuery, GranuleQuery
import json
import boto3

batch_client = boto3.client('batch')
api = GranuleQuery(mode="https://cmr.maap-project.org/search/")

def get_s3_link(granule):
    hrefs = [link['href'] for link in granule['links']]
    titles = [link['title'] if 'title' in link else None for link in granule['links']]
    href_index = titles.index('File to download')
    return hrefs[href_index]

def submit_job(event, s3_link):
    response = batch_client.submit_job(
        jobName=event['job_name'],
        jobQueue=event['job_queue'],
        jobDefinition=event['job_def'],
        containerOverrides={
            'command': [
                'python',
                'run.py',
                '-f',
                s3_link
            ]
        }     
    )
    return response

def lambda_handler(event, context):
    collection_short_name = event['collection_short_name']
    granules = api.short_name(collection_short_name).get(20)
    statuses = []
    for granule in granules:
      s3_link = get_s3_link(granule)
      response = submit_job(event, s3_link)
      statuses.append(response['ResponseMetadata']['HTTPStatusCode'])
    return statuses


event = {
    'collection_short_name': 'GPM_3IMERGHH',
    'job_name': 'imerg-conversion-lambda',
    'job_queue': 'default-job-queue',
    'job_def': 'hdf5_to_cog_batch_job_def:2'
}
# print(lambda_handler(event = event, context={}))
