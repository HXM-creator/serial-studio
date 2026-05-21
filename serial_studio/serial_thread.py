"""Background serial reader thread."""

from PyQt6.QtCore import QThread, pyqtSignal
from serial import Serial, SerialException
from serial.tools import list_ports


def available_ports() -> list[str]:
    return [p.device for p in list_ports.comports()]


class SerialReader(QThread):
    data_received = pyqtSignal(str)     # one line of text
    connection_error = pyqtSignal(str)  # error message
    connected_signal = pyqtSignal()     # successful open
    disconnected_signal = pyqtSignal()  # connection lost

    def __init__(self, parent=None):
        super().__init__(parent)
        self._port: str = ""
        self._baud: int = 115200
        self._running = False
        self._serial: Serial | None = None

    def configure(self, port: str, baud: int):
        self._port = port
        self._baud = baud

    def open(self) -> str | None:
        """Open the serial port. Returns None on success, error string on failure."""
        try:
            self._serial = Serial(self._port, self._baud, timeout=0.05)
            self._running = True
            self.connected_signal.emit()
            self.start()
            return None
        except SerialException as e:
            return str(e)

    def close(self):
        self._running = False
        if self._serial and self._serial.is_open:
            try:
                self._serial.close()
            except SerialException:
                pass
        self._serial = None
        self.disconnected_signal.emit()

    def run(self):
        buf = b""
        while self._running and self._serial and self._serial.is_open:
            try:
                data = self._serial.read(256)
                if data:
                    buf += data
                    while b"\n" in buf:
                        line, buf = buf.split(b"\n", 1)
                        try:
                            text = line.decode("utf-8", errors="replace").strip("\r ")
                            if text:
                                self.data_received.emit(text)
                        except Exception:
                            pass
                else:
                    self.msleep(10)
            except SerialException:
                self.connection_error.emit("Connection lost")
                self.close()
                break
