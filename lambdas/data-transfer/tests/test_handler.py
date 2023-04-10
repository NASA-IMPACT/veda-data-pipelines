import handler


def test_handler(mock_src_bucket, mock_dst_bucket):
    test_data = b"test-object"
    test_object = mock_src_bucket.put_object(Body=test_data, Key="test-key")
    test_event = {
        "upload": 1,
        "remote_fileurl": f"s3://{test_object.bucket_name}/{test_object.key}",
        "collection": "test_collection",
        "directory": "",
    }

    response = handler.handler([test_event], None)

    expected_bucket = mock_dst_bucket.name
    expected_path = "/".join([test_event["collection"], test_object.key])
    assert response == [
        {
            **test_event,
            "remote_fileurl": f"s3://{expected_bucket}/{expected_path}",
        }
    ]
    assert mock_dst_bucket.Object(expected_path).get()["Body"].read() == test_data
