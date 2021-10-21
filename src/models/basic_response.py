from typing import Optional, Union

from pydantic import BaseModel


class StatusResponse(BaseModel):
    status: bool
    errorCode: Optional[Union[str, int]]
    errorMessage: Optional[Union[str, int]]


class BasicResponse(BaseModel):
    data: StatusResponse
