Docker to query STAC for items associated with a given collection and temporal range.

...Used for copying from one STAC catalog to this one :grimace:

```bash
docker build -t stac-query .
docker run stac-query python -m handler
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
