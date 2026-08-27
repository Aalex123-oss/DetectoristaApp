"""Punto de entrada de la estación de superficie del ROV."""

import argparse
import atexit
import signal
import time
from typing import Optional

try:
    import tkinter as tk
except ImportError:
    tk = None

from .config import Config, apply_arguments, parse_video_source
from .gui import ROVGui
from .joystick import Joystick
from .protocol import FLAG_ARMED, FLAG_EMERGENCY, FLAG_LIGHTS
from .serial_link import SerialLink
from .video import VideoCaptureThread


def frame_for_tick(axes: tuple, armed: bool, emergency: bool,
                   lights: bool) -> tuple:
    """Decide la trama segura que se transmite en un ciclo."""
    if emergency:
        return 128, 128, 128, FLAG_EMERGENCY
    if not armed:
        return 128, 128, 128, 0
    flags = FLAG_ARMED | (FLAG_LIGHTS if lights else 0)
    return axes[0], axes[1], axes[2], flags


class ROVApplication:
    """Coordina joystick, enlace, vídeo y la ventana de control."""

    def __init__(self, config: Config) -> None:
        self.config = config
        if tk is None:
            raise RuntimeError("Tkinter no está instalado en este sistema")
        self.root = tk.Tk()
        self.root.title("Detectorista ROV — superficie")
        self.link = SerialLink(config.serial_port, config.baudrate)
        self.joystick = Joystick(config.deadzone, config.invert_x, config.invert_y, config.invert_z)
        self.video = VideoCaptureThread(parse_video_source(config.video_source))
        self.armed = False
        self.lights = False
        self.emergency = False
        self.last_error = ""
        self.packet_count = 0
        self.rate_start = time.monotonic()
        self.packet_rate = 0.0
        self.last_axes = (128, 128, 128)
        self.last_telemetry_at = 0.0
        self.previous_link_connected = False
        self.previous_joystick_connected = False
        self.closing = False
        self.gui = ROVGui(self.root, self.arm, self.disarm, self.stop_emergency,
                          self.toggle_lights, self.reconnect)
        self.joystick.initialize()
        self.video.start()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.after(50, self.control_tick)

    def arm(self) -> None:
        """Arma los motores después de una acción explícita del operador."""
        self.armed = True
        self.emergency = False

    def disarm(self) -> None:
        """Desarma y envía inmediatamente una orden de parada."""
        self.armed = False
        self.link.send_stop()

    def stop_emergency(self) -> None:
        """Activa la parada de emergencia hasta que se rearme manualmente."""
        self.emergency = True
        self.armed = False
        self.link.send(128, 128, 128, 0x04)

    def toggle_lights(self) -> None:
        """Cambia el estado solicitado del relé de luces."""
        self.lights = not self.lights

    def reconnect(self) -> None:
        """Fuerza la reconexión del adaptador serie."""
        self.link.reconnect()

    def safety_stop(self, reason: str) -> None:
        """Aplica la detención local y avisa con un banner rojo."""
        self.armed = False
        self.last_error = reason
        self.link.send_stop()
        if not self.closing:
            self.gui.set_banner(f"PARADA DE SEGURIDAD: {reason}", safe=False)
            self.gui.update_status(
                "conectado" if self.link.connected else "desconectado",
                self.joystick.name,
                "conectado" if self.joystick.connected else "desconectado",
                self.last_axes, 0, self.packet_rate, self.link.last_telemetry, reason,
                self.link.last_telemetry is not None
                and time.monotonic() - self.last_telemetry_at > 2.0,
            )

    def control_tick(self) -> None:
        """Ejecuta un ciclo de control de 20 Hz y siempre reprograma el ciclo."""
        if self.closing:
            return
        tick_started = time.monotonic()
        try:
            axes = self.joystick.read_axes()
            buttons = self.joystick.read_buttons()
            if buttons.get("emergency"):
                self.stop_emergency()
            if not self.joystick.connected:
                raise ConnectionError("El joystick se desconectó")
            if not self.previous_joystick_connected:
                self.last_error = ""
                self.joystick.error = ""
            self.previous_joystick_connected = True
            sent_frame = frame_for_tick(
                axes, self.armed, self.emergency,
                self.lights or buttons.get("lights", False),
            )
            self.last_axes = sent_frame[:3]
            self.link.send(*sent_frame)
            link_connected = self.link.connected
            if link_connected and not self.previous_link_connected:
                self.link.last_error = ""
                self.last_error = ""
            self.previous_link_connected = link_connected
            self.packet_count += 1
            elapsed = time.monotonic() - self.rate_start
            if elapsed >= 1.0:
                self.packet_rate = self.packet_count / elapsed
                self.packet_count = 0
                self.rate_start = time.monotonic()
            telemetry = self.link.read_telemetry()
            if telemetry is not None:
                self.last_telemetry_at = time.monotonic()
            telemetry_stale = (
                self.link.last_telemetry is not None
                and time.monotonic() - self.last_telemetry_at > 2.0
            )
            self.gui.update_status(
                "conectado" if link_connected else "desconectado",
                self.joystick.name, "conectado" if self.joystick.connected else "desconectado",
                self.last_axes, sent_frame[3], self.packet_rate,
                self.link.last_telemetry, self.last_error, telemetry_stale,
            )
            self.gui.show_frame(self.video.latest())
            if self.emergency:
                self.gui.set_banner(
                    "PARADA DE EMERGENCIA — pulse ARMAR para rearmar", safe=False
                )
            elif self.armed:
                self.gui.set_banner("Control activo", safe=True)
            else:
                self.gui.set_banner("Sistema desarmado", safe=False)
        except Exception as exc:
            self.safety_stop(str(exc))
        finally:
            if not self.closing:
                period_ms = 1000.0 / self.config.send_rate
                work_ms = (time.monotonic() - tick_started) * 1000.0
                self.root.after(max(1, int(period_ms - work_ms)), self.control_tick)

    def close(self) -> None:
        """Detiene el ROV y libera todos los recursos antes de cerrar."""
        if self.closing:
            return
        self.closing = True
        self.link.send_stop()
        self.video.stop()
        self.joystick.close()
        self.link.close()
        self.root.destroy()


def build_parser() -> argparse.ArgumentParser:
    """Construye las opciones de ejecución."""
    parser = argparse.ArgumentParser(description="Estación de superficie para ROV")
    parser.add_argument("--port", dest="serial_port", help="Puerto del adaptador RS-485")
    parser.add_argument("--video", dest="video_source", help="Índice USB o URL RTSP")
    parser.add_argument("--baud", dest="baudrate", type=int, help="Velocidad serie")
    parser.add_argument("--no-video", action="store_true", help="Desactiva la captura de vídeo")
    parser.add_argument("--config", help="Ruta del archivo JSON de configuración")
    return parser


def main(argv: Optional[list] = None) -> int:
    """Carga configuración y arranca Tkinter."""
    args = build_parser().parse_args(argv)
    config = Config.load(args.config)
    config = apply_arguments(config, args)
    try:
        application = ROVApplication(config)
        atexit.register(application.link.send_stop)
        signal.signal(signal.SIGINT, lambda _signum, _frame: application.close())
        application.root.mainloop()
    except Exception as exc:
        print(f"No se pudo iniciar la interfaz gráfica: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
