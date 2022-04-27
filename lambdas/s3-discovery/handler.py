import boto3

s3 = boto3.resource(
    "s3",
)

def list_bucket(bucket, prefix, file_type):
    try:
        files = []
        bucket = s3.Bucket(bucket)
        for obj in bucket.objects.filter(Prefix=prefix):
            if file_type:
                if obj.key.endswith(file_type):
                    files.append(obj)
            else:
                files.append(obj.key)
        return files

    except Exception as e:
        print(e)
    return e


def handler(event, context):
    filenames = list_bucket(
        bucket=event["bucket"], prefix=event["prefix"], file_type=event["file_type"]
    )

    files_objs = []
    for obj in filenames:
        print(obj);

        res = {
            # Remove trailing back slash used for prefixing
            "collection": event["prefix"][:-1],
            "s3_filename": f's3://{event["bucket"]}/{obj.key}',
            "s3_datetime": obj.last_modified.isoformat()
        }

        if event.get('datetime_regex') is not None:
            res["datetime_regex"] = event["datetime_regex"],

        files_objs.append(res)

    return files_objs


if __name__ == "__main__":
    sample_event = {
        "bucket": "climatedashboard-data",
        # Directory
        "prefix": "OMSO2PCA-COG/",
        # File type
        "file_type": ".tif",
        "datetime_regex": {
            "regex": f"^(.*?)(_)([0-9][0-9][0-9][0-9])(.*?)(.tif)$",
            "target_group": [3]
        }
    }

    handler(sample_event, {})
