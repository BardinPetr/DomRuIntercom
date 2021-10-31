import os.path
import pickle
import sys
from math import sqrt

import cv2
import face_recognition
from sklearn import neighbors
from tqdm import tqdm

if len(sys.argv) != 3:
    print('Usage: python3 train_classifier.py root_photos_dir classifier_output_path')
else:
    photos_path, output_path = sys.argv[1:3]

    if not os.path.isdir(photos_path):
        raise Exception()

    X, Y = [], []

    for user in os.listdir(photos_path):
        dp = os.path.join(photos_path, user)
        if not os.path.isdir(dp):
            continue
        print(f"User {user}:")
        for i in tqdm(os.listdir(dp)):
            frame = cv2.imread(os.path.join(photos_path, user, i))
            face_locations = face_recognition.face_locations(frame, 1)
            if len(face_locations) != 1:
                continue
            X.append(face_recognition.face_encodings(frame, face_locations, num_jitters=2, model="large")[0])
            Y.append(user)

    # clf = svm.SVC(gamma='scale', probability=True)
    clf = neighbors.KNeighborsClassifier(n_neighbors=int(sqrt(len(X))), weights='distance')
    clf.fit(X, Y)

    with open(output_path, 'wb') as f:
        pickle.dump(clf, f)
