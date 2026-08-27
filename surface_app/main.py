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
from .joystick import Joystick, flags_from_buttons
from .serial_link import SerialLink
from .video import VideoCaptureThread


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
        self.gui.set_banner(f"PARADA DE SEGURIDAD: {reason}", safe=False)

    def control_tick(self) -> None:
        """Ejecuta un ciclo de control de 20 Hz y siempre reprograma el ciclo."""
        try:
            axes = self.joystick.read_axes()
            self.last_axes = axes
            buttons = self.joystick.read_buttons()
            if buttons.get("emergency"):
                self.stop_emergency()
            flags = flags_from_buttons(buttons, self.armed, self.emergency, self.lights)
            if self.emergency:
                flags = 0x04
            if not self.joystick.connected:
                raise ConnectionError("El joystick se desconectó")
            self.link.send(*axes, flags)
            self.packet_count += 1
            elapsed = time.monotonic() - self.rate_start
            if elapsed >= 1.0:
                self.packet_rate = self.packet_count / elapsed
                self.packet_count = 0
                self.rate_start = time.monotonic()
            telemetry = self.link.read_telemetry()
            self.gui.update_status(
                "conectado" if self.link.connected else "desconectado",
                self.joystick.name, "conectado" if self.joystick.connected else "desconectado",
                axes, flags, self.packet_rate, telemetry, self.last_error,
            )
            self.gui.show_frame(self.video.latest())
            if not self.emergency:
                self.gui.set_banner("Control activo" if self.armed else "Sistema desarmado", safe=self.armed)
            self.last_error = self.link.last_error
        except Exception as exc:
            self.safety_stop(str(exc))
        finally:
            self.root.after(max(1, int(1000 / self.config.send_rate)), self.control_tick)

    def close(self) -> None:
        """Detiene el ROV y libera todos los recursos antes de cerrar."""
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
