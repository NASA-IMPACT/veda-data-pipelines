# Operating: data transformation and ingest for VEDA

## Data

### `collections/`

Holds collection jsons

Should follow the following format:

```json
{
    "id": "<collection-id>",
    "type": "Collection",
    "links":[
    ],
    "title":"<collection-title>",
    "extent":{
        "spatial":{
            "bbox":[
                [
                    "<min-longitude>",
                    "<min-latitude>",
                    "<max-longitude>",
                    "<max-latitude>",
                ]
            ]
        },
        "temporal":{
            "interval":[
                [
                    "<start-date>",
                    "<end-date>",
                ]
            ]
        }
    },
    "license":"MIT",
    "description": "<collection-description>",
    "stac_version": "1.0.0",
    "dashboard:is_periodic": "<true/false>",
    "dashboard:time_density": "<month/>day/year>",
    "item_assets": {
        "cog_default": {
            "type": "image/tiff; application=geotiff; profile=cloud-optimized",
            "roles": [
                "data",
                "layer"
            ],
            "title": "Default COG Layer",
            "description": "Cloud optimized default layer to display on map"
        }
    }
}

```

### `events/`

Holds jsons of events passed to the ingestion pipeline.
Can either be a single event or a list of events.

Should follow the following format:

```json
{
    "collection": "<collection-id>",
    "discovery": "<s3/cmr>",

    ## for s3 discovery
    "prefix": "<s3-key-prefix>",
    "bucket": "<s3-bucket>",
    "filename_regex": "<filename-regex>",
    "datetime_range": "<month/day/year>",
    
    ## for cmr discovery
    "version": "<collection-version>",
    "temporal": ["<start-date>", "<end-date>"],
    "bounding_box": ["<bounding-box-as-comma-separated-LBRT>"],
    "include": "<filename-pattern>",
    
    ### misc
    "cogify": "<true/false>",
    "upload": "<true/false>",
    "dry_run": "<true/false>",
}
```

## Ingestion

Install dependencies:

```bash
poetry install
```

### Ingesting a collection

Done by passing the collection json to the `db-write` lambda.

Create a collection json file in the `data/collections/` directory. For format, check the [data](#data) section.

```bash
poetry run insert-collection <collection-name-start-pattern>
```

### Ingesting items to a collection

Done by passing event json to the discovery step function workflow.

Create an event json file in the `data/events/` directory. For format, check the [data](#data) section.

```bash
poetry run insert-item <event-json-start-pattern>
```

## Glossary

### Lambdas

#### 1. s3-discovery

Discovers all the files in an S3 bucket, based on the prefix and filename regex.

#### 2. cmr-query

Discovers all the files in a CMR collection, based on the version, temporal, bounding box, and include. Returns objects that follow the specified criteria.

#### 3. cogify-or-not

Based on the `cogify` flag, either writes the objects to a `COGIFY_QUEUE` or `STAC_READY_QUEUE`.

#### 4. cogify

Converts the input file to a COG file, writes it to S3, and returns the S3 key.

#### 5. build-ndjson

Based on the objects received from the `STAC_READY_QUEUE` in batches, builds a bulk ndjson file, writes it to S3, and returns the S3 key.

#### 6. db-write

Loads either the bulk ndjson file (from s3) or a json collection file into the pgstac database.

#### 7. proxy

Reads objects from the specified queue in batches and invokes the specified step function workflow with the objects from the queue as the input.

### Step Function Workflows

#### 1. Discover

Discovers all the files that need to be ingested either from s3 or cmr.

#### 2. Cogify

Converts the input files to COGs, runs parallely.

#### 3. Publication

Publishes the item to the STAC.
