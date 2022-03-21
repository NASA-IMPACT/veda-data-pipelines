INSERT INTO pgstac.collections (content) VALUES('{
   "id": "facebook_population_density",
   "type": "Collection",
   "links":[
       {
            "href": "https://arxiv.org/pdf/1712.05839.pdf",
            "rel": "external",
            "type": "application/pdf",
            "title": "Mapping the world population one building at a time"
       }
   ],
   "title":"Population Density (Facebook)",
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
               "2015-01-01T00:00:00Z",
               null
            ]
         ]
      }
   },
   "license":"public-domain",
   "description":"Facebook high-resolution population density: Darker areas indicate higher population density areas and lighter areas indicate lower population density areas, with a 30m² resolution.",
   "stac_version":"1.0.0"
}')
ON CONFLICT (id) DO UPDATE
  SET content = excluded.content;
