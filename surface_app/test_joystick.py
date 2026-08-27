#!/usr/bin/env python3
"""Verificación autónoma de ejes, protocolo, checksum y comportamiento seguro."""

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_JOYSTICKDRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from surface_app.joystick import Joystick
from surface_app.protocol import (
    FLAG_ARMED,
    FLAG_EMERGENCY,
    checksum,
    is_failsafe,
    pack_frame,
    parse_telemetry,
    unpack_frame,
)


class SimulatedAxisSource:
    """Fuente documentada para una máquina sin joystick físico."""

    def __init__(self) -> None:
        self.values = (0.0, 0.0, 0.0)

    def set_axes(self, values):
        self.values = tuple(values)

    def read(self):
        return tuple(Joystick.axis_to_byte(value, 0.10) for value in self.values)


def main() -> int:
    """Ejecuta todas las comprobaciones y devuelve cero sólo si pasan."""
    try:
        import pygame

        pygame.init()
        pygame.joystick.init()
        print(f"pygame inicializado; joysticks detectados: {pygame.joystick.get_count()}")
    except Exception as exc:
        print(f"pygame no pudo inicializarse ({exc}); se usa fuente simulada")

    source = SimulatedAxisSource()
    cases = (
        (0.0, 0.0, 0.0),
        (0.05, -0.05, 0.09),
        (1.0, -1.0, 0.5),
        (-0.75, 0.4, -1.0),
    )
    for values in cases:
        source.set_axes(values)
        axes = source.read()
        flags = FLAG_ARMED
        packet = pack_frame(*axes, flags)
        decoded = unpack_frame(packet)
        print(f"entrada={values} -> bytes={axes} trama={packet.hex()} -> {decoded}")
        assert decoded and tuple(decoded[key] for key in ("x", "y", "z")) == axes
        assert decoded["flags"] == flags
        assert packet[-1] == checksum(*axes, flags)

    source.set_axes((0.0, 0.0, 0.0))
    assert source.read() == (128, 128, 128)
    bad = bytearray(pack_frame(128, 128, 128, FLAG_ARMED))
    bad[-1] ^= 0x01
    assert unpack_frame(bad) is None
    assert unpack_frame(pack_frame(128, 128, 128, FLAG_EMERGENCY))["flags"] == FLAG_EMERGENCY
    telemetry = parse_telemetry("TLM;vin=12.4;fps=20;fs=1\n")
    assert telemetry and telemetry["vin"] == 12.4 and telemetry["fps"] == 20
    assert is_failsafe(telemetry)
    assert parse_telemetry("mensaje inválido") is None
    print("PASS: deadband, round-trip, checksum, emergencia y telemetría verificados")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
