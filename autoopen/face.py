import os
import time
from multiprocessing import Manager, cpu_count, Process
from threading import Thread

import cv2 as cv
import face_recognition
import numpy as np


class FaceProcessor(Thread):
    def __init__(self, known_face_samples: list[str], threshold=0.5):
        super().__init__()
        self.known_face_encodings, self.known_face_names = self.image_to_encoding_and_name(known_face_samples)
        self.threshold = threshold

        self._mp_manager = Manager().Namespace()
        self._mp_manager.frame_id = 0
        self._mp_manager.cur_read_worker_id = 0
        self._mp_manager.cur_write_worker_id = 0
        self._mp_manager.frame_delay = 0
        self._mp_manager.running = True

        self._input_frames = Manager().dict()
        self._output_frames = Manager().dict()

        self._processes = []
        self._processes_count = cpu_count()

        self.last_took_id = 0

    def _next_id(self, cur):
        return (cur + 1) % self._processes_count

    def _prev_id(self, cur):
        return (cur - 1) % self._processes_count

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

            time.sleep(self._mp_manager.frame_delay)

            frame = self._input_frames[self_id]

            self._mp_manager.cur_read_worker_id = self._next_id(self._mp_manager.cur_read_worker_id)

            frame, res = self._recognise(frame)

            while self._mp_manager.cur_write_worker_id != self_id:
                time.sleep(0.01)

            self._output_frames[self_id] = frame[:, :, ::-1]
            self._mp_manager.cur_write_worker_id = self._next_id(self._mp_manager.cur_write_worker_id)

    def _recognise(self, new_frame, debug=True):
        frame = cv.resize(new_frame[:, :, ::-1], (0, 0), fx=0.5, fy=0.5)
        face_locations = face_recognition.face_locations(frame, 1)
        face_encodings = face_recognition.face_encodings(frame, face_locations, num_jitters=1, model="large")

        found = []
        for enc in face_encodings:
            dists = face_recognition.face_distance(self.known_face_encodings, enc)
            idx_min = np.argmin(dists)
            found.append(
                (self.known_face_names[idx_min], dists[idx_min]) if dists[idx_min] < self.threshold else (None, None)
            )

        if debug:
            for (top, right, bottom, left), (name, _) in zip(face_locations, found):
                # if name is None:
                #     continue
                cv.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                cv.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv.FILLED)
                cv.putText(frame, str(name), (left + 6, bottom - 6), cv.FONT_HERSHEY_DUPLEX, 1.0, (255, 255, 255), 1)

        return frame, {i[0]: i[1] for i in found if i is not None}

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
                print("fps: %.2f" % fps)

                yield self._output_frames[self._prev_id(cw)]

    @staticmethod
    def scan_samples_dir(path: str):
        return [os.path.join(path, i) for i in os.listdir(path)]

    @staticmethod
    def image_to_encoding_and_name(image_files: list[str]):
        """use format for files: 'username-id.ext' """
        return [face_recognition.face_encodings(face_recognition.load_image_file(i))[0] for i in image_files], \
               [i.split('/')[-1].split('-')[0] for i in image_files]
