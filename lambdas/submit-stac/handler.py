from dataclasses import dataclass
import json
import os
from urllib.parse import urlparse
from typing import Any, Dict, Optional, TypedDict, Union

import boto3
import requests


COGNITO_APP_SECRET = os.environ["COGNITO_APP_SECRET"]
STAC_INGESTOR_API_URL = os.environ["STAC_INGESTOR_API_URL"]


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
    base_url=STAC_INGESTOR_API_URL,
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
    filename = "example.ndjson"
    sample_event = {
        "stac_item": {
            "type": "Feature",
            "stac_version": "1.0.0",
            "id": "boreal_agb_202205071651900000_26827_cog",
            "properties": {
            "proj:epsg": 3857,
            "proj:geometry": {
                "type": "Polygon",
                "coordinates": [
                [
                    [
                    3414594.9275553934,
                    5762740.436476009
                    ],
                    [
                    3600489.7803449407,
                    5762740.436476009
                    ],
                    [
                    3600489.7803449407,
                    5958419.228886059
                    ],
                    [
                    3414594.9275553934,
                    5958419.228886059
                    ],
                    [
                    3414594.9275553934,
                    5762740.436476009
                    ]
                ]
                ]
            },
            "proj:bbox": [
                3414594.9275553934,
                5762740.436476009,
                3600489.7803449407,
                5958419.228886059
            ],
            "proj:shape": [
                5120,
                4864
            ],
            "proj:transform": [
                38.21851414258785,
                0.0,
                3414594.9275553934,
                0.0,
                -38.21851414258781,
                5958419.228886059,
                0.0,
                0.0,
                1.0
            ],
            "datetime": "2022-05-07T00:00:00Z"
            },
            "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                [
                    30.673828125,
                    45.89000815866183
                ],
                [
                    32.343749999999986,
                    45.89000815866183
                ],
                [
                    32.343749999999986,
                    47.10004469402519
                ],
                [
                    30.673828125,
                    47.10004469402519
                ],
                [
                    30.673828125,
                    45.89000815866183
                ]
                ]
            ]
            },
            "links": [
            {
                "rel": "collection",
                "href": "aimeeb-shared",
                "type": "application/json"
            }
            ],
            "assets": {
            "cog_default": {
                "href": "s3://maap-user-shared-data/aimeeb-shared/boreal_agb_202205071651900000_26827_cog.tif",
                "type": "image/tiff; application=geotiff; profile=cloud-optimized",
                "raster:bands": [
                {
                    "data_type": "float32",
                    "scale": 1.0,
                    "offset": 0.0,
                    "sampling": "area",
                    "nodata": "nan",
                    "statistics": {
                    "mean": 13.947627564862637,
                    "minimum": -5.202122211456299,
                    "maximum": 94.9677734375,
                    "stddev": 6.586425725599481,
                    "valid_percent": 14.982355633350464
                    },
                    "histogram": {
                    "count": 11,
                    "min": -5.202122211456299,
                    "max": 94.9677734375,
                    "buckets": [
                        64,
                        105970,
                        34194,
                        6370,
                        1815,
                        563,
                        193,
                        74,
                        23,
                        11
                    ]
                    }
                },
                {
                    "data_type": "float32",
                    "scale": 1.0,
                    "offset": 0.0,
                    "sampling": "area",
                    "nodata": "nan",
                    "statistics": {
                    "mean": 2.483518266377272,
                    "minimum": -1.3178435564041138,
                    "maximum": 15.769033432006836,
                    "stddev": 1.2959685027687635,
                    "valid_percent": 14.982355633350464
                    },
                    "histogram": {
                    "count": 11,
                    "min": -1.3178435564041138,
                    "max": 15.769033432006836,
                    "buckets": [
                        15,
                        72678,
                        58335,
                        12392,
                        4473,
                        951,
                        299,
                        116,
                        15,
                        3
                    ]
                    }
                }
                ],
                "roles": [
                "data",
                "layer"
                ]
            }
            },
            "bbox": [
            30.673828125,
            45.89000815866183,
            32.343749999999986,
            47.10004469402519
            ],
            "stac_extensions": [
            "https://stac-extensions.github.io/projection/v1.0.0/schema.json",
            "https://stac-extensions.github.io/raster/v1.1.0/schema.json"
            ],
            "collection": "aimeeb-shared"
        }
        }


    handler(sample_event, {})
