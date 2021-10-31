import os.path
import pickle
import sys
from math import sqrt

import cv2
import face_recognition
from sklearn import neighbors
from tqdm import tqdm

sys.argv += ["/home/petr/Pictures/faces/", "/home/petr/Pictures/faces/knn.bin"]
photos_path, output_path = sys.argv[1:3]

clf: neighbors.KNeighborsClassifier = pickle.load(open(output_path, 'rb'))

frame = cv2.imread('/home/petr/Pictures/faces0/Irina-0.png')
face_locations = face_recognition.face_locations(frame, 1)
test = face_recognition.face_encodings(frame, face_locations, num_jitters=2, model="large")

res = {name: (dst, loc) for name, dst, loc in
       zip(clf.predict(test), clf.kneighbors(test, 1)[0].reshape(-1), face_locations) if dst < 0.5}

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
