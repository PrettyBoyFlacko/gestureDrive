"""Scripted command sender for USB serial or WiFi UDP bring-up (no camera).

Examples:
    python send_commands.py --udp --script demo
    python send_commands.py --serial COM5 --once FORWARD
    python send_commands.py --udp --impossible-servo
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from protocol import (  # noqa: E402
    CENTER,
    COMMANDS,
    DEFAULT_ESP32_IP,
    DEFAULT_UDP_PORT,
    FORWARD,
    FORWARD_LEFT,
    FORWARD_RIGHT,
    LEFT,
    REVERSE,
    REVERSE_LEFT,
    REVERSE_RIGHT,
    RIGHT,
    STOP,
    normalize_command,
)
from transport import HeartbeatSender, SerialSink, UdpSink  # noqa: E402

DEMO_PATH = [
    (FORWARD, 2.0),
    (FORWARD_LEFT, 1.5),
    (FORWARD, 1.5),
    (FORWARD_RIGHT, 1.5),
    (CENTER, 0.8),
    (REVERSE, 1.5),
    (REVERSE_LEFT, 1.2),
    (REVERSE_RIGHT, 1.2),
    (LEFT, 1.0),
    (RIGHT, 1.0),
    (STOP, 0.5),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send GestureDrive commands without vision")
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("--udp", nargs="?", const=DEFAULT_ESP32_IP)
    group.add_argument("--serial", metavar="COM")
    parser.add_argument("--port", type=int, default=DEFAULT_UDP_PORT)
    parser.add_argument("--once", help="Send a single command then STOP")
    parser.add_argument("--script", choices=("demo",), help="Run the marked-path command sequence")
    parser.add_argument(
        "--impossible-servo",
        action="store_true",
        help="Send SERVO 180; firmware must clamp (vehicle test from the proposal)",
    )
    parser.add_argument("--list", action="store_true", help="Print the command set and exit")
    return parser.parse_args()


def make_sink(args: argparse.Namespace):
    if args.serial:
        return SerialSink(args.serial)
    return UdpSink(args.udp, args.port)


def hold(sender: HeartbeatSender, command: str, seconds: float) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        sender.update(command)
        time.sleep(0.05)


def main() -> None:
    args = parse_args()
    if args.list:
        print("Canonical commands:")
        for cmd in sorted(COMMANDS):
            print(f"  {cmd}")
        return
    if not args.serial and args.udp is None:
        raise SystemExit("Specify --udp or --serial (or --list)")

    sink = make_sink(args)
    sender = HeartbeatSender(sink)
    try:
        if args.impossible_servo:
            print("Sending SERVO 180 (firmware must clamp, then STOP)")
            sink.send("SERVO 180")
            time.sleep(1.0)
            hold(sender, STOP, 0.3)
            return
        if args.once:
            cmd = normalize_command(args.once)
            if cmd is None:
                raise SystemExit(f"Unknown command: {args.once}")
            print(f"Sending {cmd}")
            hold(sender, cmd, 1.5)
            hold(sender, STOP, 0.3)
            return
        print("Running demo path script (straight, left, right, reverse)")
        for cmd, dur in DEMO_PATH:
            print(f"  {cmd} {dur}s")
            hold(sender, cmd, dur)
        hold(sender, STOP, 0.3)
    except KeyboardInterrupt:
        pass
    finally:
        sender.close()
        print("Stopped.")


if __name__ == "__main__":
    main()
