INSERT INTO pgstac.collections (content) VALUES('{
   "id": "nightlights-hd-monthly",
   "type": "Collection",
   "links":[
   ],
   "title":"Black Marble High Definition Nightlights Monthly Dataset",
   "extent":{
      "spatial":{
         "bbox":[
            [
               -90.3037818244749,
               29.804659612978707,
               -89.87578181971654,
               30.07177072705947
            ]
         ]
      },
      "temporal":{
         "interval":[
            [
               "2017-07-21T00:00:00Z",
               "2021-09-30T23:59:59Z"
            ]
         ]
      }
   },
   "license":"public-domain",
   "description": "The High Definition Nightlights dataset is processed to eliminate light sources, including moonlight reflectance and other interferences. Darker colors indicate fewer night lights and less activity. Lighter colors indicate more night lights and more activity.",
   "stac_version": "1.0.0",
   "dashboard:is_periodic": false,
   "dashboard:time_density": "month"
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
