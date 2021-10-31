from os import getenv
from threading import Thread

import cv2 as cv
from dotenv import load_dotenv

from autoopen.camera import StreamReaderThread
from autoopen.face import FaceProcessor
from autoopen.motiondetector import MotionDetector
from autoopen.stream_server import WebVideoStreamServer
from src.api import IntercomAPI

load_dotenv()

import logging

logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)


class IntercomOpener(Thread):
    def __init__(self,
                 api: IntercomAPI,
                 face_processor: FaceProcessor,
                 motion_detector: MotionDetector,
                 access_control_id: int):
        super().__init__(name=f'intercom-opener-{api.get_login()}')
        self._api = api
        self._fp = face_processor
        self._motion = motion_detector

        pid, cid = api.find_by_access_control(access_control_id)
        self.camera_pointer = {'pid': pid, 'cid': cid, 'aid': access_control_id}

        self.running = True
        self.start()

    def stop(self):
        self.running = False
        self._fp.stop()

    def _output_worker(self):
        srv = WebVideoStreamServer(open_browser=False)

        for frame in self._fp.take_frames():
            if not self.running:
                break

            # cv.imshow('frame', frame)
            # cv.imshow('motion', self._motion.motion_mask)
            srv(frame)

            if cv.waitKey(1) == 27:
                self.stop()

    def _open_door(self, user):
        # self._api.open_door(self.camera_pointer['pid'], self.camera_pointer['aid'])
        logging.info(f"Door opened for {user}")

    def run(self):
        self._fp.set_on_detected(lambda users: self._open_door(users[0]))
        self._fp.start()

        Thread(target=self._output_worker).start()

        while self.running:
            # stream = 0
            # stream = "/home/petr/Downloads/Telegram Desktop/test.mp4"
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
                        self._fp(frame)

        # cv.destroyAllWindows()


api = IntercomAPI(getenv('DOMRU_LOGIN'), getenv('DOMRU_PASSWORD'))

api.login()
# api.set_session(MyhomeSession(accessToken=getenv('SESSION_TOKEN'),
#                               refreshToken=getenv('SESSION_REFRESH_TOKEN'),
#                               operatorId=int(getenv('SESSION_OPERATOR'))))

fp = FaceProcessor(getenv('KNN_CLASSIFIER', './knn.bin'), threshold=float(getenv('THRESHOLD', 0.5)), debug_draw=True)
md = MotionDetector()

io = IntercomOpener(api, fp, md, int(getenv('CAMERA_ID')))

logging.debug("Basic init finished")

while True:
    pass
