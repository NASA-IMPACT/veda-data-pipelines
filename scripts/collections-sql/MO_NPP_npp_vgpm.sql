INSERT INTO pgstac.collections (content) VALUES('{
    "id": "MO_NPP_npp_vgpm",
    "type": "Collection",
    "links": [],
    "title": "", 
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
                    "2020-01-01T00:00:00Z",
                    "2020-12-12T23:59:59Z"
                ]
            ]
        }
    },
    "license": "MIT",
    "description": "Ocean NPP",
    "stac_version": "1.0.0",
    "dashboard:is_periodic": true,
    "dashboard:time_density": "month",
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
}')
ON CONFLICT (id) DO UPDATE 
  SET content = excluded.content;
