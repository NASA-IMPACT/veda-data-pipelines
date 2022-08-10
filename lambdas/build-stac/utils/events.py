from typing import Dict, List, Literal, Optional, Union

from pydantic import BaseModel
import pystac


INTERVAL = Literal["month", "year"]


class BaseEvent(BaseModel, frozen=True):
    collection: str
    s3_filename: str

    asset_name: Optional[str] = None
    asset_roles: Optional[List[str]] = None
    asset_media_type: Optional[Union[str, pystac.MediaType]] = None


class CmrEvent(BaseEvent):
    granule_id: str


class RegexEvent(BaseEvent):
    filename_regex: str

    properties: Optional[Dict] = {}
    datetime_range: Optional[INTERVAL] = None


SupportedEvent = Union[RegexEvent, CmrEvent]
