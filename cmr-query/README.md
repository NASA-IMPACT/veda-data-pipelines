Docker to query CMR for granules associated with a given collection and temporal range.

```bash
docker build -t cmr-query .
docker run cmr-query python -m handler.handler -c "OMNO2d" -d "7" --include "^.+he5$"
```