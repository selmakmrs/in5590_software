from detector import DETECTOR
import cv2

detector = DETECTOR()
detector.start_camera()

while True:
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
detector.stop_camera()


