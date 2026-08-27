"""Interfaz Tkinter para vídeo, control y telemetría del ROV."""

from typing import Any, Callable, Optional

try:
    import tkinter as tk
    from tkinter import ttk
except ImportError:
    tk = None
    ttk = None

import cv2
from PIL import Image

try:
    from PIL import ImageTk
except ImportError:
    ImageTk = None


class ROVGui:
    """Ventana principal, deliberadamente sin crear una ventana al importar."""

    def __init__(self, root: Any, on_arm: Callable[[], None],
                 on_disarm: Callable[[], None], on_emergency: Callable[[], None],
                 on_lights: Callable[[], None], on_reconnect: Callable[[], None]) -> None:
        if tk is None or ttk is None:
            raise RuntimeError("Tkinter no está instalado en este sistema")
        self.root = root
        self.callbacks = {
            "arm": on_arm, "disarm": on_disarm, "emergency": on_emergency,
            "lights": on_lights, "reconnect": on_reconnect,
        }
        self.video_label = ttk.Label(root, text="Sin vídeo", anchor="center")
        self.video_label.pack(fill="both", expand=True, padx=8, pady=8)
        controls = ttk.Frame(root)
        controls.pack(fill="x", padx=8)
        ttk.Button(controls, text="ARMAR", command=on_arm).pack(side="left", padx=2)
        ttk.Button(controls, text="DESARMAR", command=on_disarm).pack(side="left", padx=2)
        ttk.Button(controls, text="PARADA DE EMERGENCIA", command=on_emergency).pack(side="left", padx=2)
        ttk.Button(controls, text="LUCES", command=on_lights).pack(side="left", padx=2)
        ttk.Button(controls, text="RECONECTAR", command=on_reconnect).pack(side="left", padx=2)
        self.banner = tk.Label(root, text="Sistema detenido", bg="#9b1c1c", fg="white")
        self.banner.pack(fill="x", padx=8, pady=4)
        self.status = tk.StringVar(value="")
        ttk.Label(root, textvariable=self.status, justify="left").pack(fill="x", padx=8)
        self.last_image = None

    def set_banner(self, text: str, safe: bool = False) -> None:
        """Actualiza el aviso visible con color seguro o de error."""
        self.banner.configure(text=text, bg="#217a3c" if safe else "#9b1c1c")

    def update_status(self, serial_state: str, joystick_name: str, joystick_state: str,
                      axes: tuple, flags: int, packet_rate: float,
                      telemetry: Optional[dict], error: str = "") -> None:
        """Muestra todos los estados requeridos por el operador."""
        telemetry_text = "Sin telemetría" if not telemetry else "; ".join(
            f"{key}={value}" for key, value in telemetry.items() if key != "tipo"
        )
        self.status.set(
            f"Serie: {serial_state} | Joystick: {joystick_name} ({joystick_state})\n"
            f"X={axes[0]} Y={axes[1]} Z={axes[2]} | flags=0x{flags:02X} | "
            f"paquetes={packet_rate:.1f} Hz\nTelemetría subsea: {telemetry_text}\n"
            f"Último error: {error or 'ninguno'}"
        )

    def show_frame(self, frame: Any) -> None:
        """Convierte un fotograma BGR de OpenCV para mostrarlo en Tk."""
        if frame is None or ImageTk is None:
            return
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(rgb)
        image.thumbnail((960, 540))
        self.last_image = ImageTk.PhotoImage(image)
        self.video_label.configure(image=self.last_image, text="")
