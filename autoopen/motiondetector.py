import cv2 as cv
import numpy as np

from autoopen.debounce import Debounce


class MotionDetector:
    def __init__(self, motion_size_thresh: float = 0.01, motion_active_time=5, motion_debounce_time=1):
        self._background_sub = cv.createBackgroundSubtractorMOG2()

        self._debounce = Debounce(motion_debounce_time)

        self.running = True

        self.motion_size = 0
        self.realtime_motion = False
        self.motion_mask = None

        self.motion_size_thresh = motion_size_thresh
        self.motion_active_time = motion_active_time

    @property
    def state(self):
        return self._debounce.value

    def __call__(self, frame):
        mask = self._background_sub.apply(frame)
        mask = cv.GaussianBlur(mask, (19, 19), 0)
        mask = cv.dilate(mask, None, iterations=1)
        cv.threshold(mask, 150, 255, cv.THRESH_BINARY, dst=self.motion_mask)

        self.motion_size = np.sum(mask) / (255 * mask.shape[0] * mask.shape[1])

        self.realtime_motion = self.motion_size > self.motion_size_thresh
        self._debounce.update(self.realtime_motion)
