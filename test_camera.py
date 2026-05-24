import cv2
import sys

print("OpenCV version:", cv2.__version__)
cap = cv2.VideoCapture(0)
print("isOpened:", cap.isOpened())
ret, frame = cap.read()
print("read ok:", ret)
if ret and frame is not None:
    print("frame shape:", getattr(frame, "shape", None))
else:
    print("No frame captured")
cap.release()
sys.exit(0)
