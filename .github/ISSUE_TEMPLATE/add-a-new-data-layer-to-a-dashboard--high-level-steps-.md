---
name: Add a new data layer to a dashboard (high-level steps)
about: All steps for adding a new layer or indicator the dashboard
title: Add a new data layer to a dashboard (high-level steps)
labels: ''
assignees: ''

---

For each dataset, we will follow the following steps:
1. Identify dataset and where it will be accessed from. Check it's a good source with science team. Ask about specific variables and required spatial and temporal extent. Note most datasets will require back processing (e.g. generating cloud-optimized data for historical data).
2. If the dataset is ongoing (i.e. new files are continuously added and should be included in the dashboard), design and construct the forward-processing workflow. 
    - Each collection will have a workflow which includes discovering data files from the source, generating the cloud-optimized versions of the data and writing STAC metadata.
   - Each collection will have different requirements for both the generation and scheduling of these steps, so a design step much be included for each new collection / data layer.
3. Verify the COG output with the science team by sharing in a visual interface.
4. Verify the metadata output with STAC API developers and any systems which may be depending on this STAC metadata (e.g. the front-end dev team).
5. If the dataset should be backfilled, create and monitor the backward-processing workflow.
6. Engage the science team to add any required background information on the methodology used to derive the dataset.
7. Add the dataset to the production dashboard.
