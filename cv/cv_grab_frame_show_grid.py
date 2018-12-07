import argparse
from scipy.spatial import distance as dist
import cv2
import numpy as np

print(cv2.__version__)

cap = cv2.VideoCapture(0)
_, frame = cap.read()
frame_size = frame.shape
print('Frame size {}'.format(frame_size))

while (1):
    _, frame = cap.read()

    for y in range(0,480,25):
        cv2.line(frame, (0, y), (640, y), (255, 0, 0), 1, 1)
        cv2.putText(frame, "[{0}]".format(y), (5, y+10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 250), 2)

    for x in range(0,640,25):
        cv2.line(frame, (x, 0), (x, 480), (255, 0, 0), 1, 1)

    # cv2.putText(frame, " [{0},{1}]".format(cX, cY), (cX, cY), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

    cv2.imshow("Image", frame)
    k = cv2.waitKey(5) & 0xFF
    if k == 27: #or cY > 200:
        break

cap.release()
cv2.destroyAllWindows()