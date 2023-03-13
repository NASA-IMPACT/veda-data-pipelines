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
            "id": "GEDI02_A_2020366232302_O11636_02_T08595_02_003_02_V002",
            "properties": {
                "producer_granule_id": "GEDI02_A_2020366232302_O11636_02_T08595_02_003_02_V002.h5",
                "time_start": "2020-12-31T23:23:02.000Z",
                "updated": "2021-09-16T13:39:42.918Z",
                "dataset_id": "GEDI L2A Elevation and Height Metrics Data Global Footprint Level V002",
                "data_center": "NASA_MAAP",
                "title": "SC:GEDI02_A.002:2479422824",
                "coordinate_system": "GEODETIC",
                "day_night_flag": "UNSPECIFIED",
                "time_end": "2021-01-01T00:55:54.000Z",
                "original_format": "ECHO10",
                "granule_size": "2769.65",
                "browse_flag": False,
                "polygons": [
                    [
                        "-0.2387289 -7.5971209 2.8189966 -5.4423856 5.8716528 -3.2747626 8.9132468 -1.0797761 11.9384815 1.1554717 14.9404437 3.4468156 17.9126576 5.8092283 20.8479939 8.259201 23.7380778 10.8151833 26.5736864 13.4966606 29.3450799 16.3238182 32.0403274 19.319827 34.6464371 22.5076979 37.1492987 25.9115612 39.5291864 29.5597367 41.7696059 33.4734198 43.8475875 37.6754714 45.7399801 42.1817944 47.4203727 47.001753 48.8627759 52.1285012 50.0402224 57.5428327 50.9290227 63.2044527 51.5085858 69.0547511 51.7642443 75.0176386 51.7746316 75.9956659 51.8249909 75.994814 51.8145864 75.015351 51.5586036 69.0453025 50.9783437 63.1882822 50.0885272 57.5206382 48.9098095 52.1011197 47.4659638 46.9701174 45.7840169 42.1467687 43.8900371 37.6378822 41.8104732 33.4339463 39.5685347 29.5189717 37.1871726 25.8699043 34.6829653 22.4655454 32.0756085 19.2774222 29.379222 16.2813389 26.6068138 13.4542411 23.7703001 10.7728961 20.879429 8.2170933 17.9434253 5.7673228 14.9706524 3.4051068 11.9682326 1.1139361 8.9426599 -1.1211578 5.9008172 -3.3160383 2.8480234 -5.4835915 -0.209737 -7.6383013 -0.2387289 -7.5971209"
                    ]
                ],
                "collection_concept_id": "C1201746156-NASA_MAAP",
                "online_access_flag": False,
                "links": [
                    {
                        "rel": "http://esipfed.org/ns/fedsearch/1.1/s3#",
                        "title": "File to download",
                        "hreflang": "en-US",
                        "href": "s3://nasa-maap-data-store/file-staging/nasa-map/GEDI02_A___002/2020.12.31/GEDI02_A_2020366232302_O11636_02_T08595_02_003_02_V002.h5",
                    },
                    {
                        "inherited": True,
                        "rel": "http://esipfed.org/ns/fedsearch/1.1/data#",
                        "hreflang": "en-US",
                        "href": "https://search.earthdata.nasa.gov/search?q=C1908348134-LPDAAC_ECS",
                    },
                    {
                        "inherited": True,
                        "rel": "http://esipfed.org/ns/fedsearch/1.1/data#",
                        "hreflang": "en-US",
                        "href": "https://e4ftl01.cr.usgs.gov/GEDI/GEDI02_A.002/",
                    },
                    {
                        "inherited": True,
                        "rel": "http://esipfed.org/ns/fedsearch/1.1/metadata#",
                        "hreflang": "en-US",
                        "href": "https://lpdaac.usgs.gov/",
                    },
                    {
                        "inherited": True,
                        "rel": "http://esipfed.org/ns/fedsearch/1.1/metadata#",
                        "hreflang": "en-US",
                        "href": "https://doi.org/10.5067/GEDI/GEDI02_A.002",
                    },
                    {
                        "inherited": True,
                        "rel": "http://esipfed.org/ns/fedsearch/1.1/documentation#",
                        "hreflang": "en-US",
                        "href": "https://lpdaac.usgs.gov/documents/982/gedi_l2a_dictionary_P003_v2.html",
                    },
                    {
                        "inherited": True,
                        "rel": "http://esipfed.org/ns/fedsearch/1.1/documentation#",
                        "hreflang": "en-US",
                        "href": "https://doi.org/10.5067/DOC/GEDI/GEDI_WF_ATBD.001",
                    },
                    {
                        "inherited": True,
                        "rel": "http://esipfed.org/ns/fedsearch/1.1/documentation#",
                        "hreflang": "en-US",
                        "href": "https://doi.org/10.5067/DOC/GEDI/GEDI_WFGEO_ATBD.001",
                    },
                    {
                        "inherited": True,
                        "rel": "http://esipfed.org/ns/fedsearch/1.1/metadata#",
                        "hreflang": "en-US",
                        "href": "https://gedi.umd.edu/",
                    },
                    {
                        "inherited": True,
                        "rel": "http://esipfed.org/ns/fedsearch/1.1/metadata#",
                        "hreflang": "en-US",
                        "href": "https://gedi.umd.edu/",
                    },
                    {
                        "inherited": True,
                        "rel": "http://esipfed.org/ns/fedsearch/1.1/documentation#",
                        "hreflang": "en-US",
                        "href": "https://lpdaac.usgs.gov/documents/998/GEDI02_UserGuide_V21.pdf",
                    },
                    {
                        "inherited": True,
                        "rel": "http://esipfed.org/ns/fedsearch/1.1/documentation#",
                        "hreflang": "en-US",
                        "href": "https://git.earthdata.nasa.gov/projects/LPDUR/repos/gedi-subsetter/browse",
                    },
                    {
                        "inherited": True,
                        "rel": "http://esipfed.org/ns/fedsearch/1.1/documentation#",
                        "hreflang": "en-US",
                        "href": "https://lpdaac.usgs.gov/resources/e-learning/accessing-and-analyzing-gedi-lidar-data-for-vegetation-studies/",
                    },
                    {
                        "inherited": True,
                        "rel": "http://esipfed.org/ns/fedsearch/1.1/documentation#",
                        "hreflang": "en-US",
                        "href": "https://lpdaac.usgs.gov/documents/989/GEDI_Quick_Guide_V2.pdf",
                    },
                    {
                        "inherited": True,
                        "rel": "http://esipfed.org/ns/fedsearch/1.1/documentation#",
                        "hreflang": "en-US",
                        "href": "https://lpdaac.usgs.gov/resources/e-learning/getting-started-gedi-l2a-version-2-data-python/",
                    },
                    {
                        "inherited": True,
                        "rel": "http://esipfed.org/ns/fedsearch/1.1/documentation#",
                        "hreflang": "en-US",
                        "href": "https://git.earthdata.nasa.gov/projects/LPDUR/repos/gedi-finder-tutorial-r/browse",
                    },
                    {
                        "inherited": True,
                        "rel": "http://esipfed.org/ns/fedsearch/1.1/documentation#",
                        "hreflang": "en-US",
                        "href": "https://git.earthdata.nasa.gov/projects/LPDUR/repos/gedi-finder-tutorial-python/browse",
                    },
                ],
                "concept_id": "G1201782029-NASA_MAAP",
                "datetime": "2020-12-31T23:23:02Z",
            },
            "geometry": {
                "coordinates": [
                    [
                        [-0.2387289, -7.5971209],
                        [2.8189966, -5.4423856],
                        [5.8716528, -3.2747626],
                        [8.9132468, -1.0797761],
                        [11.9384815, 1.1554717],
                        [14.9404437, 3.4468156],
                        [17.9126576, 5.8092283],
                        [20.8479939, 8.259201],
                        [23.7380778, 10.8151833],
                        [26.5736864, 13.4966606],
                        [29.3450799, 16.3238182],
                        [32.0403274, 19.319827],
                        [34.6464371, 22.5076979],
                        [37.1492987, 25.9115612],
                        [39.5291864, 29.5597367],
                        [41.7696059, 33.4734198],
                        [43.8475875, 37.6754714],
                        [45.7399801, 42.1817944],
                        [47.4203727, 47.001753],
                        [48.8627759, 52.1285012],
                        [50.0402224, 57.5428327],
                        [50.9290227, 63.2044527],
                        [51.5085858, 69.0547511],
                        [51.7642443, 75.0176386],
                        [51.7746316, 75.9956659],
                        [51.8249909, 75.994814],
                        [51.8145864, 75.015351],
                        [51.5586036, 69.0453025],
                        [50.9783437, 63.1882822],
                        [50.0885272, 57.5206382],
                        [48.9098095, 52.1011197],
                        [47.4659638, 46.9701174],
                        [45.7840169, 42.1467687],
                        [43.8900371, 37.6378822],
                        [41.8104732, 33.4339463],
                        [39.5685347, 29.5189717],
                        [37.1871726, 25.8699043],
                        [34.6829653, 22.4655454],
                        [32.0756085, 19.2774222],
                        [29.379222, 16.2813389],
                        [26.6068138, 13.4542411],
                        [23.7703001, 10.7728961],
                        [20.879429, 8.2170933],
                        [17.9434253, 5.7673228],
                        [14.9706524, 3.4051068],
                        [11.9682326, 1.1139361],
                        [8.9426599, -1.1211578],
                        [5.9008172, -3.3160383],
                        [2.8480234, -5.4835915],
                        [-0.209737, -7.6383013],
                        [-0.2387289, -7.5971209],
                    ]
                ],
                "type": "Polygon",
            },
            "links": [
                {
                    "rel": "self",
                    "href": "s3://nasa-maap-data-store/file-staging/nasa-map/GEDI02_A___002/2020.12.31/GEDI02_A_2020366232302_O11636_02_T08595_02_003_02_V002.h5",
                    "type": "application/json",
                }
            ],
            "assets": {
                "data": {
                    "href": "s3://nasa-maap-data-store/file-staging/nasa-map/GEDI02_A___002/2020.12.31/GEDI02_A_2020366232302_O11636_02_T08595_02_003_02_V002.h5",
                    "type": "application/x-hdf5",
                    "roles": ["data"],
                },
                "metadata": {"href": "https://lpdaac.usgs.gov/", "roles": ["metadata"]},
                "documentation": {
                    "href": "https://lpdaac.usgs.gov/documents/982/gedi_l2a_dictionary_P003_v2.html",
                    "roles": ["documentation"],
                },
            },
            "bbox": [-0.2387289, -7.6383013, 51.8249909, 75.9956659],
            "stac_extensions": [],
            "collection": "GEDI02_A",
        }
    }

    handler(sample_event, {})
