from cvutil.shapedetector import ShapeDetector
import argparse
import imutils
import cv2
import cv2 as cv
import numpy as np


kernel = np.ones((5, 5), np.uint8)

# m = maestro.Controller()

# Take input from webcam
cap = cv2.VideoCapture(-1)

# Reduce the size of video to 320x240 so rpi can process faster
cap.set(3, 320)
cap.set(4, 240)


def nothing(x):
    pass


# Creating a windows for later use
cv2.namedWindow('Mask')
cv2.namedWindow('Image')

# Creating track bar for min and max for hue, saturation and value
# You can adjust the defaults as you like
cv2.createTrackbar('t', 'Image', 100, 255, nothing)
cv2.createTrackbar('d', 'Image', 100, 255, nothing)
# cv2.createTrackbar('gain','Image',1,255,nothing)


# My experimental values
# hmn = 12
# hmx = 37
# smn = 145
# smx = 255
# vmn = 186
# vmx = 255


while (1):

    buzz = 0
    # gain = cv2.getTrackbarPos('gain','Image')
    gain = -1;
    cap.set(cv.CAP_PROP_EXPOSURE, gain);
    _, frame = cap.read()
    r = (102, 50, 533, 59)
    frame = frame[int(r[1]):int(r[1] + r[3]), int(r[0]):int(r[0] + r[2])]

    image = frame
    # image = cv2.imread(args["image"])
    resized = imutils.resize(image, width=300)
    ratio = image.shape[0] / float(resized.shape[0])

    # convert the resized image to grayscale, blur it slightly,
    # and threshold it
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    t = cv2.getTrackbarPos('t', 'Image')
    thresh = cv2.threshold(blurred, t, 255, cv2.THRESH_BINARY)[1]
    cv2.imshow("Mask", thresh)

    # find contours in the thresholded image and initialize the
    # shape detector
    cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if imutils.is_cv2() else cnts[1]
    sd = ShapeDetector()

    # loop over the contours
    for c in cnts:

        # compute the center of the contour, then detect the name of the
        # shape using only the contour
        M = cv2.moments(c)

        if M["m00"] != 0:
            cX = int((M["m10"] / M["m00"]) * ratio)
            cY = int((M["m01"] / M["m00"]) * ratio)
            shape = sd.detect(c)

            # multiply the contour (x, y)-coordinates by the resize ratio,
            # then draw the contours and the name of the shape on the image
            c = c.astype("float")
            c *= ratio
            c = c.astype("int")
            cv2.drawContours(image, [c], -1, (0, 255, 0), 2)
            cv2.circle(image, (cX, cY), 3, (255, 0, 0), -1)
            # cv2.putText(image, " [{0},{1}]".format(cX, cY), (cX, cY), cv2.FONT_HERSHEY_SIMPLEX,
            #     0.5, (255, 255, 255), 2)

            # show the output image

        cv2.imshow("Image", image)

    k = cv2.waitKey(5) & 0xFF
    if k == 27:
        break

cap.release()
cv2.destroyAllWindows()
x.setTarget(3, 0 * 1500)