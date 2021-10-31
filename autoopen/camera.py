from threading import Thread
from time import sleep, time

import cv2 as cv


class StreamReaderThread(Thread):
    def __init__(self, stream: str):
        self._camera = cv.VideoCapture(stream)

        self.running = True
        self.frame = None

        super().__init__(name='stream-reader-thread')
        self.start()

    def run(self):
        ts = time()
        while self.running:
            ret, frame = self._camera.read()
            if not ret or frame is None:
                self.running = False
                try:
                    self._camera.release()
                except:
                    pass

            self.frame = frame
            # if (time() - ts) > 9:
            # sleep(0.01)
            # ts = time()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.running = False
        self.join()
