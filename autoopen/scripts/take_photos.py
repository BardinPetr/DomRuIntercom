import os.path
import sys
from shutil import rmtree
from time import time

import cv2
import face_recognition

if len(sys.argv) != 3:
    print('Usage: python3 take_photos.py user_name root_photos_dir')
else:
    name, path = sys.argv[1:3]
    path = os.path.join(path, name)

    if os.path.isdir(path):
        rmtree(path)

    os.mkdir(path)

    cap = cv2.VideoCapture(0)

    cnt = 0
    ts = time()
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if time() - ts > 0.1:
            face_locations = face_recognition.face_locations(frame, 2)
            if len(face_locations) == 1:
                (top, right, bottom, left) = face_locations[0]
                face = frame[top:bottom, left: right]
                cv2.imwrite(f"{path}/{cnt}.jpg", face)

                ts = time()
                cnt += 1

        cv2.imshow('temp', frame)
        cv2.waitKey(1)

        if cnt > 100:
            break

    cap.release()
    cv2.destroyAllWindows()
