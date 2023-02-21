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
        "id": "boreal_agb_202302151676439579_1326",
        "properties": {
          "proj:epsg": None,
          "proj:geometry": {
            "type": "Polygon",
            "coordinates": [
              [
                [
                  4598521.999999994,
                  5643304.000000009
                ],
                [
                  4688521.999999994,
                  5643304.000000009
                ],
                [
                  4688521.999999994,
                  5733304.000000009
                ],
                [
                  4598521.999999994,
                  5733304.000000009
                ],
                [
                  4598521.999999994,
                  5643304.000000009
                ]
              ]
            ]
          },
          "proj:bbox": [
            4598521.999999994,
            5643304.000000009,
            4688521.999999994,
            5733304.000000009
          ],
          "proj:shape": [
            3000,
            3000
          ],
          "proj:transform": [
            30.0,
            0.0,
            4598521.999999994,
            0.0,
            -30.0,
            5733304.000000009,
            0.0,
            0.0,
            1.0
          ],
          "datetime": "2023-02-15T00:00:00Z"
        },
        "geometry": {
          "type": "Polygon",
          "coordinates": [
            [
              [
                -78.40290984426046,
                51.88215648468819
              ],
              [
                -78.32778988059182,
                51.07724585591961
              ],
              [
                -77.04127077089376,
                51.11571796796324
              ],
              [
                -77.09133101247565,
                51.92130718597872
              ],
              [
                -78.40290984426046,
                51.88215648468819
              ]
            ]
          ]
        },
        "links": [
          {
            "rel": "collection",
            "href": "icesat2-boreal",
            "type": "application/json"
          }
        ],
        "assets": {
          "cog_default": {
            "href": "s3://maap-ops-workspace/lduncanson/dps_output/run_boreal_biomass_quick_v2_ubuntu/map_boreal_2022_rh_noground_v4/2023/02/15/05/42/01/342476/boreal_agb_202302151676439579_1326.tif",
            "type": "image/tiff; application=geotiff; profile=cloud-optimized",
            "raster:bands": [
              {
                "data_type": "float32",
                "scale": 1.0,
                "offset": 0.0,
                "sampling": "area",
                "nodata": "nan",
                "statistics": {
                  "mean": 20.13457220378195,
                  "minimum": 3.2080953121185303,
                  "maximum": 184.36343383789062,
                  "stddev": 16.76768258991038,
                  "valid_percent": 96.62446975708008
                },
                "histogram": {
                  "count": 11,
                  "min": 3.2080953121185303,
                  "max": 184.36343383789062,
                  "buckets": [
                    681765,
                    228373,
                    63820,
                    21697,
                    9756,
                    4666,
                    2226,
                    760,
                    103,
                    15
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
                  "mean": 3.1726184659996584,
                  "minimum": 0.509101927280426,
                  "maximum": 77.29371643066406,
                  "stddev": 2.480238548909341,
                  "valid_percent": 96.62446975708008
                },
                "histogram": {
                  "count": 11,
                  "min": 0.509101927280426,
                  "max": 77.29371643066406,
                  "buckets": [
                    960512,
                    49080,
                    3485,
                    79,
                    12,
                    5,
                    5,
                    0,
                    0,
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
          -78.40290984426046,
          51.07724585591961,
          -77.04127077089376,
          51.92130718597872
        ],
        "stac_extensions": [
          "https://stac-extensions.github.io/projection/v1.0.0/schema.json",
          "https://stac-extensions.github.io/raster/v1.1.0/schema.json"
        ],
        "collection": "icesat2-boreal"
      }
    }
    handler(sample_event, {})
