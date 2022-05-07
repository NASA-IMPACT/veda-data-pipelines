import boto3
import re

s3 = boto3.resource(
    "s3",
)

def list_bucket(bucket, prefix, filename_regex):
    try:
        files = []
        bucket = s3.Bucket(bucket)
        for obj in bucket.objects.filter(Prefix=prefix):
            if filename_regex:
                if re.match(filename_regex, obj.key):
                    files.append(obj.key)
            else:
                files.append(obj.key)
        return files

    except Exception as e:
        print(e)
    return e


def handler(event, context):
    filenames = list_bucket(
        bucket=event["bucket"], prefix=event.get("prefix"), filename_regex=event.get("filename_regex")
    )

    files_objs = []
    cogify = event.pop("key", False)
    bucket = event.get("bucket")
    collection = event.get("collection", event["prefix"][:-1])
    for filename in filenames:
        files_objs.append(
            {
                "filename_regex": event.get("filename_regex"),
                "datetime_range": event.get("datetime_range"),
                # Remove trailing back slash used for prefixing
                "collection": collection,
                "s3_filename": f's3://{bucket}/{filename}',
                "id": filename,
            }
        )
    return {
        "cogify": cogify,
        "objects": files_objs
    }


if __name__ == "__main__":
    sample_event = {
        "bucket": "climatedashboard-data",
        "prefix": "social_vulnerability_index/",
        "file_type": ".tif",
        "filename_regex": "^(.*)_housing_(.*)$",
        "collection": "social-vulnerability-index-housing",
        "upload_cog": True,
        "cogify": False,
    }

    handler(sample_event, {})
