from typing import Any, List, Optional

from pydantic import BaseModel


class ParentGroup(BaseModel):
    ID: int
    Name: str
    ParentID: Optional[int]


class Camera(BaseModel):
    ID: int
    Name: str
    IsActive: int
    IsSound: int
    RecordType: int
    Quota: int
    MaxBandwidth: Any
    HomeMode: int
    Devices: Any
    ParentGroups: List[ParentGroup]
    State: int
    TimeZone: int
    MotionDetectorMode: str
    ParentID: str


class CamerasResponse(BaseModel):
    data: List[Camera]
