from os import getenv
from threading import Thread

import cv2 as cv
from dotenv import load_dotenv

from autoopen.camera import StreamReaderThread
from autoopen.face import FaceProcessor
from autoopen.motiondetector import MotionDetector
from src.api import IntercomAPI
from src.models.session import MyhomeSession

load_dotenv()


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
        self.camera_pointer = [pid, access_control_id, cid]

        self.running = True
        self.start()

    def stop(self):
        self.running = False

    # def _proc_frame(self, frame):

    def run(self):
        while self.running:
            stream = "/home/petr/Downloads/Telegram Desktop/test.mp4"  # _api.get_video_stream(cid)
            with StreamReaderThread(stream) as cap:
                while self.running and cap.running:
                    frame = cap.frame
                    if frame is None:
                        continue

                    motion = True
                    if self._motion is not None:
                        self._motion(frame)
                        motion = self._motion.state

                    if motion:
                        img, faces = fp(cap.frame, debug=True)
                        if len(faces) > 0:
                            print(faces)
                        cv.imshow('Frame', img)
                    else:
                        cv.imshow('Frame2', cap.frame)

                    # gray = cv.cvtColor(cap.frame, cv.COLOR_BGR2GRAY)
                    # cv.imshow('Frame', gray)
                    # cv.imshow('motion', cap.motion_mask)

                    if cv.waitKey(1) == 27:
                        self.running = False

        cv.destroyAllWindows()


api = IntercomAPI(getenv('DOMRU_LOGIN'), getenv('DOMRU_PASSWORD'))
# _api.login()
api.set_session(MyhomeSession(accessToken=getenv('SESSION_TOKEN'),
                              refreshToken=getenv('SESSION_REFRESH_TOKEN'),
                              operatorId=int(getenv('SESSION_OPERATOR'))))

fp = FaceProcessor(known_face_samples=FaceProcessor.scan_samples_dir('/home/petr/Desktop/faces'), threshold=100000)
md = MotionDetector()

io = IntercomOpener(api, fp, md, int(getenv('CAMERA_ID')))

while True:
    pass
