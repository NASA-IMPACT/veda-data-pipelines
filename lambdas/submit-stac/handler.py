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
            "id": "uavsar_AfriSAR_v1_SLC-twenty_14044_16008_003_160225_L090",
            "properties": {
            "boxes": [
                "-2.0677778 9.1694444 0.61 11.8641667"
            ],
            "time_start": "2016-02-25T00:00:00.000Z",
            "updated": "2019-03-07T21:22:05.563Z",
            "dataset_id": "AfriSAR UAVSAR Coregistered SLCs Generated Using NISAR Tools",
            "data_center": "NASA_MAAP",
            "title": "uavsar_AfriSAR_v1_SLC-twenty_14044_16008_003_160225_L090.vrt",
            "coordinate_system": "CARTESIAN",
            "time_end": "2016-03-08T00:00:00.000Z",
            "original_format": "ECHO10",
            "browse_flag": True,
            "collection_concept_id": "C1200000308-NASA_MAAP",
            "online_access_flag": False,
            "links": [
                {
                "rel": "http://esipfed.org/ns/fedsearch/1.1/s3#",
                "title": "File to download",
                "hreflang": "en-US",
                "href": "s3://nasa-maap-data-store/file-staging/circleci/AfriSAR_UAVSAR_Coreg_SLC___1/uavsar_AfriSAR_v1_SLC-twenty_14044_16008_003_160225_L090.vrt"
                },
                {
                "rel": "http://esipfed.org/ns/fedsearch/1.1/browse#",
                "title": "(BROWSE)",
                "hreflang": "en-US",
                "href": "s3://nasa-maap-data-store/file-staging/circleci/AfriSAR_UAVSAR_Coreg_SLC___1/uavsar_AfriSAR_v1_SLC-twenty_14044_16008_003_160225_L090.vrt.cog.tif"
                },
                {
                "rel": "http://esipfed.org/ns/fedsearch/1.1/metadata#",
                "title": "WMS GetMap Resource (VisualizationURL)",
                "hreflang": "en-US",
                "href": "https://api.maap.xyz/api/wms/GetMap?SERVICE=WMS&VERSION=1.1.0&REQUEST=GetMap&LAYERS=uavsar_AfriSAR_v1_SLC-twenty_14044_16008_003_160225_L090.vrt"
                },
                {
                "inherited": True,
                "rel": "http://esipfed.org/ns/fedsearch/1.1/data#",
                "hreflang": "en-US",
                "href": "s3://nasa-maap-data-store/file-staging/nasa-map/AfriSAR_UAVSAR_Coreg_SLC___1"
                },
                {
                "inherited": True,
                "rel": "http://esipfed.org/ns/fedsearch/1.1/documentation#",
                "hreflang": "en-US",
                "href": "https://ieeexplore.ieee.org/document/8469014"
                }
            ],
            "concept_id": "G1200040264-NASA_MAAP",
            "datetime": "2016-02-25T00:00:00Z"
            },
            "geometry": {
            "coordinates": [
                [
                [
                    -2.0677778,
                    9.1694444
                ],
                [
                    0.61,
                    9.1694444
                ],
                [
                    0.61,
                    11.8641667
                ],
                [
                    -2.0677778,
                    11.8641667
                ],
                [
                    -2.0677778,
                    9.1694444
                ]
                ]
            ],
            "type": "Polygon"
            },
            "links": [
            {
                "rel": "self",
                "href": "s3://nasa-maap-data-store/file-staging/circleci/AfriSAR_UAVSAR_Coreg_SLC___1/uavsar_AfriSAR_v1_SLC-twenty_14044_16008_003_160225_L090.vrt",
                "type": "application/json"
            }
            ],
            "assets": {
            "data": {
                "href": "s3://nasa-maap-data-store/file-staging/circleci/AfriSAR_UAVSAR_Coreg_SLC___1/uavsar_AfriSAR_v1_SLC-twenty_14044_16008_003_160225_L090.vrt",
                "roles": [
                "data"
                ]
            },
            "metadata": {
                "href": "https://api.maap.xyz/api/wms/GetMap?SERVICE=WMS&VERSION=1.1.0&REQUEST=GetMap&LAYERS=uavsar_AfriSAR_v1_SLC-twenty_14044_16008_003_160225_L090.vrt",
                "roles": [
                "metadata"
                ]
            },
            "documentation": {
                "href": "https://ieeexplore.ieee.org/document/8469014",
                "roles": [
                "documentation"
                ]
            }
            },
            "bbox": [
            -2.0677778,
            9.1694444,
            0.61,
            11.8641667
            ],
            "stac_extensions": [],
            "collection": "AfriSAR_UAVSAR_Coreg_SLC",
            "test_links": True
        }
    }

    handler(sample_event, {})
