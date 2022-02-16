This handler expects a STAC_ITEM to be provided in JSON format. It then performs an insert operation into a remote database, specified via command line.

```bash
docker build -t db-write.
# Currently runs an example for OMI Ozone
docker run --env STAC_DB_USER=<user> --env STAC_DB_PASSWORD=<pw> --env STAC_DB_HOST=<host> db-write python -m handler
```

Example Input:
```
{
    "stac_item": {
        "assets": {
            "cog": {
                "href": "s3://climatedashboard-data/BMHD_Ida/BMHD_Ida2021_NO_LA_August9.tif",
                "roles": ["data"],
                "title": "COG",
                "type": "image/tiff; application=geotiff",
            }
        },
        "bbox": [
            -90.3037818244749,
            29.804659612978707,
            -89.87578181971654,
            30.07177072705947,
        ],
        "collection": "BMHD_Ida",
        "geometry": {
            "coordinates": [
                [
                    [-90.3037818244749, 30.07177072705947],
                    [-90.3037818244749, 29.804659612978707],
                    [-89.87578181971654, 29.804659612978707],
                    [-89.87578181971654, 30.07177072705947],
                    [-90.3037818244749, 30.07177072705947],
                ]
            ],
            "type": "Polygon",
        },
        "id": "BMHD_Ida2021_NO_LA_August9.tif",
        "links": [
            {
                "href": "BMHD_Ida",
                "rel": "collection",
                "type": "application/json",
            }
        ],
        "properties": {
            "datetime": "2021-08-09T00:00:00Z",
            "proj:bbox": [
                -90.3037818244749,
                29.804659612978707,
                -89.87578181971654,
                30.07177072705947,
            ],
            "proj:epsg": 4326,
            "proj:geometry": {
                "coordinates": [
                    [
                        [-90.3037818244749, 30.07177072705947],
                        [-90.3037818244749, 29.804659612978707],
                        [-89.87578181971654, 29.804659612978707],
                        [-89.87578181971654, 30.07177072705947],
                        [-90.3037818244749, 30.07177072705947],
                    ]
                ],
                "type": "Polygon",
            },
            "proj:shape": [2404, 3852],
            "proj:transform": [
                0.00011111111234640703,
                0.0,
                -90.3037818244749,
                0.0,
                -0.00011111111234640703,
                30.07177072705947,
                0.0,
                0.0,
                1.0,
            ],
        },
        "stac_extensions": [
            "https://stac-extensions.github.io/projection/v1.0.0/schema.json",
            "https://stac-extensions.github.io/raster/v1.1.0/schema.json",
        ],
        "stac_version": "1.0.0",
        "type": "Feature",
    }
}
```
