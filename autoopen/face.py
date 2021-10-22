import os
from time import time

import cv2 as cv
import face_recognition
import numpy as np


class FaceProcessor:
    def __init__(self, known_face_samples: list[str], threshold=0.5):
        self.known_face_encodings, self.known_face_names = self.image_to_encoding_and_name(known_face_samples)
        self.threshold = threshold

    @staticmethod
    def scan_samples_dir(path: str):
        return [os.path.join(path, i) for i in os.listdir(path)]

    @staticmethod
    def image_to_encoding_and_name(image_files: list[str]):
        """use format for files: 'username-id.ext' """
        return [face_recognition.face_encodings(face_recognition.load_image_file(i))[0] for i in image_files], \
               [i.split('/')[-1].split('-')[0] for i in image_files]

    def __call__(self, new_frame, debug=False):
        start_time = time()

        frame = cv.resize(new_frame[:, :, ::-1], (0, 0), fx=0.5, fy=0.5)
        face_locations = face_recognition.face_locations(frame, 1)
        face_encodings = face_recognition.face_encodings(frame, face_locations, num_jitters=1, model="small")

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

            print(round((time() - start_time) * 1000), "ms")

        return frame, {i[0]: i[1] for i in found if i is not None}
