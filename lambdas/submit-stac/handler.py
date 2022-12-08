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
        "id": "boreal_agb_202212051670264409_2112",
        "properties": {
          "proj:epsg": None,
          "proj:geometry": {
            "type": "Polygon",
            "coordinates": [
              [
                [
                  -2961478.0,
                  4473304.0
                ],
                [
                  -2871478.0,
                  4473304.0
                ],
                [
                  -2871478.0,
                  4563304.0
                ],
                [
                  -2961478.0,
                  4563304.0
                ],
                [
                  -2961478.0,
                  4473304.0
                ]
              ]
            ]
          },
          "proj:bbox": [
            -2961478.0,
            4473304.0,
            -2871478.0,
            4563304.0
          ],
          "proj:shape": [
            3000,
            3000
          ],
          "proj:transform": [
            30.0,
            0.0,
            -2961478.0,
            0.0,
            -30.0,
            4563304.0,
            0.0,
            0.0,
            1.0
          ],
          "datetime": "2022-12-05T00:00:00Z"
        },
        "geometry": {
          "type": "Polygon",
          "coordinates": [
            [
              [
                104.86110644433832,
                63.53882062284371
              ],
              [
                105.68371316442243,
                64.25250527759168
              ],
              [
                103.97974230345058,
                64.60012611711596
              ],
              [
                103.18984743000539,
                63.8776409949251
              ],
              [
                104.86110644433832,
                63.53882062284371
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
            "href": "s3://maap-user-shared-data/icesat2-boreal/boreal_agb_202212051670264409_2112.tif",
            "type": "image/tiff; application=geotiff; profile=cloud-optimized",
            "raster:bands": [
              {
                "data_type": "float32",
                "scale": 1.0,
                "offset": 0.0,
                "sampling": "area",
                "nodata": "nan",
                "statistics": {
                  "mean": 31.942728162205626,
                  "minimum": 3.376779079437256,
                  "maximum": 150.87786865234375,
                  "stddev": 10.524873722675382,
                  "valid_percent": 98.44493865966797
                },
                "histogram": {
                  "count": 11,
                  "min": 3.376779079437256,
                  "max": 150.87786865234375,
                  "buckets": [
                    73947,
                    524791,
                    353092,
                    70303,
                    8732,
                    1121,
                    214,
                    48,
                    17,
                    5
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
          103.18984743000539,
          63.53882062284371,
          105.68371316442243,
          64.60012611711596
        ],
        "stac_extensions": [
          "https://stac-extensions.github.io/projection/v1.0.0/schema.json",
          "https://stac-extensions.github.io/raster/v1.1.0/schema.json"
        ],
        "collection": "icesat2-boreal"
      }
    }

    handler(sample_event, {})
