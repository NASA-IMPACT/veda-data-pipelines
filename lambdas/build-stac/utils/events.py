from datetime import datetime
from typing import Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field
import pystac


INTERVAL = Literal["month", "year"]


class BaseEvent(BaseModel, frozen=True):
    collection: str
    s3_filename: str

    asset_name: Optional[str] = None
    asset_roles: Optional[List[str]] = None
    asset_media_type: Optional[Union[str, pystac.MediaType]] = None

    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    single_datetime: Optional[datetime] = None


class CmrEvent(BaseEvent):
    granule_id: str


class RegexEvent(BaseEvent):
    properties: Optional[Dict] = Field(default_factory=dict)
    datetime_range: Optional[INTERVAL] = None


SupportedEvent = Union[RegexEvent, CmrEvent]
