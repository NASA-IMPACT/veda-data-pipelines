INSERT INTO pgstac.collections (content) VALUES('{
   "id": "Hurricane_Ida_Blue_Tarps",
   "type": "Collection",
   "links":[
   ],
   "title":"Hurricane Ida Blue Tarps",
   "extent":{
      "spatial":{
         "bbox":[
            [
               -90.300691019583,
               29.791754950316868,
               -89.86300184384689,
               30.099979027371006
            ]
         ]
      },
      "temporal":{
         "interval":[
            [
               "2021-09-26T00:00:00Z",
               "2021-11-25T00:00:00Z"
            ]
         ]
      }
   },
   "license":"MIT",
   "description":"Blue tarps were detected in the aftermath of Hurricane Ida using Planet Imagery. The detection algorithm involved segmenting out blue pixels from the buildings in the affected region.",
   "stac_version":"1.0.0",
   "dashboard:is_periodic": false,
   "dashboard:time_density": "day",
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
