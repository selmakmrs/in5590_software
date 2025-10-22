from picamera2 import Picamera2
import cv2

# Initialize camera
picam2 = Picamera2()

# Configure for preview (640x480 is fast on Pi 3 B+)
config = picam2.create_preview_configuration(main={"size": (640, 480)})
picam2.configure(config)
picam2.start()

print("Press 'q' to quit.")

while True:
    frame = picam2.capture_array()
    cv2.imshow("Camera Preview", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

picam2.stop()
cv2.destroyAllWindows()
