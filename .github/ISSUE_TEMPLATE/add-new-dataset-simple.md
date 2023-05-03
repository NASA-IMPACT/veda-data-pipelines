---
name: Add a new dataset to the API (simple)
about: Gathering information for dataset ingestion
title: Add <dataset title>
labels: 'dataset'
assignees: ''

---

- [ ] Identify the point of contact and ensure someone is providing them updates:
- [ ] Data provider has read [guidelines on data preparation](https://github.com/NASA-IMPACT/veda-workflows-api/blob/main/how-to.md#prepare-the-data)
- [ ] Identify data location:
- [ ] Number of items:
- [ ] Verify that files are valid COGs (e.g. with [`rio cogeo validate`](https://cogeotiff.github.io/rio-cogeo/Is_it_a_COG/#3-cog-validation))
- [ ] Gather STAC collection metadata

  - id:
  - title:
  - description:
  - license:
  - provider(s): (producer, processor, licensor)
  - temporal interval:
  - whether it is periodic on the dashboard (periodic = regular time series of layers without gaps):
  - the dashboard time density:

- [ ] Review and follow https://github.com/NASA-IMPACT/cloud-optimized-data-pipelines/blob/main/OPERATING.md
- [ ] Open PR for publishing those datasets to the Staging API:
- [ ] Notify QA / move ticket to QA state
- [ ] Once approved, merge and close.

## Resources on metadata

If not already familiar with these conventions for generating STAC collection and item metadata:
       - Collections: https://github.com/NASA-IMPACT/delta-backend/issues/29 and STAC version 1.0 specification for collections
       - Items: https://github.com/NASA-IMPACT/delta-backend/issues/28 and STAC version 1.0 specification for items
       - NOTE: The delta-backend instructions are specific to datasets for the climate dashboard, however not all datasets are going to be a part of the visual layers for the dashboard so you can ignore the instructions that are specific to "dashboard" extension, "item_assets" in the collection and "cog_default" asset type in the item.
