import cv2
import numpy as np
import sys

# --- Input video ---
cap = cv2.VideoCapture("input.mp4")

ret, prev = cap.read()
prev_gray = cv2.cvtColor(prev, cv2.COLOR_BGR2GRAY)
changed = prev
changed[:] = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    diff = cv2.absdiff(gray, prev_gray)

    # Threshold to mark changed pixels 
    _, mask = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)

    changed[mask > 0] = (0, 0, 255)  # mark changes in red

    cv2.imshow("Changed Pixels Mask", mask)
    cv2.imshow("All", changed)

    prev_gray = gray

    if cv2.waitKey(1) == 27:  # ESC to quit
        break

cap.release()
cv2.destroyAllWindows()
