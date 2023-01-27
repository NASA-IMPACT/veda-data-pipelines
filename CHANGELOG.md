# Changelog

## 2022-12-01: `ab/mergeable-maap-changes`

### Changes
* change `EXTERNAL_ROLE_ARN` to `DATA_MANAGEMENT_ROLE_ARN` - this was necessary since the data management role we're using in MAAP actually exists in the same AWS account ad VDP
* change `s3_filename` to `remote_fileurl` - this was necessary since some items in MAAP (specifically ESA datasets) have HTTP URLs
* in `lambdas/cmr-query/handler.py` call the API directly instead of using python-cmr. This was necessary because there is no way to iterate through smaller batches of CMR results using python-cmr. pythong-cmr's `get_all()` will return everything and [`get()`](https://github.com/nasa/python_cmr/blob/develop/cmr/queries.py#L42) accepts a limit but no way of picking a specific page of results.

### Additions

* in `lambdas/build-stac/utils/stac.py`:
  * in `create_stac_item` use a try/catch so that non-rasterio-readable datasets can still be published using pystac.Item()
  * in `generate_stac_cmrevent` - generate geometry from CMR JSON and generate assets from CMR Links
* Add the ability to paginate through CMR results through adding a `start_after` key in `lambdas/cmr-query/handler.py`. This key is used in a conditional for the `maybe_next_discovery` task in the discovery step function. When the `start_after` key is present, the step function will call a discovery lambda to re-trigger the discovery step function.