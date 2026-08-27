#!/usr/bin/env python3
"""Verificación autónoma de los caminos de mando, serie y protocolo."""

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_JOYSTICKDRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import surface_app.joystick as joystick_module
from surface_app.joystick import Joystick, flags_from_buttons
from surface_app.protocol import (
    FLAG_ARMED,
    FLAG_EMERGENCY,
    FLAG_LIGHTS,
    checksum,
    is_failsafe,
    pack_frame,
    parse_telemetry,
    unpack_frame,
)
from surface_app.serial_link import SerialLink


class FakeJoystickDevice:
    """Dispositivo pygame mínimo para ejecutar el camino real de lectura."""

    def __init__(self) -> None:
        self.axes = (0.0, 0.0, 0.0)
        self.buttons = (False, False, False)
        self.alive = True

    def init(self) -> None:
        return None

    def quit(self) -> None:
        self.alive = False

    def get_init(self) -> bool:
        return self.alive

    def get_name(self) -> str:
        return "Joystick simulado"

    def get_numaxes(self) -> int:
        return len(self.axes)

    def get_axis(self, index: int) -> float:
        if not self.alive:
            raise OSError("dispositivo simulado desconectado")
        return self.axes[index]

    def get_numbuttons(self) -> int:
        return len(self.buttons)

    def get_button(self, index: int) -> bool:
        return self.buttons[index]


class FakeJoystickModule:
    """Parte pygame.joystick necesaria para la detección de conexión."""

    def __init__(self, device: FakeJoystickDevice) -> None:
        self.device = device

    def init(self) -> None:
        return None

    def quit(self) -> None:
        return None

    def get_count(self) -> int:
        return 1

    def Joystick(self, _index: int) -> FakeJoystickDevice:
        return self.device


class FakePygame:
    """Sustituto de pygame que conserva la excepción esperada por el código."""

    def __init__(self, device: FakeJoystickDevice, error_type: type) -> None:
        self.joystick = FakeJoystickModule(device)
        self.event = self
        self.error = error_type

    def pump(self) -> None:
        return None


class FakeSerialPort:
    """Puerto serie falso con captura de escrituras y fallos configurables."""

    def __init__(self, fail_write: bool = False, **_kwargs) -> None:
        self.is_open = True
        self.fail_write = fail_write
        self.writes = []
        self.in_waiting = 0

    def write(self, data: bytes) -> int:
        if self.fail_write:
            raise OSError("fallo de escritura simulado")
        self.writes.append(bytes(data))
        return len(data)

    def readline(self) -> bytes:
        return b""

    def close(self) -> None:
        self.is_open = False


def assert_protocol_basics() -> None:
    """Conserva las comprobaciones originales de checksum y failsafe."""
    cases = (
        (0.0, 0.0, 0.0),
        (0.05, -0.05, 0.09),
        (1.0, -1.0, 0.5),
        (-0.75, 0.4, -1.0),
    )
    for values in cases:
        axes = tuple(Joystick.axis_to_byte(value, 0.10) for value in values)
        packet = pack_frame(*axes, FLAG_ARMED)
        decoded = unpack_frame(packet)
        print(f"entrada estática={values} -> bytes={axes} trama={packet.hex()} -> {decoded}")
        assert decoded and tuple(decoded[key] for key in ("x", "y", "z")) == axes
        assert decoded["flags"] == FLAG_ARMED
        assert packet[-1] == checksum(*axes, FLAG_ARMED)
    assert tuple(Joystick.axis_to_byte(0.0, 0.10) for _ in range(3)) == (128, 128, 128)
    bad = bytearray(pack_frame(128, 128, 128, FLAG_ARMED))
    bad[-1] ^= 0x01
    assert unpack_frame(bad) is None
    assert unpack_frame(pack_frame(128, 128, 128, FLAG_EMERGENCY))["flags"] == FLAG_EMERGENCY
    telemetry = parse_telemetry("TLM;vin=12.4;fps=20;fs=1\n")
    assert telemetry and telemetry["vin"] == 12.4 and telemetry["fps"] == 20
    assert is_failsafe(telemetry)
    assert parse_telemetry("mensaje inválido") is None


def assert_joystick_path() -> None:
    """Ejecuta ejes, botones, flags y desconexión contra un dispositivo falso."""
    real_pygame = joystick_module.pygame
    device = FakeJoystickDevice()
    fake_pygame = FakePygame(device, real_pygame.error if real_pygame else RuntimeError)
    joystick_module.pygame = fake_pygame
    try:
        controller = Joystick(deadzone=0.10)
        controller.device = device
        controller.name = device.get_name()
        sweeps = (
            ((0.0, 0.0, 0.0), (False, False, False)),
            ((0.25, -0.50, 1.0), (True, False, True)),
            ((-1.0, 0.75, -0.2), (False, True, False)),
        )
        for axis_values, button_values in sweeps:
            device.axes = axis_values
            device.buttons = button_values
            axes = controller.read_axes()
            buttons = controller.read_buttons()
            flags = flags_from_buttons(buttons)
            packet = pack_frame(*axes, flags)
            print(f"entrada simulada={axis_values}, botones={button_values} -> "
                  f"bytes={axes}, flags=0x{flags:02X}, trama={packet.hex()}")
            assert unpack_frame(packet)["flags"] == flags
            expected_flags = (
                (FLAG_ARMED if button_values[0] else 0)
                | (FLAG_EMERGENCY if button_values[1] else 0)
                | (FLAG_LIGHTS if button_values[2] else 0)
            )
            assert flags == expected_flags
        device.alive = False
        try:
            controller.read_axes()
        except ConnectionError:
            pass
        else:
            raise AssertionError("La desconexión simulada no generó ConnectionError")
        assert not controller.connected
        assert controller.device is None
    finally:
        joystick_module.pygame = real_pygame


def assert_serial_path() -> None:
    """Comprueba parada, cierre y fallo de escritura sin hardware."""
    stop_packet = bytes.fromhex("aa 80 80 80 00 80")
    port = FakeSerialPort()
    link = SerialLink("/dev/falso", retry_seconds=0, serial_factory=lambda *_args, **kwargs: port)
    assert link.send_stop()
    assert port.writes == [stop_packet]
    link.close()
    assert port.writes[-1] == stop_packet

    failing_port = FakeSerialPort(fail_write=True)
    failing_link = SerialLink("/dev/falso", retry_seconds=0,
                              serial_factory=lambda *_args, **kwargs: failing_port)
    assert not failing_link.send(128, 128, 128, FLAG_ARMED)
    assert not failing_link.connected
    print(f"parada serie={stop_packet.hex()}, escrituras={len(port.writes)}, "
          "fallo de escritura desconectó el enlace")


def main() -> int:
    """Inicializa pygame en modo dummy y ejecuta todas las comprobaciones."""
    try:
        import pygame

        pygame.init()
        pygame.joystick.init()
        print(f"pygame inicializado; joysticks detectados: {pygame.joystick.get_count()}")
    except Exception as exc:
        print(f"pygame no pudo inicializarse ({exc}); se usa fuente simulada")
    assert_protocol_basics()
    assert_joystick_path()
    assert_serial_path()
    print("PASS: protocolo, deadband, joystick real simulado, desconexión, serie y failsafe")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
