from cmr import CollectionQuery, GranuleQuery
import json
import boto3

batch_client = boto3.client('batch')

def get_link(granule, link_title):
    hrefs = [link['href'] for link in granule['links']]
    if link_title:
        titles = [link['title'] if 'title' in link else None for link in granule['links']]
        href_index = titles.index(link_title)
    else:
        href_index = 0
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
    link_title = event['link_title']
    cmr_host = event['cmr_host'] if 'host' in event else 'https://cmr.earthdata.nasa.gov/search/'
    api = GranuleQuery(mode = cmr_host)
    granules = api.short_name(collection_short_name).get(20)
    statuses = []
    for granule in granules:
        print(json.dumps(granule, indent=2))
        s3_link = get_link(granule, link_title)
        print(s3_link)
      #response = submit_job(event, s3_link)
      #statuses.append(response['ResponseMetadata']['HTTPStatusCode'])
    return #statuses


event = {
    'collection_short_name': 'GPM_3IMERGDF',
    'link_title': None,
    'job_name': 'imerg-conversion-lambda',
    'job_queue': 'default-job-queue',
    'job_def': 'hdf5_to_cog_batch_job_def:2'
}
print(lambda_handler(event = event, context={}))
