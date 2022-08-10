Docker to query CMR for granules associated with a given collection and temporal range.

```bash
docker build -t cmr-query .
# Currently runs an example for OMI Ozone
docker run cmr-query python -m handler
```

Example input:
```
{
    "hours": 240,
    "collection": "OMDOAO3e",
    "version": "003",
    "include": "^.+he5$",
}
```

Example output:
```
{
    "collection": xxx,
    "href": xxx,
    "granule_id": xxx,
    "upload": True,
}
```
