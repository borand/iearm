import argparse
from scipy.spatial import distance as dist
import cv2 as cv
import numpy as np

print(cv.__version__)

cap = cv.VideoCapture(0)
while (1):
    _, frame = cap.read()
    frame = frame[0:500, 245:315]
    #frame = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    cv.imshow("Image", frame)
    k = cv.waitKey(5) & 0xFF
    if k == 27: #or cY > 200:
        break  

cap.release()
cv.destroyAllWindows()