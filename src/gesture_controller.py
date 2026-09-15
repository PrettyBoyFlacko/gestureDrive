import cv2
import mediapipe as mp
import math
import udp_server as udp

# MediaPipe setup
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

client_ip = input("Enter client IP address: ")
client_port = int(input("Enter port number: "))
udp.init(client_ip, client_port)

with mp_hands.Hands(
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
) as hands:

    prev_command = ""

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            print("Ignoring empty camera frame.")
            continue

        # Mirror image
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        # Convert for MediaPipe
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(image_rgb)

        center_x = w // 2
        center_y = h // 2

        # Dead zones
        dead_zone_x = 60
        dead_zone_y = 80

        # Draw guide lines
        cv2.line(frame, (center_x - dead_zone_x, 0), (center_x - dead_zone_x, h), (255, 255, 255), 1)
        cv2.line(frame, (center_x + dead_zone_x, 0), (center_x + dead_zone_x, h), (255, 255, 255), 1)
        cv2.line(frame, (0, center_y - dead_zone_y), (w, center_y - dead_zone_y), (255, 255, 255), 1)
        cv2.line(frame, (0, center_y + dead_zone_y), (w, center_y + dead_zone_y), (255, 255, 255), 1)

        command = "STOP"
        speed = "STOP"
        steering = "STRAIGHT"

        detected_hands = []

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                thumb_tip = hand_landmarks.landmark[4]
                index_tip = hand_landmarks.landmark[8]
                wrist = hand_landmarks.landmark[0]

                thumb_coords = (int(thumb_tip.x * w), int(thumb_tip.y * h))
                index_coords = (int(index_tip.x * w), int(index_tip.y * h))
                wrist_coords = (int(wrist.x * w), int(wrist.y * h))

                # Draw landmarks
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                # Draw fingertip markers
                cv2.circle(frame, thumb_coords, 8, (0, 255, 0), -1)
                cv2.circle(frame, index_coords, 8, (0, 0, 255), -1)

                # Pinch distance
                distance = math.sqrt(
                    (thumb_coords[0] - index_coords[0]) ** 2 +
                    (thumb_coords[1] - index_coords[1]) ** 2
                )

                detected_hands.append({
                    "wrist_x": wrist_coords[0],
                    "thumb_coords": thumb_coords,
                    "index_coords": index_coords,
                    "pinch_distance": distance
                })

        # Need both hands: left-side hand = pinch, right-side hand = control
        if len(detected_hands) >= 2:
            # Sort by x-position on the screen
            detected_hands.sort(key=lambda hand: hand["wrist_x"])

            pinch_hand = detected_hands[0]     # left side of screen
            control_hand = detected_hands[-1]  # right side of screen

            pinch_threshold = 40
            pinch_enabled = pinch_hand["pinch_distance"] < pinch_threshold

            # Draw labels
            cv2.putText(
                frame, f"LEFT HAND = PINCH ({int(pinch_hand['pinch_distance'])})",
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2
            )
            cv2.putText(
                frame, "RIGHT HAND = CONTROL",
                (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2
            )

            x, y = control_hand["index_coords"]

            # Highlight control fingertip
            cv2.circle(frame, (x, y), 12, (255, 255, 255), 3)

            if pinch_enabled:
                # Speed from up/down
                if y < center_y - dead_zone_y:
                    speed = "FORWARD"
                elif y > center_y + dead_zone_y:
                    speed = "REVERSE"
                else:
                    speed = "STOP"

                # Steering from left/right
                if x <= center_x - dead_zone_x:
                    steering = "LEFT"
                elif x >= center_x + dead_zone_x:
                    steering = "RIGHT"
                else:
                    steering = "STRAIGHT"

                # Combine command
                if speed == "STOP" and steering == "STRAIGHT":
                    command = "CENTER"
                elif speed == "STOP":
                    command = steering
                elif steering == "STRAIGHT":
                    command = speed
                else:
                    command = f"{speed}-{steering}"
            else:
                command = "STOP"
                speed = "STOP"
                steering = "STRAIGHT"

        # Only print when command changes
        if command != prev_command:
            print(f"Command: {command} | Speed: {speed} | Steering: {steering}")
            udp.send(f"Command: {command} | Speed: {speed} | Steering: {steering}".encode("utf-8"))
            prev_command = command

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

        cv2.imshow("Two-Hand RC Control", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
