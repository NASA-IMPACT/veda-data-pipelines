---
name: Add a new dataset to the API (high-level steps)
about: All steps for adding a new dataset or indicator to the VEDA STAC API
title: Add a new dataset to the API (high-level steps)
labels: 'dataset'
assignees: ''

---

**NOTE:** The dataset ingest + publication workflows are currently undergoing a refactor in this branch: https://github.com/NASA-IMPACT/cloud-optimized-data-pipelines/tree/refactor

For each dataset, we will follow the following steps:

## Identify the dataset and what the processing needs are
1. Identify dataset and where it will be accessed from. Check it's a good source with science team. Ask about specific variables and required spatial and temporal extent. Note most datasets will require back processing (e.g. generating cloud-optimized data for historical data).
2. If the dataset is ongoing (i.e. new files are continuously added and should be included in the dashboard), design and construct the forward-processing workflow. 
    - Each collection will have a workflow which includes discovering data files from the source, generating the cloud-optimized versions of the data and writing STAC metadata.
   - Each collection will have different requirements for both the generation and scheduling of these steps, so a design step much be included for each new collection / data layer.
3. If appropriate, create COG conversion code and verify the COG output with a data product expert (for example, someone at the DAAC which hosts the native format) by sharing in a visual interface.

## Design the metadata and publish to the Dev API

1. Review conventions for generating STAC collection and item metadata:
   - Collections: https://github.com/NASA-IMPACT/delta-backend/issues/29 and STAC version 1.0 specification for collections
   - Items: https://github.com/NASA-IMPACT/delta-backend/issues/28 and STAC version 1.0 specification for items
   - NOTE: The delta-backend instructions are specific to datasets for the climate dashboard, however not all datasets are going to be a part of the visual layers for the dashboard so I believe you can ignore the instructions that are specific to "dashboard" extension, "item_assets" in the collection and "cog_default" asset type in the item.

A collection will need the following fields, some of which may be self-evident through the filename or an about page for the product, however there are many cases in which we may need to reach out to product owners to define the right values for these fields:

- temporal interval
- license
- id
- title
- description
- whether it is periodic or not on the dashboard
- the dashboard time density
  
2. After reviewing the STAC documentation for collections and items and reviewing existing scripts for generating collection metadata (generally with SQL) and item metadata, generate or reuse scripts for your collection and a few items to publish to the testing API. There is some documentation and examples for how to generate a pipeline or otherwise document your dataset workflow in https://github.com/NASA-IMPACT/cloud-optimized-data-pipelines. We would like to maintain the scripts folks are using to publish datasets in that repo so we can easily re-run those datasets ingest and publish workflows if necessary.

3.  If necessary, request access and credentials to the dev database and ingest and publish to the Dev API. Submit a PR with the manual or CDK scripts used to run the workflow to publish to the Dev API and include links to the published datasets in the Dev API


## Publish to the Staging API

Once the PR is approved, we can merge and publish those datasets to the Staging API
