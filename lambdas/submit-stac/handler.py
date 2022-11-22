from dataclasses import dataclass
import json
import os
from urllib.parse import urlparse
from typing import Any, Dict, Optional, TypedDict, Union

import boto3
import requests


COGNITO_APP_SECRET = os.environ["COGNITO_APP_SECRET"]
STAC_INGESTOR_URL = os.environ["STAC_INGESTOR_URL"]


class InputBase(TypedDict):
    dry_run: Optional[Any]


class S3LinkInput(InputBase):
    stac_file_url: str


class StacItemInput(InputBase):
    stac_item: Dict[str, Any]


class AppConfig(TypedDict):
    cognito_domain: str
    client_id: str
    client_secret: str
    scope: str


class Creds(TypedDict):
    access_token: str
    expires_in: int
    token_type: str


@dataclass
class IngestionApi:
    base_url: str
    token: str

    @classmethod
    def from_veda_auth_secret(cls, *, secret_id: str, base_url: str) -> "IngestionApi":
        cognito_details = cls._get_cognito_service_details(secret_id)
        print(cognito_details)
        credentials = cls._get_app_credentials(**cognito_details)
        return cls(token=credentials["access_token"], base_url=base_url)

    @staticmethod
    def _get_cognito_service_details(secret_id: str) -> AppConfig:
        client = boto3.client("secretsmanager")
        response = client.get_secret_value(SecretId=secret_id)
        return json.loads(response["SecretString"])

    @staticmethod
    def _get_app_credentials(
        cognito_domain: str, client_id: str, client_secret: str, scope: str, **kwargs
    ) -> Creds:
        response = requests.post(
            f"{cognito_domain}/oauth2/token",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
            auth=(client_id, client_secret),
            data={
                "grant_type": "client_credentials",
                # A space-separated list of scopes to request for the generated access token.
                "scope": scope,
            },
        )
        try:
            response.raise_for_status()
        except:
            print(response.text)
            raise
        return response.json()

    def submit(self, stac_item: Dict[str, Any]):
        response = requests.post(
            f"{self.base_url.rstrip('/')}/ingestions",
            json=stac_item,
            headers={"Authorization": f"bearer {self.token}"},
        )

        try:
            response.raise_for_status()
        except Exception as e:
            print(response.text)
            raise e

        return response.json()


def get_stac_item(event: Dict[str, Any]) -> Dict[str, Any]:
    if stac_item := event.get("stac_item"):
        return stac_item

    if file_url := event.get("stac_file_url"):
        url = urlparse(file_url)

        response = boto3.client("s3").get_object(
            Bucket=url.hostname,
            Key=url.path.lstrip("/"),
        )
        return json.load(response["Body"])

    raise Exception("No stac_item or stac_file_url provided")


ingestor = IngestionApi.from_veda_auth_secret(
    secret_id=COGNITO_APP_SECRET,
    base_url=STAC_INGESTOR_URL,
)


def handler(event: Union[S3LinkInput, StacItemInput], context) -> None:
    stac_item = get_stac_item(event)

    if event.get("dry_run"):
        print("Dry run, not inserting, would have inserted:")
        print(json.dumps(stac_item, indent=2))
        return

    ingestor.submit(stac_item)
    print(f"Successfully submitted STAC item")


if __name__ == "__main__":
    # filename = "example.ndjson"
    # sample_event = {
    #     "stac_file_url": "example.ndjson",
    #     # or
    #     "stac_item": {},
    #     "type": "collections",
    # }
    sample_event = {
        "stac_item": {
            "type": "Feature",
            "stac_version": "1.0.0",
            "id": "LVIS1B_ABoVE2017_0629_R1803_056233",
            "properties": {
            "producer_granule_id": "LVIS1B_ABoVE2017_0629_R1803_056233.h5",
            "time_start": "2017-06-29T15:37:13.488Z",
            "updated": "2018-04-17T10:10:51.082Z",
            "dataset_id": "ABoVE LVIS L1B Geolocated Return Energy Waveforms V001",
            "data_center": "NASA_MAAP",
            "title": "SC:ABLVIS1B.001:129486296",
            "coordinate_system": "GEODETIC",
            "day_night_flag": "UNSPECIFIED",
            "time_end": "2017-06-29T15:43:13.285Z",
            "id": "G1200116875-NASA_MAAP",
            "original_format": "ECHO10",
            "granule_size": "949.188",
            "browse_flag": "false",
            "polygons": [
                [
                "52.73648 -107.21639 52.73287 -107.21639 52.72565 -107.21639 52.68955 -107.14518 52.6354 -107.03845 52.58847 -106.91991 52.54515 -106.83707 52.52349 -106.77785 52.54515 -106.77169 52.57764 -106.83084 52.61735 -106.93757 52.67511 -107.04424 52.71843 -107.1451 52.74009 -107.21639 52.73648 -107.21639"
                ]
            ],
            "collection_concept_id": "C1200110748-NASA_MAAP",
            "online_access_flag": "false",
            "links": [
                {
                "rel": "http://esipfed.org/ns/fedsearch/1.1/s3#",
                "title": "File to download",
                "hreflang": "en-US",
                "href": "s3://nasa-maap-data-store/file-staging/nasa-map/ABLVIS1B___001/LVIS1B_ABoVE2017_0629_R1803_056233.h5"
                },
                {
                "rel": "http://esipfed.org/ns/fedsearch/1.1/metadata#",
                "type": "text/xml",
                "title": "(METADATA)",
                "hreflang": "en-US",
                "href": "https://n5eil01u.ecs.nsidc.org/DP4/ICEBRIDGE/ABLVIS1B.001/2017.06.29/LVIS1B_ABoVE2017_0629_R1803_056233.h5.xml"
                },
                {
                "inherited": "true",
                "rel": "http://esipfed.org/ns/fedsearch/1.1/data#",
                "hreflang": "en-US",
                "href": "s3://nasa-maap-data-store/file-staging/nasa-map/ABLVIS1B___001"
                },
                {
                "inherited": "true",
                "rel": "http://esipfed.org/ns/fedsearch/1.1/documentation#",
                "hreflang": "en-US",
                "href": "https://doi.org/10.5067/UMRAWS57QAFU"
                },
                {
                "inherited": "true",
                "rel": "http://esipfed.org/ns/fedsearch/1.1/metadata#",
                "hreflang": "en-US",
                "href": "http://lvis.gsfc.nasa.gov/"
                }
            ],
            "proj:epsg": None,
            "proj:geometry": {
                "type": "Polygon",
                "coordinates": [
                [
                    [
                    0.0,
                    512.0
                    ],
                    [
                    512.0,
                    512.0
                    ],
                    [
                    512.0,
                    0.0
                    ],
                    [
                    0.0,
                    0.0
                    ],
                    [
                    0.0,
                    512.0
                    ]
                ]
                ]
            },
            "proj:bbox": [
                0.0,
                512.0,
                512.0,
                0.0
            ],
            "proj:shape": [
                512,
                512
            ],
            "proj:transform": [
                1.0,
                0.0,
                0.0,
                0.0,
                1.0,
                0.0,
                0.0,
                0.0,
                1.0
            ],
            "datetime": "2017-06-29T15:37:13.488000Z"
            },
            "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                [
                    -180.0,
                    -90.0
                ],
                [
                    180.0,
                    -90.0
                ],
                [
                    180.0,
                    90.0
                ],
                [
                    -180.0,
                    90.0
                ],
                [
                    -180.0,
                    -90.0
                ]
                ]
            ]
            },
            "links": [
            {
                "rel": "collection",
                "href": "ABLVIS1B",
                "type": "application/json"
            }
            ],
            "assets": {
            "cog_default": {
                "href": "s3://nasa-maap-data-store/file-staging/nasa-map/ABLVIS1B___001/LVIS1B_ABoVE2017_0629_R1803_056233.h5",
                "type": "image/tiff; application=geotiff; profile=cloud-optimized",
                "raster:bands": [],
                "roles": [
                "data",
                "layer"
                ]
            }
            },
            "bbox": [
            -180.0,
            -90.0,
            180.0,
            90.0
            ],
            "stac_extensions": [
            "https://stac-extensions.github.io/projection/v1.0.0/schema.json",
            "https://stac-extensions.github.io/raster/v1.1.0/schema.json"
            ],
            "collection": "ABLVIS1B"
        }
    }
    handler(sample_event, {})
