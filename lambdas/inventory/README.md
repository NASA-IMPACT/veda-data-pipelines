Docker to read an inventory file from S3 and queue all urls.

Assumes the file is a CSV in an accessible S3 location.

Example input:

```json
{
    "collection": "icesat2-boreal",
    "inventory_url": "s3://maap-data-store-test/AGB_tindex_master.csv",
    "discovery": "inventory",
    "file_url_key": "s3_path",
    "upload": true
}
```

Example output:

```json
{
  "collection": "icesat2-boreal",
  "inventory_url": "s3://maap-data-store-test/AGB_tindex_master.csv",
  "discovery": "inventory",
  "file_url_key": "s3_path",
  "upload": true,
  "cogify": false,
  "objects": [ ... ],
  "start_after": 795
}
```