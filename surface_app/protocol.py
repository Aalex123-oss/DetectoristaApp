"""Funciones puras para las tramas binarias y la telemetría ASCII."""

from typing import Dict, Optional, Union

START_BYTE = 0xAA
FRAME_SIZE = 6
FLAG_LIGHTS = 0x01
FLAG_ARMED = 0x02
FLAG_EMERGENCY = 0x04
FLAGS_MASK = FLAG_LIGHTS | FLAG_ARMED | FLAG_EMERGENCY


def checksum(x: int, y: int, z: int, flags: int) -> int:
    """Calcula el octeto de comprobación definido por el protocolo."""
    return (x + y + z + flags) & 0xFF


def pack_frame(x: int, y: int, z: int, flags: int) -> bytes:
    """Empaqueta una trama de seis bytes y valida sus campos."""
    values = (x, y, z, flags)
    if any(not isinstance(value, int) or not 0 <= value <= 255 for value in values):
        raise ValueError("Los campos de la trama deben ser enteros entre 0 y 255")
    if flags & ~FLAGS_MASK:
        raise ValueError("Los bits reservados de flags deben estar a cero")
    return bytes((START_BYTE, x, y, z, flags, checksum(x, y, z, flags)))


def unpack_frame(data: Union[bytes, bytearray, memoryview]) -> Optional[Dict[str, int]]:
    """Valida y desempaqueta una trama; devuelve None si no es válida."""
    raw = bytes(data)
    if len(raw) != FRAME_SIZE or raw[0] != START_BYTE:
        return None
    if raw[4] & ~FLAGS_MASK or raw[5] != checksum(raw[1], raw[2], raw[3], raw[4]):
        return None
    return {"x": raw[1], "y": raw[2], "z": raw[3], "flags": raw[4], "checksum": raw[5]}


def parse_telemetry(line: Union[str, bytes]) -> Optional[Dict[str, Union[str, float, int]]]:
    """Convierte una línea TLM en un diccionario con tipos numéricos."""
    if isinstance(line, bytes):
        line = line.decode("ascii", errors="replace")
    text = line.strip()
    if not text.startswith("TLM;"):
        return None
    result: Dict[str, Union[str, float, int]] = {"tipo": "TLM"}
    for item in text.split(";")[1:]:
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        try:
            result[key] = float(value) if "." in value else int(value)
        except ValueError:
            result[key] = value
    return result


def is_failsafe(telemetry: Optional[Dict[str, Union[str, float, int]]]) -> bool:
    """Indica si una telemetría válida informa del modo failsafe."""
    return bool(telemetry and telemetry.get("fs") == 1)
