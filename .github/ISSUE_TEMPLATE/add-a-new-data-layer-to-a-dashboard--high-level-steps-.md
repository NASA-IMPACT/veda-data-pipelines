---
name: Add a new dataset to the API (high-level steps)
about: All steps for adding a new dataset or indicator to the VEDA STAC API
title: Add a new dataset to the API (high-level steps)
labels: 'dataset'
assignees: ''

---

# Research + prepare processing for the dataset: Identify the dataset and what the processing needs are

1. Identify dataset and where it will be accessed from (HTTP from DAAC vs S3, for example). Check it's a good source with science team. Ask about specific variables and required spatial and temporal extent. Note many datasets will require back processing (e.g. generating cloud-optimized data for historical data).

    [Future: 2. If the dataset is ongoing (i.e. new files are continuously added and should be included in the dashboard), design and construct the scheduling + forward-processing workflow.]

2. If necessary, create COG or any other conversion / processing code and verify the COG output with a data product expert (for example, someone at the DAAC which hosts the native format) by sharing in a visual interface.

3. Identify the point of contact and ensure someone is providing them updates!

# Design the metadata and publish to the Dev API

1. If not already familiar with these conventions for generating STAC collection and item metadata:
       - Collections: https://github.com/NASA-IMPACT/delta-backend/issues/29 and STAC version 1.0 specification for collections
       - Items: https://github.com/NASA-IMPACT/delta-backend/issues/28 and STAC version 1.0 specification for items
       - NOTE: The delta-backend instructions are specific to datasets for the climate dashboard, however not all datasets are going to be a part of the visual layers for the dashboard so you can ignore the instructions that are specific to "dashboard" extension, "item_assets" in the collection and "cog_default" asset type in the item.

      A collection will need the following fields, some of which may be self-evident through the filename or an about page for the product, however there are many cases in which we may need to reach out to product owners to define the right values for these fields:
      
      - temporal interval
      - license
      - id
      - title
      - description
      - whether it is periodic or not on the dashboard
      - the dashboard time density
  
4. Review and follow https://github.com/NASA-IMPACT/cloud-optimized-data-pipelines/blob/main/OPERATING.md


## Publish to the Staging API

Once the PR is approved, we can merge and publish those datasets to the Staging API

