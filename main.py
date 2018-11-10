import argparse
from scipy.spatial import distance as dist
from imutils import perspective
import maestro
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
# cap.set(cv2.CAP_PROP_EXPOSURE, 1)
cap.set(cv2.CAP_PROP_AUTOFOCUS, 0) # turn the autofocus off
cap.set(cv2.CAP_PROP_FOCUS, 0)

def nothing(x):
    pass
TOP = 250
BOTTOM = TOP + 150

def pre_process(frame):
    image = frame[TOP:BOTTOM, 0:600]
    #image = frame


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

    return image, cnts

R = 3440
D = np.array([18.97, 21.2, 18, 23.85])
D = D * D
d = (D / D[2]) * R
d = d.round()

num_of_coins = 0

def get_con_value(coin_area):
    val = 0
    servo_target = 4 * 1500
    RANGE = 300
    if in_rage(coin_area, d[0], RANGE):
        val = 0.01
        servo_target = 4 * 1000

    if in_rage(coin_area, d[1], RANGE):
        val = 0.05
        servo_target = 4 * 1900

    if in_rage(coin_area, d[2], RANGE):
        val = 0.10
        servo_target = 4 * 1400

    if in_rage(coin_area, d[3], RANGE):
        val = 0.25
        servo_target = 4 * 1000
    return val, servo_target


# Creating a windows for later use
cv2.namedWindow('Coins')

# Creating track bar for min and max for hue, saturation and value
# You can adjust the defaults as you like
cv2.createTrackbar('gain', 'Image', 7, 255, nothing)

state = 0

WAIT_FOR_COIN = 0
CALC_VALUE = 1
WAIT_FOR_NEXT = 2

tot = 0
last_area = -1
last_val = -1
coin_area = -1
n = 0
coin_area_tmp = 0



servo = maestro.Controller()
def in_rage(x, val, tol):
    return x >= val - tol and x <= val + tol

while (1):

    _, frame = cap.read()
    image, cnts = pre_process(frame)

    coins = image.copy()
    cX = 0
    try:
        for c in cnts:
            # compute the center of the contour, then detect the name of the
            # shape using only the contour
            M = cv2.moments(c)
            if M["m00"] != 0:
                ratio = image.shape[0] / float(image.shape[0])
                cX = int((M["m10"] / M["m00"]) * ratio)
                cY = int((M["m01"] / M["m00"]) * ratio)
                cv2.circle(coins, (cX, cY), 3, (255, 0, 0), -1)
                cv2.drawContours(coins, cnts, -1, (0, 255, 0), 2)


            coin_area = cv2.contourArea(c)
            val, servo_target = get_con_value(coin_area)
            cv2.putText(coins, "cY {}, val = {}, tot = {}".format(coin_area, val, tot),(5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            if state == WAIT_FOR_COIN:
                if val > 0:
                    coin_area_tmp += coin_area
                    n += 1
                    print(coin_area)
                if cX < 150 and n > 0:
                    state = CALC_VALUE

            if state == CALC_VALUE:
                coin_area = coin_area_tmp/n
                print("n={}, coin_area={}".format(n, coin_area))
                val, servo_target = get_con_value(coin_area)
                servo.set_target(0, servo_target)
                tot += val
                last_val = val
                last_area = round(coin_area)
                n = 0
                coin_area_tmp = 0
                num_of_coins += 1
                state = WAIT_FOR_NEXT


            if state == WAIT_FOR_NEXT:
                if cX > 500:
                    state = WAIT_FOR_COIN
    except:
        pass

    cv2.line(coins, (150, 0), (150, BOTTOM), (255, 0, 255), 2)
    cv2.line(coins, (500, 0), (500, BOTTOM), (255, 0, 0), 2)
    status_text ="cX: {}, State {}, Tot {:.2f}, last_area = {:.0f}, last_val = {:.2f}, #={}".format(cX, state, tot, last_area, last_val, num_of_coins)
    cv2.putText(coins, status_text, (5, 120), cv2.FONT_HERSHEY_SIMPLEX,0.5, (0, 0, 255), 1)
    cv2.imshow("RAW", frame)
    cv2.imshow("Image", coins)
    k = cv2.waitKey(5) & 0xFF
    if k == 27: #or cY > 200:
        break
    elif k == 114:
        tot = 0
    else:
        if k < 255:
            print(k)

cap.release()
cv2.destroyAllWindows()