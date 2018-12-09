import cv2
from imutils import contours

def preselect(cam=None, image=None):

    if cam is None:
        cam = cv2.VideoCapture(0)

    if image is None:
        print("Capture with camera")
        _, frame = cam.read()
    else:
        frame = image

    show_crosshair = False
    from_center = False
    r = cv2.selectROI(frame, from_center, show_crosshair)
    return r, frame


def get_contours(image):

    # gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = image
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)
    # cv2.imshow("Image", blurred)

    # The first thing we are going to do is apply edge detection to
    # the image to reveal the outlines of the coins
    edged = cv2.Canny(blurred, 20, 150)
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
    else:
        cnts = []

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


if __name__ == "__main__":
    r,img = preselect()