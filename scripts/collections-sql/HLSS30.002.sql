INSERT INTO pgstac.collections (content) VALUES('{
   "id": "HLSS30.002",
   "type": "Collection",
   "links":[
   ],
   "title":"HLSS30.002",
    
   "dashboard:is_periodic": True,
   "dashboard:time_density": 
   "extent":{
      "spatial":{
         "bbox":[
            [
               -180,
               -90,
               180,
               90
            ]
         ]
      },
      "temporal":{
         "interval":[
            [
               "2015-12-01T00:00:00Z",
               null
            ]
         ]
      }
   },
   "license":"public-domain",
   "description":"Read more on the NASA CMR Landing page: https://cmr.earthdata.nasa.gov/search/concepts/C2021957295-LPCLOUD.html",
   "provider": {
       "name": "Land Processes Distributed Active Archive Center (LP DAAC)",
       "roles": ["processor"],
       "url": "https://lpdaac.usgs.gov/products/hlss30v002/"

   },
   "links": [{
       "rel": "external",
       "title": "NASA Common Metadata Repository Record for this Dataset",
       "href": "https://cmr.earthdata.nasa.gov/search/concepts/C2021957295-LPCLOUD.html",
       "type": "text/html"
   }],
   "stac_version":"1.0.0",
   "properties": {
     "dashboard:is_periodic": true
     "dashboard:time_density": "hour",
     "summaries": {
       "datetime": ["2021-07-29 01:00:00","2021-07-29 05:00:00Z"]
     }
   }
}')
ON CONFLICT (id) DO UPDATE 
  SET content = excluded.content;
