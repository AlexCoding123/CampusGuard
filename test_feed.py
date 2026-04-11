import cv2
import sys
from datetime import datetime

# Usage:
#   python test_feed.py                          -> uses webcam
#   python test_feed.py videos/fight_01.mp4     -> uses video file
#   python test_feed.py http://IP:8080/video    -> uses IP Webcam

source = sys.argv[1] if len(sys.argv) > 1 else 0

cap = cv2.VideoCapture(source)

if not cap.isOpened():
    print(f"ERROR: Could not open source: {source}")
    sys.exit(1)

# Reduce buffer lag on IP stream
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

CAMERA_NAME = "CAM 03 - HALLWAY B"
LOCATION    = "John Abbott College - Building A"

print(f"Feed opened: {source}")
print("Press Q to quit")

frame_count = 0
last_faces = []  # reuse last detection between frames

while True:
    ret, frame = cap.read()
    if not ret:
        print("End of feed or lost connection.")
        break

    frame_count += 1

    # Run face detection every 5 frames to stay smooth
    if frame_count % 5 == 0:
        small = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        gray  = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        # Scale coords back up
        last_faces = [(x*2, y*2, w*2, h*2) for (x, y, w, h) in faces]

    # Draw green boxes from last detection
    for (x, y, w, h) in last_faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(frame, "PERSON", (x, y - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)

    # --- CCTV Overlay ---
    fh, fw = frame.shape[:2]
    now = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")

    # Semi-transparent black bar at bottom
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, fh - 50), (fw, fh), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)

    # Semi-transparent black bar at top
    overlay2 = frame.copy()
    cv2.rectangle(overlay2, (0, 0), (fw, 45), (0, 0, 0), -1)
    cv2.addWeighted(overlay2, 0.5, frame, 0.5, 0, frame)

    # Top bar: camera name + location
    cv2.putText(frame, CAMERA_NAME, (10, 18),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    cv2.putText(frame, LOCATION, (10, 38),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)

    # Bottom bar: timestamp + face count
    cv2.putText(frame, now, (10, fh - 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    cv2.putText(frame, f"PERSONS: {len(last_faces)}", (fw - 180, fh - 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)

    # Blinking REC dot (blinks every 30 frames)
    if (frame_count // 30) % 2 == 0:
        cv2.circle(frame, (fw - 30, 20), 8, (0, 0, 255), -1)
        cv2.putText(frame, "REC", (fw - 55, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

    cv2.imshow("CampusGuard", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print("Done.")
