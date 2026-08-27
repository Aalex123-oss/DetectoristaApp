"""Configuración persistente y opciones de línea de órdenes del ROV."""

from dataclasses import asdict, dataclass, fields
import json
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence


@dataclass
class Config:
    """Parámetros de operación con valores seguros para comenzar."""

    serial_port: str = "/dev/ttyUSB0"
    baudrate: int = 57600
    video_source: Any = 0
    deadzone: float = 0.10
    invert_x: bool = False
    invert_y: bool = False
    invert_z: bool = False
    send_rate: float = 20.0
    config_path: Optional[str] = None

    @classmethod
    def load(cls, path: Optional[str] = None) -> "Config":
        """Carga JSON opcional y conserva los valores predeterminados."""
        candidate = Path(path or "config.json")
        values = {}
        if candidate.is_file():
            with candidate.open("r", encoding="utf-8") as stream:
                raw = json.load(stream)
            valid = {field.name for field in fields(cls)}
            values = {key: value for key, value in raw.items() if key in valid}
        values["config_path"] = str(candidate) if candidate.is_file() else path
        return cls(**values)

    def update(self, overrides: Mapping[str, Any]) -> "Config":
        """Devuelve una configuración con las opciones proporcionadas."""
        values = asdict(self)
        values.update({key: value for key, value in overrides.items() if value is not None})
        return Config(**values)


def apply_arguments(config: Config, args: Any) -> Config:
    """Aplica los atributos definidos de argparse sin alterar los demás."""
    names = ("serial_port", "video_source", "baudrate", "send_rate")
    overrides = {name: getattr(args, name, None) for name in names}
    if getattr(args, "no_video", False):
        overrides["video_source"] = None
    return config.update(overrides)


def parse_video_source(value: Any) -> Any:
    """Convierte índices de cámara escritos como texto y conserva las URL."""
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return value
