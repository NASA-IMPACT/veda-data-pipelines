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
            "id": "GEDI02_B_2020366232302_O11636_02_T08595_02_003_01_V002",
            "properties": {
            "producer_granule_id": "GEDI02_B_2020366232302_O11636_02_T08595_02_003_01_V002.h5",
            "time_start": "2020-12-31T23:23:02.000Z",
            "updated": "2021-09-16T13:37:33.255Z",
            "dataset_id": "GEDI L2B Canopy Cover and Vertical Profile Metrics Data Global Footprint Level V002",
            "data_center": "NASA_MAAP",
            "title": "SC:GEDI02_B.002:2479608683",
            "coordinate_system": "GEODETIC",
            "day_night_flag": "UNSPECIFIED",
            "time_end": "2021-01-01T00:55:54.000Z",
            "original_format": "ECHO10",
            "granule_size": "663.926",
            "browse_flag": False,
            "polygons": [
                [
                "-0.2640931 -7.5942986 2.7932293 -5.4398834 5.8454799 -3.2726337 8.8866541 -1.0780887 11.9114801 1.1566424 14.9130173 3.4473936 17.8848238 5.8091107 20.8197692 8.2582584 23.7095027 10.8132661 26.544827 13.4937214 29.3157925 16.3194844 32.0107917 19.3138675 34.6167406 22.4998778 37.1188361 25.9025215 39.4994854 29.547296 41.7401324 33.4580782 43.8184058 37.6568137 45.7114327 42.1594278 47.3924312 46.9745689 48.8360387 52.0968745 50.0150151 57.5065964 50.9057461 63.1637517 51.4875696 69.0098772 51.7455864 74.9686714 51.7565444 75.9660086 51.8427388 75.987172 51.8319445 74.9875826 51.5742477 69.0162927 50.9925629 63.1585731 50.1015707 57.4905648 48.9214244 52.0711538 47.4763487 46.9406189 45.7935181 42.1186894 43.8986719 37.6106335 41.8182714 33.4077396 39.5757225 29.4937108 37.1932254 25.8465441 34.689305 22.442235 32.0816387 19.2550737 29.3850463 16.2598944 26.6126275 13.4337206 23.7760066 10.7530123 20.885204 8.197866 17.9493436 5.748683 14.9767598 3.3869977 11.9745821 1.0962992 8.9492949 -1.1383706 5.9077824 -3.3328705 2.855375 -5.5001079 -0.2019723 -7.6545299 -0.2640931 -7.5942986"
                ]
            ],
            "collection_concept_id": "C1201460047-NASA_MAAP",
            "online_access_flag": False,
            "links": [
                {
                "rel": "http://esipfed.org/ns/fedsearch/1.1/s3#",
                "title": "File to download",
                "hreflang": "en-US",
                "href": "s3://nasa-maap-data-store/file-staging/nasa-map/GEDI02_B___002/2020.12.31/GEDI02_B_2020366232302_O11636_02_T08595_02_003_01_V002.h5"
                },
                {
                "inherited": True,
                "rel": "http://esipfed.org/ns/fedsearch/1.1/metadata#",
                "hreflang": "en-US",
                "href": "https://doi.org/10.5067/GEDI/GEDI02_B.002"
                },
                {
                "inherited": True,
                "rel": "http://esipfed.org/ns/fedsearch/1.1/metadata#",
                "hreflang": "en-US",
                "href": "https://gedi.umd.edu/"
                },
                {
                "inherited": True,
                "rel": "http://esipfed.org/ns/fedsearch/1.1/metadata#",
                "hreflang": "en-US",
                "href": "https://lpdaac.usgs.gov/products/gedi02_bv002/"
                },
                {
                "inherited": True,
                "rel": "http://esipfed.org/ns/fedsearch/1.1/documentation#",
                "hreflang": "en-US",
                "href": "https://lpdaac.usgs.gov/documents/587/gedi_l2b_dictionary_P001_v1.html"
                },
                {
                "inherited": True,
                "rel": "http://esipfed.org/ns/fedsearch/1.1/documentation#",
                "hreflang": "en-US",
                "href": "https://doi.org/10.5067/DOC/GEDI/GEDI_WF_ATBD.001"
                },
                {
                "inherited": True,
                "rel": "http://esipfed.org/ns/fedsearch/1.1/documentation#",
                "hreflang": "en-US",
                "href": "https://doi.org/10.5067/DOC/GEDI/GEDI_FCCVPM_ATBD.001"
                }
            ],
            "concept_id": "G1201538384-NASA_MAAP",
            "datetime": "2020-12-31T23:23:02Z"
            },
            "geometry": {
            "coordinates": [
                [
                [
                    -0.2640931,
                    -7.5942986
                ],
                [
                    2.7932293,
                    -5.4398834
                ],
                [
                    5.8454799,
                    -3.2726337
                ],
                [
                    8.8866541,
                    -1.0780887
                ],
                [
                    11.9114801,
                    1.1566424
                ],
                [
                    14.9130173,
                    3.4473936
                ],
                [
                    17.8848238,
                    5.8091107
                ],
                [
                    20.8197692,
                    8.2582584
                ],
                [
                    23.7095027,
                    10.8132661
                ],
                [
                    26.544827,
                    13.4937214
                ],
                [
                    29.3157925,
                    16.3194844
                ],
                [
                    32.0107917,
                    19.3138675
                ],
                [
                    34.6167406,
                    22.4998778
                ],
                [
                    37.1188361,
                    25.9025215
                ],
                [
                    39.4994854,
                    29.547296
                ],
                [
                    41.7401324,
                    33.4580782
                ],
                [
                    43.8184058,
                    37.6568137
                ],
                [
                    45.7114327,
                    42.1594278
                ],
                [
                    47.3924312,
                    46.9745689
                ],
                [
                    48.8360387,
                    52.0968745
                ],
                [
                    50.0150151,
                    57.5065964
                ],
                [
                    50.9057461,
                    63.1637517
                ],
                [
                    51.4875696,
                    69.0098772
                ],
                [
                    51.7455864,
                    74.9686714
                ],
                [
                    51.7565444,
                    75.9660086
                ],
                [
                    51.8427388,
                    75.987172
                ],
                [
                    51.8319445,
                    74.9875826
                ],
                [
                    51.5742477,
                    69.0162927
                ],
                [
                    50.9925629,
                    63.1585731
                ],
                [
                    50.1015707,
                    57.4905648
                ],
                [
                    48.9214244,
                    52.0711538
                ],
                [
                    47.4763487,
                    46.9406189
                ],
                [
                    45.7935181,
                    42.1186894
                ],
                [
                    43.8986719,
                    37.6106335
                ],
                [
                    41.8182714,
                    33.4077396
                ],
                [
                    39.5757225,
                    29.4937108
                ],
                [
                    37.1932254,
                    25.8465441
                ],
                [
                    34.689305,
                    22.442235
                ],
                [
                    32.0816387,
                    19.2550737
                ],
                [
                    29.3850463,
                    16.2598944
                ],
                [
                    26.6126275,
                    13.4337206
                ],
                [
                    23.7760066,
                    10.7530123
                ],
                [
                    20.885204,
                    8.197866
                ],
                [
                    17.9493436,
                    5.748683
                ],
                [
                    14.9767598,
                    3.3869977
                ],
                [
                    11.9745821,
                    1.0962992
                ],
                [
                    8.9492949,
                    -1.1383706
                ],
                [
                    5.9077824,
                    -3.3328705
                ],
                [
                    2.855375,
                    -5.5001079
                ],
                [
                    -0.2019723,
                    -7.6545299
                ],
                [
                    -0.2640931,
                    -7.5942986
                ]
                ]
            ],
            "type": "Polygon"
            },
            "links": [
            {
                "rel": "self",
                "href": "s3://nasa-maap-data-store/file-staging/nasa-map/GEDI02_B___002/2020.12.31/GEDI02_B_2020366232302_O11636_02_T08595_02_003_01_V002.h5",
                "type": "application/json"
            }
            ],
            "assets": {
            "data": {
                "href": "s3://nasa-maap-data-store/file-staging/nasa-map/GEDI02_B___002/2020.12.31/GEDI02_B_2020366232302_O11636_02_T08595_02_003_01_V002.h5",
                "type": "application/x-hdf5",
                "roles": [
                "data"
                ]
            },
            "metadata": {
                "href": "https://doi.org/10.5067/GEDI/GEDI02_B.002",
                "roles": [
                "metadata"
                ]
            },
            "documentation": {
                "href": "https://lpdaac.usgs.gov/documents/587/gedi_l2b_dictionary_P001_v1.html",
                "roles": [
                "documentation"
                ]
            }
            },
            "bbox": [
            -0.2640931,
            -7.6545299,
            51.8427388,
            75.987172
            ],
            "stac_extensions": [],
            "collection": "GEDI02_B"
        }
        }

    handler(sample_event, {})
