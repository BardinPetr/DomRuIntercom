import logging
import pickle
import time
from multiprocessing import Manager, cpu_count, Process
from threading import Thread

import cv2 as cv
import face_recognition
import numpy as np
from sklearn.neighbors import KNeighborsClassifier


class FaceProcessor(Thread):
    def __init__(self, classifier_file: str, threshold=0.5, debug_draw=False, detected_timeout=5):
        super().__init__()
        with open(classifier_file, 'rb') as f:
            self._clf: KNeighborsClassifier = pickle.load(f)

        logging.debug("Classifier loaded")

        self._on_detect = None
        self.threshold = threshold
        self.debug_draw = debug_draw
        self.detected_timeout = detected_timeout

        self._mp_manager = Manager().Namespace()
        self._mp_manager.frame_id = 0
        self._mp_manager.cur_read_worker_id = 0
        self._mp_manager.cur_write_worker_id = 0
        self._mp_manager.frame_delay = 0
        self._mp_manager.running = True
        self._mp_manager.last_detected = time.time()

        self._input_frames = Manager().dict()
        self._output_frames = Manager().dict()

        self._processes = []
        self._processes_count = cpu_count()

        self.last_took_id = 0

    def _next_id(self, cur):
        return (cur + 1) % self._processes_count

    def _prev_id(self, cur):
        return (cur - 1) % self._processes_count

    def set_on_detected(self, cb):
        self._on_detect = cb

    def start(self):
        for i in range(self._processes_count):
            self._processes.append(Process(target=self._worker, args=(i,)))
            self._processes[-1].start()

    def stop(self):
        self._mp_manager.running = False

    def __call__(self, frame):
        if self._mp_manager.frame_id != self._next_id(self._mp_manager.cur_read_worker_id):
            self._input_frames[self._mp_manager.frame_id] = frame
            self._mp_manager.frame_id = self._next_id(self._mp_manager.frame_id)

    def _worker(self, self_id):
        while self._mp_manager.running:
            while (self._mp_manager.cur_read_worker_id != self_id or
                   self._mp_manager.cur_read_worker_id != self._prev_id(self._mp_manager.frame_id)) and \
                    self._mp_manager.running:
                time.sleep(0.01)

            frame = self._input_frames[self_id]

            self._mp_manager.cur_read_worker_id = self._next_id(self._mp_manager.cur_read_worker_id)

            frame = self._recognise(frame)

            while self._mp_manager.cur_write_worker_id != self_id:
                time.sleep(0.01)

            self._output_frames[self_id] = frame[:, :, ::-1]
            self._mp_manager.cur_write_worker_id = self._next_id(self._mp_manager.cur_write_worker_id)

    def _recognise(self, new_frame):
        frame = cv.resize(new_frame[:, :, ::-1], (0, 0), fx=0.75, fy=0.75)
        face_locations = face_recognition.face_locations(frame, 1)

        if len(face_locations) == 0:
            return frame

        face_encodings = face_recognition.face_encodings(frame, face_locations, num_jitters=1, model="large")

        res = {
            name: (dst, loc)
            for name, dst, loc in
            zip(self._clf.predict(face_encodings),
                self._clf.kneighbors(face_encodings, 1)[0].reshape(-1),
                face_locations)
            if dst < self.threshold
        }

        if len(res) == 0:
            return frame

        if self.debug_draw:
            for name, (dist, (top, right, bottom, left)) in res.items():
                cv.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                cv.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv.FILLED)
                cv.putText(frame, f"{name}@{dist:.1f}", (left + 6, bottom - 6),
                           cv.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)

        if time.time() - self._mp_manager.last_detected > self.detected_timeout:
            self._on_detect(list(res.keys()))
            self._mp_manager.last_detected = time.time()

        return frame

    def take_frames(self):
        fpss = []
        last_time = time.time()
        while self._mp_manager.running:
            cw = self._mp_manager.cur_write_worker_id
            if self.last_took_id != cw:
                self.last_took_id = cw

                fpss.append(time.time() - last_time)
                last_time = time.time()
                if len(fpss) > 5 * self._processes_count:
                    fpss.pop(0)
                fps = len(fpss) / np.sum(fpss)
                # logging.debug("FPS: %.2f" % fps)

                yield self._output_frames[self._prev_id(cw)]
