from typing import Optional

from pydantic import BaseModel, Field


class MyhomeSession(BaseModel):
    token: str = Field('', alias='accessToken')
    refresh_token: str = Field('', alias='refreshToken')
    operator_id: Optional[int] = Field(None, alias='operatorId')
    token_expires_in: Optional[str] = Field(None, alias='expiresIn')
    refresh_token_expires_in: Optional[str] = Field(None, alias='refreshExpiresIn')
