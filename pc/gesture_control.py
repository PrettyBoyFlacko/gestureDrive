from __future__ import annotations

import argparse
import math
import sys
import time
from pathlib import Path

import cv2
import mediapipe as mp

sys.path.insert(0, str(Path(__file__).resolve().parent))

from protocol import (  
    CENTER,
    DEAD_ZONE_X_FRACTION,
    DEAD_ZONE_Y_FRACTION,
    DEFAULT_ESP32_IP,
    DEFAULT_UDP_PORT,
    FORWARD,
    LEFT,
    PINCH_FRACTION,
    REVERSE,
    RIGHT,
    STOP,
)
from transport import HeartbeatSender, NullSink, SerialSink, UdpSink  # noqa: E402

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils


def combine_command(speed: str, steering: str, armed: bool) -> str:
    if not armed:
        return STOP
    if speed == STOP and steering == "STRAIGHT":
        return CENTER
    if speed == STOP:
        return steering
    if steering == "STRAIGHT":
        return speed
    return f"{speed}-{steering}"


def _keyboard_override(keys: set[str]) -> str | None:
    if "space" in keys:
        return STOP
    forward = "w" in keys
    reverse = "s" in keys
    left = "a" in keys
    right = "d" in keys
    if not (forward or reverse or left or right):
        return None
    if forward and reverse:
        return STOP
    speed = FORWARD if forward else REVERSE if reverse else STOP
    steering = LEFT if left and not right else RIGHT if right and not left else "STRAIGHT"
    if speed == STOP and steering == "STRAIGHT":
        return None
    return combine_command(speed, steering, armed=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GestureDrive laptop vision + command sender")
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--udp", nargs="?", const=DEFAULT_ESP32_IP, default=None,
                        help="Send commands over WiFi UDP (default host 192.168.4.1)")
    parser.add_argument("--port", type=int, default=DEFAULT_UDP_PORT)
    parser.add_argument("--serial", metavar="COM", help="Send commands over USB serial instead of UDP")
    parser.add_argument("--no-mirror", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    mirror = not args.no_mirror

    if args.serial:
        sink = SerialSink(args.serial)
        transport_name = f"serial {args.serial}"
    elif args.udp is not None:
        sink = UdpSink(args.udp, args.port)
        transport_name = f"udp {args.udp}:{args.port}"
    else:
        sink = NullSink()
        transport_name = "print-only"

    sender = HeartbeatSender(sink)
    keyboard_mode = False
    lost_since: float | None = None
    key_latch: dict[str, float] = {}
    prev_print = ""
    fps_t = time.monotonic()
    fps = 0.0
    frames = 0

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        raise SystemExit(f"Could not open camera {args.camera}")

    print("q quit | k toggle keyboard WASD | space stop")
    print(f"transport: {transport_name}")

    try:
        with mp_hands.Hands(
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7,
        ) as hands:
            while cap.isOpened():
                ok, frame = cap.read()
                if not ok:
                    continue
                if mirror:
                    frame = cv2.flip(frame, 1)
                h, w, _ = frame.shape
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = hands.process(rgb)

                center_x = w // 2
                center_y = h // 2
                dead_x = int(DEAD_ZONE_X_FRACTION * w)
                dead_y = int(DEAD_ZONE_Y_FRACTION * h)
                pinch_threshold = PINCH_FRACTION * w

                cv2.line(frame, (center_x - dead_x, 0), (center_x - dead_x, h), (255, 255, 255), 1)
                cv2.line(frame, (center_x + dead_x, 0), (center_x + dead_x, h), (255, 255, 255), 1)
                cv2.line(frame, (0, center_y - dead_y), (w, center_y - dead_y), (255, 255, 255), 1)
                cv2.line(frame, (0, center_y + dead_y), (w, center_y + dead_y), (255, 255, 255), 1)

                command = STOP
                speed = STOP
                steering = "STRAIGHT"
                armed = False
                two_hands = False

                detected: list[dict] = []
                if results.multi_hand_landmarks:
                    handedness_list = results.multi_handedness or []
                    for idx, landmarks in enumerate(results.multi_hand_landmarks):
                        thumb = landmarks.landmark[4]
                        index = landmarks.landmark[8]
                        wrist = landmarks.landmark[0]
                        thumb_px = (int(thumb.x * w), int(thumb.y * h))
                        index_px = (int(index.x * w), int(index.y * h))
                        wrist_px = (int(wrist.x * w), int(wrist.y * h))
                        distance = math.hypot(
                            thumb_px[0] - index_px[0], thumb_px[1] - index_px[1]
                        )
                        label = "Unknown"
                        if idx < len(handedness_list):
                            label = handedness_list[idx].classification[0].label
                        detected.append(
                            {
                                "label": label,
                                "wrist_x": wrist_px[0],
                                "index": index_px,
                                "pinch": distance,
                                "landmarks": landmarks,
                            }
                        )
                        mp_drawing.draw_landmarks(frame, landmarks, mp_hands.HAND_CONNECTIONS)
                        cv2.circle(frame, thumb_px, 8, (0, 255, 0), -1)
                        cv2.circle(frame, index_px, 8, (0, 0, 255), -1)

                pinch_hand = None
                control_hand = None
                if len(detected) >= 2:
                    two_hands = True
                    lefts = [hnd for hnd in detected if hnd["label"] == "Left"]
                    rights = [hnd for hnd in detected if hnd["label"] == "Right"]
                    if lefts and rights:
                        pinch_hand = lefts[0]
                        control_hand = rights[0]
                    else:
                        ordered = sorted(detected, key=lambda hnd: hnd["wrist_x"])
                        pinch_hand = ordered[0]
                        control_hand = ordered[-1]

                now = time.monotonic()
                if two_hands and pinch_hand and control_hand:
                    lost_since = None
                    armed = pinch_hand["pinch"] < pinch_threshold
                    cv2.putText(
                        frame,
                        f"LEFT PINCH {int(pinch_hand['pinch'])} / {int(pinch_threshold)}",
                        (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 255),
                        2,
                    )
                    cv2.putText(
                        frame,
                        "RIGHT INDEX = JOYSTICK",
                        (10, 55),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (255, 255, 0),
                        2,
                    )
                    x, y = control_hand["index"]
                    cv2.circle(frame, (x, y), 12, (255, 255, 255), 3)
                    if armed:
                        if y < center_y - dead_y:
                            speed = FORWARD
                        elif y > center_y + dead_y:
                            speed = REVERSE
                        else:
                            speed = STOP
                        if x <= center_x - dead_x:
                            steering = LEFT
                        elif x >= center_x + dead_x:
                            steering = RIGHT
                        else:
                            steering = "STRAIGHT"
                    command = combine_command(speed, steering, armed)
                else:
                    if lost_since is None:
                        lost_since = now
                    if (now - lost_since) * 1000 >= 0:
                        command = STOP

                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break
                if key == ord("k"):
                    keyboard_mode = not keyboard_mode
                    key_latch.clear()
                keymap = {ord("w"): "w", ord("a"): "a", ord("s"): "s", ord("d"): "d"}
                if key in keymap:
                    key_latch[keymap[key]] = now + 0.4
                if key == ord(" "):
                    key_latch = {"space": now + 0.4}
                held_keys = {name for name, until in key_latch.items() if until > now}
                kb_cmd = None
                if keyboard_mode:
                    if "space" in held_keys:
                        kb_cmd = STOP
                    elif held_keys & {"w", "a", "s", "d"}:
                        kb_cmd = _keyboard_override(held_keys)
                    else:
                        kb_cmd = CENTER

                raw_command = kb_cmd if keyboard_mode else command
            
                if not keyboard_mode and not two_hands:
                    raw_command = STOP

                sender.update(raw_command)

                frames += 1
                if now - fps_t >= 0.5:
                    fps = frames / (now - fps_t)
                    fps_t = now
                    frames = 0

                if raw_command != prev_print:
                    print(f"Command: {raw_command} | Speed: {speed} | Steering: {steering} | armed={armed}")
                    prev_print = raw_command

                cv2.putText(
                    frame, f"Command: {raw_command}", (10, h - 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2,
                )
                cv2.putText(
                    frame, f"Speed: {speed}  Steer: {steering}", (10, h - 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2,
                )
                mode = "KEYBOARD" if keyboard_mode else "GESTURE"
                arm_txt = "ARMED" if armed else "DISARMED"
                cv2.putText(
                    frame, f"{mode} {arm_txt}  {transport_name}  {fps:.0f} fps",
                    (10, h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1,
                )
                cv2.imshow("GestureDrive", frame)
    finally:
        sender.close()
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
