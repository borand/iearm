import argparse
from scipy.spatial import distance as dist
import cv2
from scipy.spatial import distance as dist
from imutils import perspective
from imutils import contours
import imutils
import cvutils
import numpy as np


def auto_canny(image, sigma=0.33):
    # compute the median of the single channel pixel intensities
    v = np.median(image)

    # apply automatic Canny edge detection using the computed median
    lower = int(max(0, (1.0 - sigma) * v))
    upper = int(min(255, (1.0 + sigma) * v))
    edged = cv2.Canny(image, lower, upper)

    # return the edged image
    return edged

def nothing(x):
    pass

# Take input from webcam
cap = cv2.VideoCapture(0)
# cap.set(3, 320)
# cap.set(4, 240)
_, frame = cap.read()


r = (57, 40, 550, 80)
r = None
# Read image
# Select ROI
if r is None:
    r, frame = cvutils.preselect(cam=cap)

# Creating a windows for later use
cv2.namedWindow('Image')
cv2.namedWindow('Frame')
cv2.namedWindow('Fmask')
cv2.namedWindow('Canny')

# Creating track bar for min and max for hue, saturation and value
# You can adjust the defaults as you like
cv2.createTrackbar('Hist', 'Image', 7, 255, nothing)
cv2.createTrackbar('blur', 'Image', 3, 12, nothing)

# fgbg = cv2.createBackgroundSubtractorMOG2()
fgbg = cv2.bgsegm.createBackgroundSubtractorMOG(history=20)

while (1):
    hist = cv2.getTrackbarPos('Hist', 'Image')
    b    = cv2.getTrackbarPos('blur', 'Image')

    _, frame = cap.read()
    image = frame[int(r[1]):int(r[1] + r[3]), int(r[0]):int(r[0] + r[2])]
    [cnts, image] = cvutils.get_contours(image)
    cm = cvutils.get_cm(image, cnts)

    cv2.imshow('Image', image)


    k = cv2.waitKey(5) & 0xFF
    if k == 27:
        break

cap.release()
cv2.destroyAllWindows()