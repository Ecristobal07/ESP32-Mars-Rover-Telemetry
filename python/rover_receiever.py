import msvcrt
import select
import socket
import time

ESP32_IP = "########"  # Replace with your ESP32 IP
PORT = 5000

CONNECT_TIMEOUT = 3.0
NO_DATA_TIMEOUT = 7.0
RECONNECT_DELAY = 2.0
POLL_INTERVAL = 0.25


def quit_requested() -> bool:
    """Return True when the user presses Q."""
    if msvcrt.kbhit():
        key = msvcrt.getwch().lower()
        return key == "q"

    return False


def wait_with_quit(seconds: float) -> bool:
    """Wait while still allowing Q to stop the program."""
    deadline = time.monotonic() + seconds

    while time.monotonic() < deadline:
        if quit_requested():
            return True

        time.sleep(0.1)

    return False


def connect_to_rover() -> socket.socket:
    """Create a new TCP connection to the ESP32."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(CONNECT_TIMEOUT)

    try:
        sock.connect((ESP32_IP, PORT))
    except Exception:
        sock.close()
        raise

    # Prevent recv() from blocking indefinitely.
    sock.setblocking(False)
    return sock


def receive_telemetry(sock: socket.socket) -> bool:
    """
    Receive telemetry.

    Returns True when Q was pressed.
    Raises an exception when the rover disconnects.
    """
    buffer = ""
    last_data_time = time.monotonic()

    while True:
        if quit_requested():
            return True

        readable, _, exceptional = select.select(
            [sock],
            [],
            [sock],
            POLL_INTERVAL
        )

        if exceptional:
            raise ConnectionError("Socket entered an error state.")

        if readable:
            data = sock.recv(4096)

            # An empty result means the other side closed the socket.
            if not data:
                raise ConnectionError("Rover closed the TCP connection.")

            last_data_time = time.monotonic()
            buffer += data.decode("utf-8", errors="replace")

            # TCP may give us several lines or part of one line.
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()

                if line:
                    print(line)

        if time.monotonic() - last_data_time > NO_DATA_TIMEOUT:
            raise TimeoutError(
                f"No telemetry received for {NO_DATA_TIMEOUT:.0f} seconds."
            )


def main() -> None:
    print("ROVER RECEIVER V3")
    print("Press Q at any time to exit.")
    print()

    while True:
        if quit_requested():
            break

        sock = None

        try:
            print(f"Connecting to {ESP32_IP}:{PORT}...")
            sock = connect_to_rover()

            print("Connected to rover.")
            print()

            if receive_telemetry(sock):
                break

        except (ConnectionError, TimeoutError, OSError) as error:
            print()
            print(f"Connection lost: {error}")

        finally:
            if sock is not None:
                sock.close()

        print(f"Retrying in {RECONNECT_DELAY:.0f} seconds...")
        print("Press Q to exit.")

        if wait_with_quit(RECONNECT_DELAY):
            break

    print("\nReceiver stopped.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nReceiver stopped with Ctrl+C.")
