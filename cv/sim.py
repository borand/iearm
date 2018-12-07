import argparse
from scipy.spatial import distance as dist
import cv2
from scipy.spatial import distance as dist
from imutils import perspective
from imutils import contours
import imutils
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

if __name__ == '__main__':
    # Read image
    # Select ROI
    show_crosshair = False
    from_center = False
    r = cv2.selectROI(frame, from_center, show_crosshair)

    # Crop image
    imCrop = frame[int(r[1]):int(r[1] + r[3]), int(r[0]):int(r[0] + r[2])]

    # Display cropped image
    cv2.imshow("Image", imCrop)
    cv2.waitKey(0)


# Creating a windows for later use
cv2.namedWindow('Image')
cv2.namedWindow('Fmask')
cv2.namedWindow('Canny')

# Creating track bar for min and max for hue, saturation and value
# You can adjust the defaults as you like
cv2.createTrackbar('Hist', 'Image', 7, 255, nothing)
cv2.createTrackbar('gain', 'Image', 7, 255, nothing)

# fgbg = cv2.createBackgroundSubtractorMOG2()
fgbg = cv2.bgsegm.createBackgroundSubtractorMOG(history=10)

while (1):
    hist = cv2.getTrackbarPos('Hist', 'Image')
    gain = cv2.getTrackbarPos('gain', 'Image')

    _, frame = cap.read()
    image = frame[int(r[1]):int(r[1] + r[3]), int(r[0]):int(r[0] + r[2])]

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (11, 11), 0)
    # cv2.imshow("Image", blurred)

    # The first thing we are going to do is apply edge detection to
    # the image to reveal the outlines of the coins

    fgmask = fgbg.apply(blurred)
    edged = cv2.Canny(fgmask, 30, 150)

    cv2.imshow('Fmask', fgmask)
    cv2.imshow("Image", image)
    cv2.imshow("Image", edged)

    k = cv2.waitKey(5) & 0xFF
    if k == 27:
        break

cap.release()
cv2.destroyAllWindows()