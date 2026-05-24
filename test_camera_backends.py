import cv2

backends = [cv2.CAP_MSMF, cv2.CAP_DSHOW, cv2.CAP_VFW, cv2.CAP_ANY]
indices = range(0, 4)

for backend in backends:
    print("\n=== Testing backend", backend, "===")
    for i in indices:
        cap = cv2.VideoCapture(i, backend)
        opened = cap.isOpened()
        print(f"Index {i}: isOpened={opened}", end="")
        if opened:
            ret, frame = cap.read()
            print(f", read={ret}")
            if ret and frame is not None:
                print(" -> frame shape", frame.shape)
            else:
                print(" -> no frame")
        else:
            print("")
        cap.release()
