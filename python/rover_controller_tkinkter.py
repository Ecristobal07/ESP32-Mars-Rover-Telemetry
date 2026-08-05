"""
ESP32 Rover Wireless Controller — Tkinter Version
--------------------------------------------------
Uses only Python's standard library. No pygame or pip install is required.

Controls:
    W / Up Arrow       Forward
    S / Down Arrow     Backward
    A / Left Arrow     Pivot left
    D / Right Arrow    Pivot right
    Space              Stop
    Esc or Q           Exit

Run:
    py rover_controller_tkinter.py
"""

from __future__ import annotations

import errno
import select
import socket
import time
import tkinter as tk
from tkinter import ttk


# ============================================================
# EDIT THESE SETTINGS
# ============================================================

ESP32_IP = "#######"
TCP_PORT = 5000

RECONNECT_DELAY_SECONDS = 2.0
CONNECT_TIMEOUT_SECONDS = 4.0
COMMAND_REPEAT_SECONDS = 0.15
UPDATE_INTERVAL_MS = 30


class RoverController:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("ESP32 Rover Controller")
        self.root.geometry("900x650")
        self.root.minsize(780, 560)

        self.sock: socket.socket | None = None
        self.connected = False
        self.connecting = False
        self.connect_started = 0.0
        self.next_reconnect_time = 0.0

        self.receive_buffer = ""
        self.telemetry_header: list[str] = []
        self.latest_telemetry: dict[str, str] = {}

        self.pressed_keys: set[str] = set()
        self.current_command = "STOP"
        self.last_sent_command = ""
        self.last_command_send_time = 0.0

        self.closing = False

        self.connection_var = tk.StringVar(value="DISCONNECTED")
        self.command_var = tk.StringVar(value="STOP")
        self.message_var = tk.StringVar(value="Starting...")
        self.raw_packet_var = tk.StringVar(value="Waiting for telemetry...")

        self.telemetry_vars = {
            "time_ms": tk.StringVar(value="--"),
            "temp_c": tk.StringVar(value="--"),
            "humidity_percent": tk.StringVar(value="--"),
            "light_raw": tk.StringVar(value="--"),
            "light_status": tk.StringVar(value="--"),
            "accel_x": tk.StringVar(value="--"),
            "accel_y": tk.StringVar(value="--"),
            "accel_z": tk.StringVar(value="--"),
            "gyro_x": tk.StringVar(value="--"),
            "gyro_y": tk.StringVar(value="--"),
            "gyro_z": tk.StringVar(value="--"),
            "rover_state": tk.StringVar(value="--"),
            "system_status": tk.StringVar(value="--"),
        }

        self._build_interface()
        self._bind_controls()

        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.after(100, self.update)

    # ========================================================
    # Interface
    # ========================================================

    def _build_interface(self) -> None:
        style = ttk.Style()
        style.configure("Title.TLabel", font=("Segoe UI", 20, "bold"))
        style.configure("Heading.TLabel", font=("Segoe UI", 13, "bold"))
        style.configure("Body.TLabel", font=("Consolas", 11))

        main = ttk.Frame(self.root, padding=18)
        main.pack(fill="both", expand=True)

        ttk.Label(
            main,
            text="ESP32 Rover Controller",
            style="Title.TLabel",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 14))

        status_frame = ttk.LabelFrame(main, text="Connection and control", padding=12)
        status_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 14))

        ttk.Label(status_frame, text="Network:", style="Heading.TLabel").grid(
            row=0, column=0, sticky="w", padx=(0, 10)
        )
        ttk.Label(status_frame, textvariable=self.connection_var).grid(
            row=0, column=1, sticky="w"
        )

        ttk.Label(status_frame, text="Command:", style="Heading.TLabel").grid(
            row=1, column=0, sticky="w", padx=(0, 10), pady=(8, 0)
        )
        ttk.Label(status_frame, textvariable=self.command_var).grid(
            row=1, column=1, sticky="w", pady=(8, 0)
        )

        ttk.Label(status_frame, textvariable=self.message_var).grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(10, 0)
        )

        controls = ttk.LabelFrame(main, text="Controls", padding=12)
        controls.grid(row=2, column=0, sticky="nsew", padx=(0, 8))

        control_text = (
            "W / Up Arrow      Forward\n"
            "S / Down Arrow    Backward\n"
            "A / Left Arrow    Pivot left\n"
            "D / Right Arrow   Pivot right\n"
            "Space             Stop\n"
            "Esc or Q          Exit\n\n"
            "Click this window before driving.\n"
            "Releasing the key sends STOP."
        )

        ttk.Label(
            controls,
            text=control_text,
            style="Body.TLabel",
            justify="left",
        ).pack(anchor="w")

        telemetry = ttk.LabelFrame(main, text="Latest telemetry", padding=12)
        telemetry.grid(row=2, column=1, sticky="nsew", padx=(8, 0))

        rows = [
            ("Time", "time_ms", "ms"),
            ("Temperature", "temp_c", "°C"),
            ("Humidity", "humidity_percent", "%"),
            ("Light", "light_raw", ""),
            ("Light status", "light_status", ""),
            ("Acceleration X", "accel_x", "m/s²"),
            ("Acceleration Y", "accel_y", "m/s²"),
            ("Acceleration Z", "accel_z", "m/s²"),
            ("Gyroscope X", "gyro_x", "rad/s"),
            ("Gyroscope Y", "gyro_y", "rad/s"),
            ("Gyroscope Z", "gyro_z", "rad/s"),
            ("Rover state", "rover_state", ""),
            ("System status", "system_status", ""),
        ]

        for row_number, (label, key, unit) in enumerate(rows):
            ttk.Label(telemetry, text=f"{label}:").grid(
                row=row_number,
                column=0,
                sticky="w",
                padx=(0, 12),
                pady=2,
            )

            value_frame = ttk.Frame(telemetry)
            value_frame.grid(row=row_number, column=1, sticky="w", pady=2)

            ttk.Label(
                value_frame,
                textvariable=self.telemetry_vars[key],
            ).pack(side="left")

            if unit:
                ttk.Label(value_frame, text=f" {unit}").pack(side="left")

        raw_frame = ttk.LabelFrame(main, text="Raw telemetry packet", padding=10)
        raw_frame.grid(
            row=3,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(14, 0),
        )

        ttk.Label(
            raw_frame,
            textvariable=self.raw_packet_var,
            wraplength=820,
            justify="left",
        ).pack(anchor="w")

        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(2, weight=1)

    # ========================================================
    # Keyboard controls
    # ========================================================

    def _bind_controls(self) -> None:
        self.root.bind_all("<KeyPress>", self.on_key_press)
        self.root.bind_all("<KeyRelease>", self.on_key_release)
        self.root.bind("<FocusOut>", self.on_focus_lost)

    @staticmethod
    def normalize_key(keysym: str) -> str:
        key = keysym.lower()

        aliases = {
            "up": "w",
            "down": "s",
            "left": "a",
            "right": "d",
            "space": "space",
        }

        return aliases.get(key, key)

    def on_key_press(self, event: tk.Event) -> None:
        key = self.normalize_key(event.keysym)

        if key in {"escape", "q"}:
            self.close()
            return

        if key in {"w", "a", "s", "d", "space"}:
            self.pressed_keys.add(key)

    def on_key_release(self, event: tk.Event) -> None:
        key = self.normalize_key(event.keysym)
        self.pressed_keys.discard(key)

    def on_focus_lost(self, _event: tk.Event) -> None:
        # Losing window focus should never leave the rover moving.
        self.pressed_keys.clear()
        self.current_command = "STOP"

        if self.connected:
            self.send_command("STOP", time.monotonic())

    def determine_command(self) -> str:
        if "space" in self.pressed_keys:
            return "STOP"

        commands = []

        if "w" in self.pressed_keys:
            commands.append("FORWARD")
        if "s" in self.pressed_keys:
            commands.append("BACKWARD")
        if "a" in self.pressed_keys:
            commands.append("LEFT")
        if "d" in self.pressed_keys:
            commands.append("RIGHT")

        # No key or conflicting keys means STOP.
        if len(commands) != 1:
            return "STOP"

        return commands[0]

    # ========================================================
    # Networking
    # ========================================================

    def begin_connection(self, now: float) -> None:
        self.disconnect("Connecting...", schedule_retry=False)

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(False)

        result = sock.connect_ex((ESP32_IP, TCP_PORT))

        allowed_results = {
            0,
            errno.EINPROGRESS,
            errno.EWOULDBLOCK,
            errno.EALREADY,
            10035,  # Windows WSAEWOULDBLOCK
            10036,  # Windows WSAEINPROGRESS
            10037,  # Windows WSAEALREADY
        }

        if result not in allowed_results:
            sock.close()
            self.message_var.set(f"Connection failed with error {result}")
            self.connection_var.set("DISCONNECTED")
            self.next_reconnect_time = now + RECONNECT_DELAY_SECONDS
            return

        self.sock = sock
        self.connect_started = now

        if result == 0:
            self.mark_connected()
        else:
            self.connecting = True
            self.connected = False
            self.connection_var.set("CONNECTING")
            self.message_var.set(f"Connecting to {ESP32_IP}:{TCP_PORT}...")

    def mark_connected(self) -> None:
        if self.sock is None:
            return

        self.connecting = False
        self.connected = True
        self.receive_buffer = ""
        self.telemetry_header = []
        self.last_sent_command = ""

        try:
            self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        except OSError:
            pass

        self.connection_var.set("CONNECTED")
        self.message_var.set(f"Connected to {ESP32_IP}:{TCP_PORT}")

    def check_connection_attempt(self, now: float) -> None:
        if self.sock is None:
            return

        if now - self.connect_started > CONNECT_TIMEOUT_SECONDS:
            self.disconnect("Connection attempt timed out")
            return

        try:
            _, writable, exceptional = select.select(
                [],
                [self.sock],
                [self.sock],
                0,
            )
        except OSError as error:
            self.disconnect(f"Connection check failed: {error}")
            return

        if exceptional:
            self.disconnect("Connection failed")
            return

        if writable:
            error_code = self.sock.getsockopt(
                socket.SOL_SOCKET,
                socket.SO_ERROR,
            )

            if error_code == 0:
                self.mark_connected()
            else:
                self.disconnect(f"Connection failed with error {error_code}")

    def receive_telemetry(self, now: float) -> None:
        if self.sock is None or not self.connected:
            return

        try:
            readable, _, exceptional = select.select(
                [self.sock],
                [],
                [self.sock],
                0,
            )
        except OSError as error:
            self.disconnect(f"Socket check failed: {error}")
            return

        if exceptional:
            self.disconnect("Socket error")
            return

        if not readable:
            return

        try:
            data = self.sock.recv(4096)
        except BlockingIOError:
            return
        except OSError as error:
            self.disconnect(f"Receive failed: {error}")
            return

        if not data:
            self.disconnect("Rover closed the connection")
            return

        self.receive_buffer += data.decode("utf-8", errors="replace")
        self.parse_telemetry_lines()

    def parse_telemetry_lines(self) -> None:
        while "\n" in self.receive_buffer:
            line, self.receive_buffer = self.receive_buffer.split("\n", 1)
            line = line.strip()

            if not line:
                continue

            self.raw_packet_var.set(line)

            if line.startswith("time_ms,"):
                self.telemetry_header = [
                    column.strip() for column in line.split(",")
                ]
                continue

            values = [value.strip() for value in line.split(",")]

            if (
                self.telemetry_header
                and len(values) == len(self.telemetry_header)
            ):
                self.latest_telemetry = dict(
                    zip(self.telemetry_header, values)
                )

                for key, variable in self.telemetry_vars.items():
                    variable.set(self.latest_telemetry.get(key, "--"))

    def send_command(self, command: str, now: float) -> bool:
        if self.sock is None or not self.connected:
            return False

        try:
            self.sock.sendall(f"{command}\n".encode("utf-8"))
            return True
        except BlockingIOError:
            return False
        except OSError as error:
            self.disconnect(f"Send failed: {error}")
            return False

    def disconnect(
        self,
        reason: str,
        schedule_retry: bool = True,
    ) -> None:
        if self.sock is not None:
            try:
                self.sock.close()
            except OSError:
                pass

        self.sock = None
        self.connected = False
        self.connecting = False
        self.pressed_keys.clear()
        self.current_command = "STOP"
        self.command_var.set("STOP")
        self.connection_var.set("DISCONNECTED")
        self.message_var.set(reason)

        if schedule_retry:
            self.next_reconnect_time = (
                time.monotonic() + RECONNECT_DELAY_SECONDS
            )

    # ========================================================
    # Main update loop
    # ========================================================

    def update(self) -> None:
        if self.closing:
            return

        now = time.monotonic()

        if self.sock is None:
            if now >= self.next_reconnect_time:
                self.begin_connection(now)

        elif self.connecting:
            self.check_connection_attempt(now)

        elif self.connected:
            self.receive_telemetry(now)

        self.current_command = (
            self.determine_command() if self.connected else "STOP"
        )
        self.command_var.set(self.current_command)

        if self.connected:
            changed = self.current_command != self.last_sent_command
            repeat_due = (
                now - self.last_command_send_time
                >= COMMAND_REPEAT_SECONDS
            )

            if changed or repeat_due:
                if self.send_command(self.current_command, now):
                    self.last_sent_command = self.current_command
                    self.last_command_send_time = now
        else:
            self.last_sent_command = ""

        self.root.after(UPDATE_INTERVAL_MS, self.update)

    def close(self) -> None:
        if self.closing:
            return

        self.closing = True
        self.pressed_keys.clear()

        if self.sock is not None and self.connected:
            try:
                self.sock.setblocking(True)
                self.sock.settimeout(0.3)
                self.sock.sendall(b"STOP\n")
            except OSError:
                pass

        if self.sock is not None:
            try:
                self.sock.close()
            except OSError:
                pass

        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    RoverController(root)
    root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
