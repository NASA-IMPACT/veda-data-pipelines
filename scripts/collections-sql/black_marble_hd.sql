INSERT INTO pgstac.collections (content) VALUES('{
    "id": "BMHD",
   "type": "Collection",
   "links":[
   ],
   "title":"BMHD",
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
               "2021-08-31T00:00:00Z"
            ]
         ]
      }
   },
   "license":"public-domain",
   "description":"BMHDIda",
   "stac_version":"1.0.0"
}')
ON CONFLICT (id) DO UPDATE 
  SET content = excluded.content;
