from __future__ import annotations

STOP = "STOP"
CENTER = "CENTER"
FORWARD = "FORWARD"
REVERSE = "REVERSE"
LEFT = "LEFT"
RIGHT = "RIGHT"
FORWARD_LEFT = "FORWARD-LEFT"
FORWARD_RIGHT = "FORWARD-RIGHT"
REVERSE_LEFT = "REVERSE-LEFT"
REVERSE_RIGHT = "REVERSE-RIGHT"

COMMANDS = frozenset(
    {
        STOP,
        CENTER,
        FORWARD,
        REVERSE,
        LEFT,
        RIGHT,
        FORWARD_LEFT,
        FORWARD_RIGHT,
        REVERSE_LEFT,
        REVERSE_RIGHT,
    }
)

# Short aliases for serial bring-up and scripted tests.
ALIASES = {
    "S": STOP,
    "C": CENTER,
    "F": FORWARD,
    "B": REVERSE,
    "L": LEFT,
    "R": RIGHT,
    "FL": FORWARD_LEFT,
    "FR": FORWARD_RIGHT,
    "BL": REVERSE_LEFT,
    "BR": REVERSE_RIGHT,
    "FORWARD_LEFT": FORWARD_LEFT,
    "FORWARD_RIGHT": FORWARD_RIGHT,
    "REVERSE_LEFT": REVERSE_LEFT,
    "REVERSE_RIGHT": REVERSE_RIGHT,
}

DEFAULT_ESP32_IP = "192.168.4.1"
DEFAULT_UDP_PORT = 8888
HEARTBEAT_HZ = 10
COMMAND_TIMEOUT_MS = 300

# SoftAP — must match firmware/include/config.h
WIFI_SSID = "GestureDrive"
WIFI_PASSWORD = "GestureDrive1"

# PC-side joystick (fractions of frame, not pixels).
PINCH_FRACTION = 0.08
DEAD_ZONE_X_FRACTION = 0.10
DEAD_ZONE_Y_FRACTION = 0.15
COMMAND_DWELL_MS = 180
LOST_HAND_STOP_MS = 300


def normalize_command(raw: str) -> str | None:
    """Return a canonical command, or None if the string is not valid."""
    token = raw.strip().upper().replace(" ", "")
    if not token:
        return None
    if token in COMMANDS:
        return token
    return ALIASES.get(token)
