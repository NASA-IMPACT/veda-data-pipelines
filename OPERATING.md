# Operating Guide: Data Transformation and Ingest for VEDA

This guide provides information on how VEDA runs data ingest, transformation and metadata (STAC) publication workflows via AWS Services, such as step functions.

## Data

### `collections/`

The `collections/` directory holds json files representing the data for VEDA collection metadata (STAC).

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

### `step_function_inputs/`

The `step_function_inputs/` directory holds json files representing the step function inputs for initiating the discovery, ingest and publication workflows.
Can either be a single input event or a list of input events.

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

Done by passing the collection json to the `submit-stac` lambda.

Create a collection json file in the `data/collections/` directory. For format, check the [data](#data) section.

```bash
poetry run insert-collection <collection-name-start-pattern>
```

### Ingesting items to a collection

Done by passing an input json to the discovery step function workflow.

Create an input json file in the `data/step_function_inputs/` directory. For format, check the [data](#data) section.

```bash
poetry run insert-item <event-json-start-pattern>
```

## Glossary

### Lambdas

#### 1. s3-discovery

Discovers all the files in an S3 bucket, based on the prefix and filename regex.

#### 2. cmr-query

Discovers all the files in a CMR collection, based on the version, temporal, bounding box, and include. Returns objects that follow the specified criteria.

#### 3. cogify

Converts the input file to a COG file, writes it to S3, and returns the S3 key.

#### 4. data-transfer

Copies the data to the VEDA MCP bucket if necessary.

#### 5. build-stac

Given an object received from the `STAC_READY_QUEUE`, builds a STAC Item, writes it to S3, and returns the S3 key.

#### 6. submit-stac

Submits STAC items to STAC Ingestor system via POST requests.

#### 7. proxy

Reads objects from the specified queue in batches and invokes the specified step function workflow with the objects from the queue as the input.

### Step Function Workflows

#### 1. Discover

Discovers all the files that need to be ingested either from s3 or cmr.

#### 2. Cogify

Converts the input files to COGs, runs in parallel.

#### 3. Publication

Publishes the item to the STAC database (and MCP bucket if necessary).
