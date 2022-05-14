from typing import List, Any, Optional

from pydantic import BaseModel


class KladrAddress(BaseModel):
    index: Optional[str]
    region: Optional[str]
    district: Optional[str]
    city: Optional[str]
    locality: Optional[str]
    street: Optional[str]
    house: Optional[str]
    building: Optional[str]
    apartment: Optional[str]


class Address(BaseModel):
    kladrAddress: KladrAddress
    kladrAddressString: str
    visibleAddress: str
    groupName: str


class Location(BaseModel):
    longitude: float
    latitude: float


class AccessControl(BaseModel):
    id: int
    name: str
    forpostGroupId: str
    forpostAccountId: Any
    type: str
    allowOpen: bool
    allowVideo: bool
    allowCallMobile: bool
    entrances: List


class Place(BaseModel):
    id: int
    address: Address
    location: Location
    autoArmingState: bool
    autoArmingRadius: int
    previewAvailable: bool
    videoDownloadAvailable: bool
    controllers: List
    accessControls: List[AccessControl]
    cameras: List


class Subscriber(BaseModel):
    id: int
    name: str
    accountId: str
    nickName: Any


class Payment(BaseModel):
    useLink: bool


class SubscriberPlace(BaseModel):
    id: int
    subscriberType: str
    subscriberState: str
    place: Place
    subscriber: Subscriber
    guardCallOut: Any
    payment: Payment
    blocked: bool


class SubscriberPlaceResponse(BaseModel):
    data: List[SubscriberPlace]
