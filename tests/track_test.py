import cv2

from body import BODY, HEAD_ID, BASE_ID, BODY_ID
from detector import DETECTOR

body = BODY()
detector = DETECTOR()
body.set_joint_mode()

def find_direction(face):
    x, y, fw, fh = face

    frame_center_x = 320 // 2
    face_center_x = x + fw // 2

    error_x_norm = (face_center_x - frame_center_x) / frame_center_x

    return error_x_norm
    
    


def move_servo(error):
    if error > 0: # Move right
        angle = -30
    else:
        angle = +30 # Move left

    for dxl_id in [HEAD_ID, BODY_ID, BASE_ID]:
        current_deg = body.tracked_positions[dxl_id]
        if current_deg + angle <= 0 or current_deg + angle >= 1023:
            continue
        body.move_position(dxl_id,current_deg+angle, 200)
        return True
    
    return False



    


body.start()
detector.start_camera()


try: 
    while True:
        frame = detector.get_frame()

        if frame is None:
            continue
        face = detector.detect_face(frame)

        if face is not None:
            detector.draw_face_box(frame,face)
            x, y, w, h = face
            face_size = w * h
            print("Face Size: ", face_size)
            if detector.is_face_centered(face):
                # center = detector.is_face_centered(face)
                emotion, emotion_prob = detector.detect_emotion(frame,face)
                
                detector.draw_emotion_text(frame,face,emotion,emotion_prob)

            else:

                error = find_direction(face)

                # Show debug text
                debug_text = f"err_x={error:.2f}"
                cv2.putText(frame, debug_text, (10, 240 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                
                move_servo(error)
                





        # cv2.imshow("Frame", frame)
        key = cv2.waitKey(1)
        if key == ord('q'):
            break

except KeyboardInterrupt:
    body.close()
    detector.stop_camera()


