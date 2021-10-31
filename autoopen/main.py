import multiprocessing
import time
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
        self.camera_pointer = {'pid': pid, 'cid': cid, 'aid': access_control_id}

        self.running = True
        self.start()

    def stop(self):
        self.running = False
        self._fp.stop()

    def _output_worker(self):
        for frame in self._fp.take_frames():
            if not self.running:
                break

            cv.imshow('frame', frame)

            if cv.waitKey(1) == 27:
                self.stop()

    def run(self):
        # srv = WebVideoStreamServer()
        self._fp.start()

        Thread(target=self._output_worker).start()

        while self.running:
            stream = 0
            # stream = "/home/petr/Downloads/Telegram Desktop/test.mp4"
            # _api.get_video_stream(self.camera_pointer['cid'])
            last_opn = 0
            with StreamReaderThread(stream) as cap:
                while self.running and cap.running:
                    frame = cap.frame
                    if frame is None:
                        continue

                    # start_time = time.time()

                    motion = True
                    # if self._motion is not None:
                    #     self._motion(frame)
                    #     motion = self._motion.state

                    # print(round((time.time() - start_time) * 1000), "ms")

                    if motion:
                        self._fp(frame)

                        # frame, faces = fp(cap.frame, debug=True)
                        # if len(faces) > 0 and (time.time() - last_opn) > 5:
                        # print(faces)
                        # self._api.open_door(self.camera_pointer['pid'], self.camera_pointer['aid'])
                        # last_opn = time.time()

                    # print(round((time.time() - start_time) * 1000), "ms")

                    # srv(frame)

                    # gray = cv.cvtColor(cap.frame, cv.COLOR_BGR2GRAY)
                    # cv.imshow('Frame', gray)

        cv.destroyAllWindows()


api = IntercomAPI(getenv('DOMRU_LOGIN'), getenv('DOMRU_PASSWORD'))
# _api.login()
api.set_session(MyhomeSession(accessToken=getenv('SESSION_TOKEN'),
                              refreshToken=getenv('SESSION_REFRESH_TOKEN'),
                              operatorId=int(getenv('SESSION_OPERATOR'))))

fp = FaceProcessor(known_face_samples=FaceProcessor.scan_samples_dir('/home/petr/Pictures/faces'), threshold=100000)
md = MotionDetector()

io = IntercomOpener(api, fp, md, int(getenv('CAMERA_ID')))

while True:
    pass
