import threading
import cv2
import time

from detector import DETECTOR
from oled import OLED


detector = DETECTOR()
detector.start_camera()
oled = OLED()


running = True
emotion = ""
EMOTIONS = ["happy","sad","angry", "confused"]



def _camera_loop():
    while running:
        frame = detector.get_frame()

        if frame is None:
            break
        face = detector.detect_face(frame)

        if face is not None and detector.is_face_centered(face):
            # center = detector.is_face_centered(face)
            emotion, emotion_prob = detector.detect_emotion(frame,face)
            
            detector.draw_face_box(frame,face)
            detector.draw_emotion_text(frame,face,emotion,emotion_prob)

        key = cv2.waitKey(1)
        if key == ord('q'):
            break

        cv2.imshow("Frame", frame)

def _oled_loop():
    while running:
        oled.update()

        if emotion in EMOTIONS:
            oled.run_emotion(emotion)


        time.sleep(0.05)


camera_thread = threading.Thread(target=_camera_loop)
oled_thread = threading.Thread(target=_oled_loop)

camera_thread.start()
oled_thread.start()


        