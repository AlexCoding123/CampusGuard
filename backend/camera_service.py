import os
import threading
import cv2 as cv
from gemini_service import analyze_clip

CLIP_DURATION = 10
FPS = 30
FRAMES_PER_CLIP = FPS * CLIP_DURATION


def start_capture(source=0):
    """Continuously capture video, chunk into 10s clips, send each to Gemini."""
    cap = cv.VideoCapture(source)
    if not cap.isOpened():
        print("Cannot open camera")
        return

    os.makedirs("static/clips", exist_ok=True)

    clip_number = 0
    frame_count = 0
    writer = None

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Can't receive frame (stream end?). Exiting ...")
            break

        # Start a new clip writer every FRAMES_PER_CLIP frames
        if frame_count % FRAMES_PER_CLIP == 0:
            # Close the previous clip and send it to Gemini
            if writer is not None:
                writer.release()
                threading.Thread(target=send_to_gemini, args=(clip_path,)).start()

            clip_number += 1
            clip_path = f"static/clips/clip_{clip_number}.mp4"
            height, width = frame.shape[:2]
            fourcc = cv.VideoWriter_fourcc(*"mp4v")
            writer = cv.VideoWriter(clip_path, fourcc, FPS, (width, height))

        writer.write(frame)
        frame_count += 1

        if cv.waitKey(1) == ord('q'):
            break

    # Release the last clip
    if writer is not None:
        writer.release()
        threading.Thread(target=send_to_gemini, args=(clip_path,)).start()

    cap.release()


def send_to_gemini(clip_path):
    """Send a clip to Gemini for analysis. If fight detected, save alert."""
    print(f"Analyzing {clip_path}...")
    result = analyze_clip(clip_path)

    if result["is_fight"]:
        print(f"FIGHT DETECTED in {clip_path} (confidence: {result['confidence']})")
        # TODO: save to alerts repo for Flutter app to access
    else:
        print(f"No fight in {clip_path}, discarding.")
        os.remove(clip_path)


if __name__ == "__main__":
    start_capture()
