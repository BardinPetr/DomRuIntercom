from datetime import datetime, timezone, timedelta
from typing import Optional

from uplink import Consumer, Body, post, returns, json, response_handler, get, Header

from src.exceptions import InvalidUserCredentials
from src.models import MyhomeSession
from src.tools import generate_auth_hashes


def raise_for_status(response):
    if response.status_code == 403:
        raise InvalidUserCredentials()
    response.raise_for_status()
    return response


class BaseAPI(Consumer):

    @response_handler(raise_for_status)
    @returns.json
    @json
    @post("auth/v2/auth/{path_login}/password")
    def _password_auth(self, path_login: str, **auth_body: Body) -> MyhomeSession:
        """Executes authorization using hash pair"""

    @response_handler(raise_for_status)
    @returns.json
    @get("auth/v2/session/refresh")
    def _refresh_session(self, refresh_token: Header("Bearer"), operator_id: Header("Operator")) -> MyhomeSession:
        """Executes authorization using hash pair"""


class IntercomAPI(BaseAPI):

    def __init__(self, login: str, password: str):
        super().__init__('https://myhome.novotelecom.ru/')
        self.cred = (login, password)
        self.current_session: Optional[MyhomeSession] = None

    def set_session(self, session: MyhomeSession):
        print(session)
        self.current_session = session
        self.session.headers["Authorization"] = f'Bearer {session.token}'

    def open_door(self):
        pass

    def login(self) -> MyhomeSession:
        date = datetime.now(tz=timezone(timedelta(hours=0)))
        h1, h2 = generate_auth_hashes(self.cred[0], self.cred[1], date)
        ts = date.isoformat(sep='T', timespec='milliseconds').replace('+00:00', 'Z')

        res = self._password_auth(
            self.cred[0],
            login=self.cred[0],
            hash1=h1,
            hash2=h2,
            timestamp=ts
        )

        self.set_session(res)
        self.refresh_token()
        return res

    def refresh_token(self) -> MyhomeSession:
        if self.current_session.refresh_token:
            del self.session.headers["Authorization"]
            res = self._refresh_session(self.current_session.refresh_token, self.current_session.operator_id)
            res.operator_id = self.current_session.operator_id
            self.set_session(res)
            return res
        else:
            raise Exception("No refresh token")


