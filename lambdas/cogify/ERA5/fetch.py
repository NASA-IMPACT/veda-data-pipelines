import cdsapi

c = cdsapi.Client()

c.retrieve(
    "reanalysis-era5-single-levels",
    {
        "product_type": "reanalysis",
        "format": "netcdf",
        "variable": "cloud_base_height",
        "year": "2021",
        "month": "08",
        "day": ["01"],
        "time": ["00:00"],
    },
    "download.nc",
)
