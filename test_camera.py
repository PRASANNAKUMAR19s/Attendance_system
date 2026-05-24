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

if __name__ == "__main__":
    # When run as a script show camera diagnostics, but avoid exiting during test collection
    sys.exit(0)
