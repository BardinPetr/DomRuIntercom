from os import getenv
from threading import Thread

import cv2 as cv
from dotenv import load_dotenv

from autoopen.camera import StreamReaderThread
from autoopen.face import FaceProcessor
from autoopen.hass import HASSDeviceTrigger
from autoopen.motiondetector import MotionDetector
from autoopen.stream_server import WebVideoStreamServer
from src.api import IntercomAPI

load_dotenv()
import logging

logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)


class IntercomOpener:
    def __init__(self,
                 api: IntercomAPI,
                 face_processor: FaceProcessor,
                 motion_detector: MotionDetector,
                 access_control_id: int,
                 video_mode=0):
        self._cb = None
        self._api = api
        self._fp = face_processor
        self._motion = motion_detector
        self._video_mode = video_mode

        pid, cid = api.find_by_access_control(access_control_id)
        self.camera_pointer = {'pid': pid, 'cid': cid, 'aid': access_control_id}

        if self._video_mode == 2:
            self._video_srv = WebVideoStreamServer(open_browser=False)

        self.running = True

    def set_opened_callback(self, cb):
        self._cb = cb

    def stop(self):
        self.running = False
        self._fp.stop()

    def _show(self, frame):
        if self._video_mode == 1:
            cv.imshow('frame', frame)
            if cv.waitKey(1) == 27:
                self.stop()
        elif self._video_mode == 2:
            self._video_srv(frame)

    def _output_worker(self):
        for frame in self._fp.take_frames():
            if not self.running:
                break
            self._show(frame)

    def _open_door(self, users):
        name, (dist, _) = users[0]
        self._api.open_door(self.camera_pointer['pid'], self.camera_pointer['aid'])
        logging.info(f"Door opened for {name} with distance {dist}")
        if self._cb:
            self._cb(users[0])

    def run(self):
        self._fp.set_on_detected(self._open_door)
        self._fp.start()

        if self._video_mode != 0 and self._fp.processes_count != 0:
            Thread(target=self._output_worker).start()

        while self.running:
            stream = api.get_video_stream(self.camera_pointer['cid'])
            logging.debug(f"Got stream: {stream}")

            with StreamReaderThread(stream) as cap:
                while self.running and cap.running:
                    frame = cap.frame
                    if frame is None:
                        continue

                    motion = True
                    # if self._motion is not None:
                    #     self._motion(frame)
                    #     motion = self._motion.state

                    if motion:
                        ret = self._fp(frame)
                        if ret is not None:
                            self._show(ret)


api = IntercomAPI(getenv('DOMRU_LOGIN'), getenv('DOMRU_PASSWORD'))

api.login()
# api.set_session(MyhomeSession(accessToken=getenv('SESSION_TOKEN'),
#                               refreshToken=getenv('SESSION_REFRESH_TOKEN'),
#                               operatorId=int(getenv('SESSION_OPERATOR'))))

fp = FaceProcessor(getenv('KNN_CLASSIFIER', './knn.bin'),
                   threshold=float(getenv('THRESHOLD', 0.5)),
                   proc_cnt=int(getenv('PROCESSES_CNT', -1)),
                   debug_draw=True)
md = MotionDetector()

access_control_id = int(getenv('ACCESS_CONTROL_ID'))
io = IntercomOpener(api, fp, md,
                    access_control_id=access_control_id,
                    video_mode=int(getenv('VISUAL', 0)))

hass = HASSDeviceTrigger(getenv('MQTT_HOST'), int(getenv('MQTT_PORT', 1883)),
                         getenv('MQTT_USER'), getenv('MQTT_PASS'),
                         access_control_id)

io.set_opened_callback(hass.opened)

logging.debug("Basic init finished")

io.run()
