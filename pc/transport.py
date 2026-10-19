from __future__ import annotations

import socket
import time
from typing import Protocol

from protocol import HEARTBEAT_HZ, STOP, normalize_command


class CommandSink(Protocol):
    def send(self, command: str) -> None: ...

    def close(self) -> None: ...


class NullSink:
    def send(self, command: str) -> None:
        return

    def close(self) -> None:
        return


class UdpSink:
    def __init__(self, host: str, port: int) -> None:
        self._addr = (host, port)
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setblocking(False)

    def send(self, command: str) -> None:
        payload = f"{command}\n".encode("ascii")
        try:
            self._sock.sendto(payload, self._addr)
        except OSError:
            pass

    def close(self) -> None:
        self._sock.close()


class SerialSink:
    def __init__(self, port: str, baud: int = 115200) -> None:
        try:
            import serial  # type: ignore
        except ImportError as exc:
            raise SystemExit(
                "pyserial is required for --serial. pip install pyserial"
            ) from exc
        self._ser = serial.Serial(port, baud, timeout=0.05)

    def send(self, command: str) -> None:
        self._ser.write(f"{command}\n".encode("ascii"))

    def close(self) -> None:
        self._ser.close()


class HeartbeatSender:
    """Send on change, plus a periodic repeat so a dropped packet cannot leave motors on."""

    def __init__(self, sink: CommandSink, hz: float = HEARTBEAT_HZ) -> None:
        self._sink = sink
        self._period = 1.0 / hz
        self._last_sent = STOP
        self._last_time = 0.0

    def update(self, command: str, force: bool = False) -> None:
        now = time.monotonic()
        if force or command != self._last_sent or (now - self._last_time) >= self._period:
            self._sink.send(command)
            self._last_sent = command
            self._last_time = now

    def close(self) -> None:
        self._sink.send(STOP)
        self._sink.close()


def parse_and_send_line(sink: CommandSink, line: str) -> str | None:
    command = normalize_command(line)
    if command is None:
        return None
    sink.send(command)
    return command
