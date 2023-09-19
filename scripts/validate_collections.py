import sys
from pathlib import Path

from pystac import Collection
from pystac.errors import STACValidationError

root = Path(__file__).parents[1]
collections = root / "data" / "collections"

errors = False
for path in collections.glob("*.json"):
    try:
        collection = Collection.from_file(str(path))
    except Exception as err:
        errors = True
        print(
            f"ERROR [{path.name}]: could not read collection because {type(err)}: {err}"
        )
    try:
        collection.validate()
    except STACValidationError as err:
        errors = True
        print(
            f"VALIDATION [{path.name}]: {collection.id} is invalid because {err.source}"
        )

if errors:
    sys.exit(1)
