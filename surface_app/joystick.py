"""Lectura segura de joystick pygame y normalización de ejes."""

from typing import Any, Dict, Optional, Tuple

from .protocol import FLAG_ARMED, FLAG_EMERGENCY, FLAG_LIGHTS

try:
    import pygame
except ImportError:
    pygame = None


class Joystick:
    """Envoltorio que tolera ausencia, conexión y desconexión del mando."""

    def __init__(self, deadzone: float = 0.10, invert_x: bool = False,
                 invert_y: bool = False, invert_z: bool = False) -> None:
        self.deadzone = max(0.0, min(0.49, deadzone))
        self.inversions = (invert_x, invert_y, invert_z)
        self.device: Optional[Any] = None
        self.name = "Sin joystick"
        self.error = ""

    def initialize(self) -> None:
        """Inicializa pygame y selecciona el primer joystick disponible."""
        if pygame is None:
            self.error = "pygame no está instalado"
            return
        pygame.init()
        pygame.joystick.init()
        self.refresh()

    def refresh(self) -> bool:
        """Detecta conexión o desconexión y devuelve el estado actual."""
        if pygame is None:
            return False
        try:
            pygame.joystick.init()
            pygame.event.pump()
            count = pygame.joystick.get_count()
            if count == 0:
                self.device = None
                self.name = "Sin joystick"
                self.error = "Joystick no conectado"
                return False
            if self.device is not None:
                try:
                    if self.device.get_init():
                        return True
                except (OSError, pygame.error):
                    pass
                self.device = None
            self.device = pygame.joystick.Joystick(0)
            self.device.init()
            if not self.device.get_init():
                self.device = None
                self.name = "Sin joystick"
                self.error = "Joystick no inicializado"
                return False
            self.name = self.device.get_name()
            self.error = ""
            return True
        except (OSError, pygame.error) as exc:
            self.device = None
            self.name = "Sin joystick"
            self.error = str(exc)
            return False

    @property
    def connected(self) -> bool:
        """Expone si existe un dispositivo inicializado."""
        if self.device is None:
            return False
        try:
            return bool(self.device.get_init())
        except (OSError, pygame.error):
            self.device = None
            self.name = "Sin joystick"
            self.error = "Joystick desconectado"
            return False

    @staticmethod
    def axis_to_byte(value: float, deadzone: float = 0.10, invert: bool = False) -> int:
        """Convierte un eje pygame a un byte centrado en 128."""
        value = max(-1.0, min(1.0, float(value)))
        if invert:
            value = -value
        if abs(value) <= deadzone:
            return 128
        magnitude = (abs(value) - deadzone) / (1.0 - deadzone)
        signed = magnitude if value > 0 else -magnitude
        return max(0, min(255, int(round(128 + signed * 127))))

    def read_axes(self) -> Tuple[int, int, int]:
        """Lee X, Y y Z, usando los tres primeros ejes del dispositivo."""
        if not self.refresh() or self.device is None:
            raise ConnectionError("El joystick no está conectado")
        try:
            pygame.event.pump()
            values = [self.device.get_axis(index) if self.device.get_numaxes() > index else 0.0
                      for index in range(3)]
            return tuple(
                self.axis_to_byte(value, self.deadzone, self.inversions[index])
                for index, value in enumerate(values)
            )
        except (OSError, pygame.error, IndexError) as exc:
            self.device = None
            self.error = str(exc)
            raise ConnectionError(self.error) from exc

    def read_buttons(self) -> Dict[str, bool]:
        """Mapea botón 0 a armado, 1 a emergencia y 2 a luces."""
        if self.device is None:
            return {"armed": False, "emergency": False, "lights": False}
        return {
            "armed": bool(self.device.get_numbuttons() > 0 and self.device.get_button(0)),
            "emergency": bool(self.device.get_numbuttons() > 1 and self.device.get_button(1)),
            "lights": bool(self.device.get_numbuttons() > 2 and self.device.get_button(2)),
        }

    def close(self) -> None:
        """Libera pygame y el dispositivo."""
        if self.device is not None:
            self.device.quit()
        self.device = None
        if pygame is not None:
            pygame.joystick.quit()
            pygame.quit()


def flags_from_buttons(buttons: Dict[str, bool], armed: bool = False,
                       emergency: bool = False, lights: bool = False) -> int:
    """Construye flags combinando botones y estados de la interfaz."""
    flags = 0
    if lights or buttons.get("lights", False):
        flags |= FLAG_LIGHTS
    if armed or buttons.get("armed", False):
        flags |= FLAG_ARMED
    if emergency or buttons.get("emergency", False):
        flags |= FLAG_EMERGENCY
    return flags
