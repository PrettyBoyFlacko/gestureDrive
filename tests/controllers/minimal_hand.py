import cv2
import mediapipe as mp
import numpy as np
import math

hands = None
cap = None
mp_drawing = None
mp_hands = None

def init():
    # MediaPipe setup
    global mp_hands
    mp_hands = mp.solutions.hands

    global mp_drawing
    mp_drawing = mp.solutions.drawing_utils

    global cap
    cap = cv2.VideoCapture(0)
  
    global hands 
    hands = mp_hands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7
    )
    
def joint_angle(a, b, c):
    ba = a - b
    bc = c - b

    ba /= np.linalg.norm(ba)
    bc /= np.linalg.norm(bc)

    cosang = np.clip(np.dot(ba, bc), -1.0, 1.0)
    angle = np.degrees(np.arccos(cosang))
    return np.clip((180 - angle) / 180.0, 0, 1)


def get_commands():
    commands = []
    if (hands is None or cap is None):
        init()
    
    success, frame = cap.read()
    if not success:
        print("Ignoring empty camera frame.")
        return []

      # Mirror image
    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape

    # Convert for MediaPipe
    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(image_rgb)

    center_x = w // 2
    center_y = h // 2

    command = "STOP"
    speed = "STOP"
    steering = "STRAIGHT"


    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            lm = hand_landmarks.landmark
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            thumb_tip = np.array([lm[4].x, lm[4].y, lm[4].z])
            thumb_mcp = np.array([lm[2].x, lm[2].y, lm[2].z])
            thumb_dir = thumb_tip - thumb_mcp
            thumb_dir /= np.linalg.norm(thumb_dir)

            FINGERS = {
                "index":  (5, 6, 7),
                "middle": (9, 10, 11),
                "ring":   (13, 14, 15),
                "pinky":  (17, 18, 19),
            }

            bends_avg = 0 

            for name, (mcp_i, pip_i, dip_i) in FINGERS.items():
                mcp = np.array([lm[mcp_i].x, lm[mcp_i].y, lm[mcp_i].z])
                pip = np.array([lm[pip_i].x, lm[pip_i].y, lm[pip_i].z])
                dip = np.array([lm[dip_i].x, lm[dip_i].y, lm[dip_i].z])

            angle = joint_angle(mcp, pip, dip)
            bends_avg += angle
            bends_avg /= 4

            thumb_threshold = 0.5
            if abs(thumb_dir[0]) > thumb_threshold:
                if thumb_dir[0] > 0:
                    steering = "LEFT"
                    commands.append("LEFT")
                else:
                    steering = "RIGHT"
                    commands.append("RIGHT")

            bend_threshold = 0.05
            if bends_avg > bend_threshold:
                command = "FORWARD"
                commands.append("UP")

    # Display text
    cv2.putText(
        frame, f"Command: {command}", (10, h - 50),
        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2
    )
    cv2.putText(
        frame, f"Speed: {speed}", (10, h - 20),
        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2
    )
    cv2.putText(
        frame, f"Steering: {steering}", (250, h - 20),
        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2
    )

    cv2.imshow("One-Hand RC Control", frame)
    return commands


