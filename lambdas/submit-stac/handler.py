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
    sample_event = {
        "stac_item": {
            "type": "Feature",
            "stac_version": "1.0.0",
            "id": "afrisar_dlr_roi_SAV1",
            "properties": {
            "time_start": "2021-07-21T14:13:18.000Z",
            "updated": "2021-07-21T14:13:18.000Z",
            "dataset_id": "AFRISAR_DLR",
            "data_center": "ESA_MAAP",
            "title": "afrisar_dlr_roi_SAV1",
            "coordinate_system": "CARTESIAN",
            "day_night_flag": "BOTH",
            "time_end": "2021-07-21T14:13:18.000Z",
            "original_format": "ECHO10",
            "granule_size": "6.591796991415322E-4",
            "browse_flag": False,
            "polygons": [
                [
                "-0.2070277 11.5902481 -0.208279 11.5902481 -0.208279 11.5915194 -0.2070277 11.5915194 -0.2070277 11.5902481"
                ]
            ],
            "collection_concept_id": "C1200109552-ESA_MAAP",
            "online_access_flag": True,
            "links": [
                {
                "rel": "http://esipfed.org/ns/fedsearch/1.1/data#",
                "type": "application/octet-stream",
                "hreflang": "en-US",
                "href": "https://bmap-catalogue-data.oss.eu-west-0.prod-cloud-ocb.orange-business.com/Campaign_data/afrisar_dlr/afrisar_dlr_roi_SAV1.prj"
                },
                {
                "rel": "http://esipfed.org/ns/fedsearch/1.1/data#",
                "type": "application/octet-stream",
                "hreflang": "en-US",
                "href": "https://bmap-catalogue-data.oss.eu-west-0.prod-cloud-ocb.orange-business.com/Campaign_data/afrisar_dlr/afrisar_dlr_roi_SAV1.dbf"
                },
                {
                "rel": "http://esipfed.org/ns/fedsearch/1.1/data#",
                "type": "application/octet-stream",
                "hreflang": "en-US",
                "href": "https://bmap-catalogue-data.oss.eu-west-0.prod-cloud-ocb.orange-business.com/Campaign_data/afrisar_dlr/afrisar_dlr_roi_SAV1.shp"
                },
                {
                "rel": "http://esipfed.org/ns/fedsearch/1.1/data#",
                "type": "application/octet-stream",
                "hreflang": "en-US",
                "href": "https://bmap-catalogue-data.oss.eu-west-0.prod-cloud-ocb.orange-business.com/Campaign_data/afrisar_dlr/afrisar_dlr_roi_SAV1.shx"
                },
                {
                "rel": "http://esipfed.org/ns/fedsearch/1.1/metadata#",
                "title": "WMS GetMap Resource (VisualizationURL)",
                "hreflang": "en-US",
                "href": "https://edav-ui.val.esa-maap.org"
                },
                {
                "inherited": True,
                "rel": "http://esipfed.org/ns/fedsearch/1.1/documentation#",
                "hreflang": "en-US",
                "href": "https://earth.esa.int/documents/10174/134665/AfriSAR-Final-Report"
                }
            ],
            "concept_id": "G1201298435-ESA_MAAP",
            "datetime": "2021-07-21T14:13:18Z"
            },
            "geometry": {
            "coordinates": [
                [
                [
                    -0.2070277,
                    11.5902481
                ],
                [
                    -0.208279,
                    11.5902481
                ],
                [
                    -0.208279,
                    11.5915194
                ],
                [
                    -0.2070277,
                    11.5915194
                ],
                [
                    -0.2070277,
                    11.5902481
                ]
                ]
            ],
            "type": "Polygon"
            },
            "links": [
            {
                "rel": "self",
                "href": "https://bmap-catalogue-data.oss.eu-west-0.prod-cloud-ocb.orange-business.com/Campaign_data/afrisar_dlr/afrisar_dlr_roi_SAV1.shx",
                "type": "application/json"
            }
            ],
            "assets": {
            "prj": {
                "href": "https://bmap-catalogue-data.oss.eu-west-0.prod-cloud-ocb.orange-business.com/Campaign_data/afrisar_dlr/afrisar_dlr_roi_SAV1.prj",
                "type": "application/octet-stream",
                "roles": [
                "metadata"
                ]
            },
            "dbf": {
                "href": "https://bmap-catalogue-data.oss.eu-west-0.prod-cloud-ocb.orange-business.com/Campaign_data/afrisar_dlr/afrisar_dlr_roi_SAV1.dbf",
                "type": "application/octet-stream",
                "roles": [
                "data"
                ]
            },
            "shp": {
                "href": "https://bmap-catalogue-data.oss.eu-west-0.prod-cloud-ocb.orange-business.com/Campaign_data/afrisar_dlr/afrisar_dlr_roi_SAV1.shp",
                "type": "application/octet-stream",
                "roles": [
                "data"
                ]
            },
            "shx": {
                "href": "https://bmap-catalogue-data.oss.eu-west-0.prod-cloud-ocb.orange-business.com/Campaign_data/afrisar_dlr/afrisar_dlr_roi_SAV1.shx",
                "type": "application/octet-stream",
                "roles": [
                "data"
                ]
            }
            },
            "bbox": [
            -0.208279,
            11.5902481,
            -0.2070277,
            11.5915194
            ],
            "stac_extensions": [],
            "collection": "AFRISAR_DLR"
        }
        }
    handler(sample_event, {})
