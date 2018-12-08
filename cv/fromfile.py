import cv2
import numpy as np

frame = cv2.imread('img/2018-11-30-205421.jpg')

# frame = cv2.imread('img/2018-11-30-205428.jpg')
# r = cv2.selectROI(frame)
r = (65, 131, 522, 56)
print(r)

# Crop image
imCrop = frame[int(r[1]):int(r[1] + r[3]), int(r[0]):int(r[0] + r[2])]
imCrop = cv2.GaussianBlur(imCrop, (7, 7), 0)
edged  = cv2.Canny(imCrop, 30, 150)

 (_, cnts, _) = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # sort the contours from left-to-right and initialize the
    # 'pixels per metric' calibration variable

if len(cnts) > 0:
    (cnts, _) = contours.sort_contours(cnts)
    cv2.drawContours(imCrop, [cnts], -1, (0, 255, 0), 2)

# Display cropped image
cv2.imshow("Crop", imCrop)

chan = cv2.split(imCrop)
for c in chan:
    print("min: {}, max {}".format(c.min(), c.max()))

lower = (91, 141, 160)
upper = (167, 186, 198)
mask = cv2.inRange(imCrop, lower, upper)
output = cv2.bitwise_not(imCrop, imCrop, mask = mask)

cv2.imshow("Crop", output)
cv2.waitKey(0)
cv2.destroyAllWindows()
