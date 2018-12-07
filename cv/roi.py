import cv2

cap = cv2.VideoCapture(0)
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

cap.release()
cv2.destroyAllWindows()