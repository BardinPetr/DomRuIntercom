from datetime import datetime, timezone, timedelta
from typing import Optional, Union, Tuple

from uplink import Consumer, Body, post, returns, json, response_handler, get, Header, Field

from src.exceptions import InvalidUserCredentials
from src.models.basic_response import StatusResponse
from src.models.camera import CamerasResponse, Camera
from src.models.place import SubscriberPlaceResponse, SubscriberPlace
from src.models.session import MyhomeSession
from src.tools import generate_auth_hashes


def raise_for_status(response):
    if response.status_code == 403:
        raise InvalidUserCredentials()
    response.raise_for_status()
    return response


@response_handler(raise_for_status)
class BaseAPI(Consumer):

    @json
    @returns.json
    @post("auth/v2/auth/{path_login}/password")
    def _password_auth(self, path_login: str, **auth_body: Body) -> MyhomeSession:
        """Executes authorization using hash pair"""

    @returns.json
    @get("auth/v2/session/refresh")
    def _refresh_session(self, refresh_token: Header("Bearer")) -> MyhomeSession:
        """Refreshes session with refresh token from current session"""

    @returns.json
    @get("rest/v1/subscriberplaces")
    def _get_places(self) -> SubscriberPlaceResponse:
        """Lists all places of current user"""

    @returns.json
    @get("rest/v1/forpost/cameras")
    def _get_cameras(self) -> CamerasResponse:
        """Lists all cameras of current user"""

    @returns.json(key='data')
    @get("rest/v1/forpost/cameras/{cam_id}/video?LightStream=0")
    def _get_video_stream(self, cam_id: str):
        """Get stream for _camera"""

    @get("rest/v1/forpost/cameras/{cam_id}/snapshots")
    def _get_snapshot(self, cam_id: str):
        """Get snapshot of _camera"""

    @returns.json
    @get("rest/v1/forpost/cameras/{cam_id}/video?LightStream=0")
    def _get_stream(self, cam_id: str) -> CamerasResponse:
        """Get stream for _camera"""

    @json
    @returns.json(key='data', type=StatusResponse)
    @post("rest/v1/places/{place_id}/accesscontrols/{ac_id}/actions")
    def _execute_action(self, place_id: str, ac_id: str, action_name: Field(name='name', type=str)) -> StatusResponse:
        """Sends action to specified access control 'ac_id' in 'place_id'"""


class IntercomAPI(BaseAPI):

    def __init__(self, login: str, password: str):
        super().__init__('https://myhome.novotelecom.ru/')
        self._cred = (login, password)
        self.current_session: Optional[MyhomeSession] = None

    def get_login(self):
        return self._cred[0]

    def set_session(self, session: MyhomeSession):
        self.current_session = session
        self.session.headers["Authorization"] = f'Bearer {session.token}'
        self.session.headers["Operator"] = session.operator_id

    def login(self) -> MyhomeSession:
        date = datetime.now(tz=timezone(timedelta(hours=0)))
        h1, h2 = generate_auth_hashes(self._cred[0], self._cred[1], date)
        ts = date.isoformat(sep='T', timespec='milliseconds').replace('+00:00', 'Z')

        res = self._password_auth(
            self._cred[0],
            login=self._cred[0],
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
            res = self._refresh_session(self.current_session.refresh_token)
            res.operator_id = self.current_session.operator_id
            self.set_session(res)
            return res
        else:
            raise Exception("No refresh token")

    def get_places(self) -> dict[int, SubscriberPlace]:
        return {i.place.id: i for i in self._get_places().data}

    def get_cameras(self) -> dict[int, Camera]:
        return {i.ID: i for i in self._get_cameras().data}

    def get_cameras_by_forpost_group(self) -> dict[int, list[int]]:
        res = {}
        for i, cam in self.get_cameras().items():
            for j in cam.ParentGroups:
                res[j.ID] = res.get(j.ID, []) + [i]
        return res

    def get_intercoms_by_place_and_ac(self) -> dict[int, dict[int, list[int]]]:
        res = {}
        cams = self.get_cameras_by_forpost_group()
        for i, pl in self.get_places().items():
            res[i] = {}
            for j in pl.place.accessControls:
                res[i][j.id] = cams.get(int(j.forpostGroupId), [])
        return res

    def get_video_stream(self, cam_id: Union[str, int]) -> Optional[str]:
        return self._get_video_stream(str(cam_id)).get('URL', None)

    def get_snapshot(self, cam_id: Union[str, int]) -> Optional[str]:
        return self._get_snapshot(str(cam_id)).content

    def open_door(self, place_id, ac_id):
        return self._execute_action(place_id, ac_id, 'accessControlOpen')

    def find_by_access_control(self, acid) -> Tuple[Optional[int], Optional[int]]:
        """Returns [place_id, camera_id] from access_control_id"""
        intercoms = self.get_intercoms_by_place_and_ac()
        for pid, place in intercoms.items():
            cams = place.get(acid, [])
            if len(cams) > 0:
                return pid, cams[0]
        return None, None
