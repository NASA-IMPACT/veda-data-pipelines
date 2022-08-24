from typing import Dict, List, Literal, Optional, Union

from pydantic import BaseModel, constr, Field
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

    start_datetime: Optional[constr(regex=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")] = None
    end_datetime: Optional[constr(regex=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")] = None
    single_datetime: Optional[constr(regex=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")] = None

    properties: Optional[Dict] = Field(default_factory=dict)
    datetime_range: Optional[INTERVAL] = None


SupportedEvent = Union[RegexEvent, CmrEvent]
