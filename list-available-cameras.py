# camlist.py
# Lists all avaiable cameras attached to the computer
# Dependencies: pip install opencv-python
# Usage: python camlist.py

import cv2
index = 0
arr = []
while True:
    cap = cv2.VideoCapture(index, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
    if not cap.read()[0]:
        break
    else:
        arr.append(index)
    cap.release()
    index += 1
print(arr)