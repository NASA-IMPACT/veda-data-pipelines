# NetCDF4 / HDF5 to COG

Configurable module for converting GeoTiff to COG.

## Testing

`handler.py` by default is using an example with OMI OAO3 dataset.

```bash
docker build -t cogify-tiff .
# Runs an example in handler.py
docker run cogify-tiff python -m handler
```


Example Input:
```
{
    "s3_filename": "s3://gesdisc/example.tif",
    "collection": "gesdisc"
}

```

Example Output
```
{
  "s3_filename": "s3://",
    "collection": "gesdisc"
}

```

