import argparse
from scipy.spatial import distance as dist
from imutils import perspective
from imutils import contours
import imutils
import cv2
import cv2 as cv
import numpy as np


def midpoint(ptA, ptB):
    return ((ptA[0] + ptB[0]) * 0.5, (ptA[1] + ptB[1]) * 0.5)


def auto_canny(image, sigma=0.33):
    # compute the median of the single channel pixel intensities
    v = np.median(image)

    # apply automatic Canny edge detection using the computed median
    lower = int(max(0, (1.0 - sigma) * v))
    upper = int(min(255, (1.0 + sigma) * v))
    edged = cv2.Canny(image, lower, upper)

    # return the edged image
    return edged


# Take input from webcam
cap = cv2.VideoCapture(-1)

# Reduce the size of video to 320x240 so rpi can process faster
#cap.set(3, 320)
#cap.set(4, 240)


def nothing(x):
    pass


def wait_for_coin():
    pass


def get_contours():
    _, frame = cap.read()
    #image = frame[0:400, 100:220]
    image = frame

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (11, 11), 0)
    # cv2.imshow("Image", blurred)

    # The first thing we are going to do is apply edge detection to
    # the image to reveal the outlines of the coins
    edged = cv2.Canny(blurred, 30, 150)
    # cv2.imshow("Edges", edged)

    # Find contours in the edged image.
    # NOTE: The cv2.findContours method is DESTRUCTIVE to the image
    # you pass in. If you intend on reusing your edged image, be
    # sure to copy it before calling cv2.findContours
    (_, cnts, _) = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # sort the contours from left-to-right and initialize the
    # 'pixels per metric' calibration variable

    if len(cnts) > 0:
        (cnts, _) = contours.sort_contours(cnts)

    return [cnts, edged]


def get_cm(img, cnts):
    if len(cnts)==0:
        return []

    for c in cnts:
        # compute the center of the contour, then detect the name of the
        # shape using only the contour
        M = cv2.moments(c)
        ratio =1
        if M["m00"] != 0:
            cX = int((M["m10"] / M["m00"]) * ratio)
            cY = int((M["m01"] / M["m00"]) * ratio)
            cv2.circle(img, (cX, cY), 3, (255, 0, 0), -1)
            cv2.drawContours(img, cnts, -1, (0, 255, 0), 2)
    return [cX, cY]


def get_coin_value(image, c):
    # compute the rotated bounding box of the contour
    orig = image.copy()
    box = cv2.minAreaRect(c)
    box = cv2.cv.BoxPoints(box) if imutils.is_cv2() else cv2.boxPoints(box)
    box = np.array(box, dtype="int")

    # order the points in the contour such that they appear
    # in top-left, top-right, bottom-right, and bottom-left
    # order, then draw the outline of the rotated bounding
    # box
    box = perspective.order_points(box)
    cv2.drawContours(orig, [box.astype("int")], -1, (0, 255, 0), 2)

    # loop over the original points and draw them
    # for (x, y) in box:
    #    cv2.circle(orig, (int(x), int(y)), 5, (0, 0, 255), -1)

    (tl, tr, br, bl) = box
    (tltrX, tltrY) = midpoint(tl, tr)
    (blbrX, blbrY) = midpoint(bl, br)

    # compute the midpoint between the top-left and top-right points,
    # followed by the midpoint between the top-righ and bottom-right
    (tlblX, tlblY) = midpoint(tl, bl)
    (trbrX, trbrY) = midpoint(tr, br)

    # draw the midpoints on the image
    # cv2.circle(orig, (int(tltrX), int(tltrY)), 5, (255, 0, 0), -1)
    # cv2.circle(orig, (int(blbrX), int(blbrY)), 5, (255, 0, 0), -1)
    # cv2.circle(orig, (int(tlblX), int(tlblY)), 5, (255, 0, 0), -1)
    # cv2.circle(orig, (int(trbrX), int(trbrY)), 5, (255, 0, 0), -1)

    # draw lines between the midpoints
    cv2.line(orig, (int(tltrX), int(tltrY)), (int(blbrX), int(blbrY)),
             (255, 0, 255), 2)
    cv2.line(orig, (int(tlblX), int(tlblY)), (int(trbrX), int(trbrY)),
             (255, 0, 255), 2)
    # compute the Euclidean distance between the midpoints
    dA = dist.euclidean((tltrX, tltrY), (blbrX, blbrY))
    dB = dist.euclidean((tlblX, tlblY), (trbrX, trbrY))

    # if the pixels per metric has not been initialized, then
    # compute it as the ratio of pixels to supplied metric
    # (in this case, inches)

    # compute the size of the object
    dimA = dA
    dimB = dB

    # draw the object sizes on the image
    cv2.putText(orig, "{:.0f}".format(dimA),
                (int(tltrX - 15), int(tltrY - 10)), cv2.FONT_HERSHEY_SIMPLEX,
                0.5, (255, 255, 255), 2)
    cv2.putText(orig, "{:.0f}".format(dimB),
                (int(trbrX + 10), int(trbrY)), cv2.FONT_HERSHEY_SIMPLEX,
                0.5, (255, 255, 255), 2)

    if dimA > 45 and dimA < 52:
        val = 0.1
    elif dimA >= 52 and dimA < 59:
        val = 0.05
    elif dimA >= 61:
        val = 0.25
    else:
        val = 0

    return val


def run():
    state = 0
    WAIT_FOR_COIN = 0
    GET_COIN_VALUE = 1
    new_coin_threshold = 10

    while (1):
        [cnts, image] = get_contours()

        cv2.line(image, (0, 100), (400, 100), (255, 0, 255), 2)
        cv2.line(image, (0, 200), (400, 200), (255, 0, 255), 2)
        cv2.imshow("Coins", image)

        cm = get_cm(image, cnts)

        if state == WAIT_FOR_COIN:
            if cm[1] > new_coin_threshold:
                state = GET_COIN_VALUE

        if state == GET_COIN_VALUE:
            #get_coin_value(image, cnts)
            pass

        # show the output image
        cv2.imshow("Image", image)

        k = cv2.waitKey(5) & 0xFF
        if k == 27:  # or cY > 200:
            break

run()
cap.release()
cv2.destroyAllWindows()