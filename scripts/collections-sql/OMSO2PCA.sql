INSERT INTO pgstac.collections (content) VALUES('{
    "id": "OMSO2PCA",
    "type": "Collection",
    "links": [],
    "title": "OMSO2PCA", 
    "extent": {
        "spatial": {
            "bbox": [
                [
                    -180,
                    -90,
                    180,
                    90
                ]
            ]
        },
        "temporal": {
            "interval": [
                [
                    "2005-01-01T00:00:00Z",
                    "2021-01-01T00:00:00Z"
                ]
            ]
        }
    },
    "license": "public-domain",
    "description": "OMI/Aura Sulfur Dioxide (SO2) Total Column L3 1 day Best Pixel in 0.25 degree x 0.25 degree V3",
    "stac_version": "1.0.0",
    "summaries": {
        "datetime": [
            "2005-01-01T00:00:00Z",
            "2021-01-01T00:00:00Z"
        ],
        "cog_default": {
            "avg": 287.90577560637,
            "max": 478.89999389648,
            "min": 51
        }
    },
    "properties": {
        "dashboard:is_periodic": true,
        "dashboard:time_density": "year"
    }    
}')
ON CONFLICT (id) DO UPDATE 
  SET content = excluded.content;
