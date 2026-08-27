"""Enlace serie con RS-485, reconexión y lectura de telemetría."""

import time
from typing import Callable, Optional

from .protocol import pack_frame, parse_telemetry

try:
    import serial
except ImportError:
    serial = None


class SerialLink:
    """Gestiona el adaptador serie sin bloquear el lazo de control."""

    def __init__(self, port: str, baudrate: int = 57600, retry_seconds: float = 2.0,
                 serial_factory: Optional[Callable[..., object]] = None) -> None:
        self.port = port
        self.baudrate = baudrate
        self.retry_seconds = retry_seconds
        self.serial_factory = serial_factory or (serial.Serial if serial else None)
        self.connection = None
        self.last_attempt = 0.0
        self.last_error = ""
        self.last_telemetry = None

    @property
    def connected(self) -> bool:
        """Devuelve el estado operativo del puerto."""
        return bool(self.connection and getattr(self.connection, "is_open", False))

    def open(self, force: bool = False) -> bool:
        """Abre o reabre el puerto respetando un intervalo de reintento."""
        if self.connected:
            return True
        now = time.monotonic()
        if not force and now - self.last_attempt < self.retry_seconds:
            return False
        self.last_attempt = now
        if self.serial_factory is None:
            self.last_error = "pyserial no está instalado"
            return False
        try:
            self.connection = self.serial_factory(self.port, self.baudrate, timeout=0, write_timeout=0.2)
            return True
        except Exception as exc:
            self.connection = None
            self.last_error = str(exc)
            return False

    def reconnect(self) -> bool:
        """Cierra el puerto actual y fuerza una reapertura."""
        self._close_connection()
        return self.open(force=True)

    def send(self, x: int, y: int, z: int, flags: int) -> bool:
        """Envía una trama válida o informa de la desconexión."""
        if not self.open() or not self.connected:
            return False
        try:
            self.connection.write(pack_frame(x, y, z, flags))
            return True
        except Exception as exc:
            self.last_error = str(exc)
            self._close_connection()
            return False

    def send_stop(self) -> bool:
        """Envía la trama neutral y desarmada."""
        return self.send(128, 128, 128, 0)

    def read_telemetry(self) -> Optional[dict]:
        """Lee como máximo las líneas disponibles sin bloquear."""
        if not self.connected:
            return None
        latest = None
        try:
            while self.connection.in_waiting:
                line = self.connection.readline()
                parsed = parse_telemetry(line)
                if parsed is not None:
                    latest = parsed
                    self.last_telemetry = parsed
            return latest
        except Exception as exc:
            self.last_error = str(exc)
            self._close_connection()
            return None

    def _close_connection(self) -> None:
        if self.connection is not None:
            try:
                self.connection.close()
            except Exception:
                pass
        self.connection = None

    def close(self) -> None:
        """Intenta detener motores antes de cerrar el adaptador."""
        if self.connected:
            self.send_stop()
        self._close_connection()
