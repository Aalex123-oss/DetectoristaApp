"""Coordinate parsing and conversion (Decimal Degrees, DMS, UTM/WGS84).

The UTM <-> geographic conversion uses the standard Transverse Mercator series
expansion for the WGS84 ellipsoid, so no external projection library is needed.
"""

from __future__ import annotations

import math
import re

from app.models import ParsedCoordinate

WGS84_A = 6378137.0
WGS84_F = 1 / 298.257223563
WGS84_E2 = 2 * WGS84_F - WGS84_F**2
K0 = 0.9996
FALSE_EASTING = 500000.0
FALSE_NORTHING = 10000000.0

_DECIMAL_RE = re.compile(
    r"^\s*(?P<lat>[+-]?\d{1,3}(?:\.\d+)?)\s*[,;\s]\s*(?P<lon>[+-]?\d{1,3}(?:\.\d+)?)\s*$"
)

_DMS_PART = r"""
    (?P<deg>\d{1,3})\s*(?:°|d|:|\s)\s*
    (?:(?P<min>\d{1,2}(?:\.\d+)?)\s*(?:'|’|m|:|\s)\s*)?
    (?:(?P<sec>\d{1,2}(?:\.\d+)?)\s*(?:"|”|''|s)?\s*)?
    (?P<hem>[NSEWnsew])
"""

_DMS_RE = re.compile(
    r"^\s*" + _DMS_PART.replace("deg", "lat_deg").replace("min", "lat_min").replace("sec", "lat_sec").replace("hem", "lat_hem")
    + r"\s*[,;/]?\s*"
    + _DMS_PART.replace("deg", "lon_deg").replace("min", "lon_min").replace("sec", "lon_sec").replace("hem", "lon_hem")
    + r"\s*$",
    re.VERBOSE,
)

_UTM_RE = re.compile(
    r"^\s*(?P<zone>[1-9]|[1-5]\d|60)\s*(?P<band>[C-HJ-NP-X])?\s*[,\s]\s*"
    r"(?:E\s*)?(?P<easting>\d+(?:\.\d+)?)\s*[,\s]\s*"
    r"(?:N\s*)?(?P<northing>\d+(?:\.\d+)?)\s*(?P<hemisphere>[NS])?\s*$",
    re.IGNORECASE,
)


class CoordinateParseError(ValueError):
    """Raised when a string cannot be interpreted as a coordinate."""


def _dms_to_decimal(degrees: str, minutes: str | None, seconds: str | None, hemisphere: str) -> float:
    value = float(degrees) + float(minutes or 0) / 60 + float(seconds or 0) / 3600
    if hemisphere.upper() in ("S", "W"):
        value = -value
    return value


def utm_to_latlon(zone: int, easting: float, northing: float, northern_hemisphere: bool) -> tuple[float, float]:
    """Convert UTM coordinates to WGS84 latitude/longitude in decimal degrees."""
    x = easting - FALSE_EASTING
    y = northing if northern_hemisphere else northing - FALSE_NORTHING

    e1 = (1 - math.sqrt(1 - WGS84_E2)) / (1 + math.sqrt(1 - WGS84_E2))
    m = y / K0
    mu = m / (WGS84_A * (1 - WGS84_E2 / 4 - 3 * WGS84_E2**2 / 64 - 5 * WGS84_E2**3 / 256))

    phi1 = (
        mu
        + (3 * e1 / 2 - 27 * e1**3 / 32) * math.sin(2 * mu)
        + (21 * e1**2 / 16 - 55 * e1**4 / 32) * math.sin(4 * mu)
        + (151 * e1**3 / 96) * math.sin(6 * mu)
        + (1097 * e1**4 / 512) * math.sin(8 * mu)
    )

    ep2 = WGS84_E2 / (1 - WGS84_E2)
    c1 = ep2 * math.cos(phi1) ** 2
    t1 = math.tan(phi1) ** 2
    n1 = WGS84_A / math.sqrt(1 - WGS84_E2 * math.sin(phi1) ** 2)
    r1 = WGS84_A * (1 - WGS84_E2) / (1 - WGS84_E2 * math.sin(phi1) ** 2) ** 1.5
    d = x / (n1 * K0)

    latitude = phi1 - (n1 * math.tan(phi1) / r1) * (
        d**2 / 2
        - (5 + 3 * t1 + 10 * c1 - 4 * c1**2 - 9 * ep2) * d**4 / 24
        + (61 + 90 * t1 + 298 * c1 + 45 * t1**2 - 252 * ep2 - 3 * c1**2) * d**6 / 720
    )
    longitude = (
        d
        - (1 + 2 * t1 + c1) * d**3 / 6
        + (5 - 2 * c1 + 28 * t1 - 3 * c1**2 + 8 * ep2 + 24 * t1**2) * d**5 / 120
    ) / math.cos(phi1)

    central_meridian = math.radians(zone * 6 - 183)
    return math.degrees(latitude), math.degrees(central_meridian + longitude)


def latlon_to_utm(latitude: float, longitude: float) -> str:
    """Format a lat/lon pair as a human readable UTM/WGS84 string."""
    zone = int((longitude + 180) / 6) + 1
    central_meridian = math.radians(zone * 6 - 183)
    phi = math.radians(latitude)
    lam = math.radians(longitude)

    n = WGS84_A / math.sqrt(1 - WGS84_E2 * math.sin(phi) ** 2)
    t = math.tan(phi) ** 2
    c = WGS84_E2 / (1 - WGS84_E2) * math.cos(phi) ** 2
    a = math.cos(phi) * (lam - central_meridian)

    m = WGS84_A * (
        (1 - WGS84_E2 / 4 - 3 * WGS84_E2**2 / 64 - 5 * WGS84_E2**3 / 256) * phi
        - (3 * WGS84_E2 / 8 + 3 * WGS84_E2**2 / 32 + 45 * WGS84_E2**3 / 1024) * math.sin(2 * phi)
        + (15 * WGS84_E2**2 / 256 + 45 * WGS84_E2**3 / 1024) * math.sin(4 * phi)
        - (35 * WGS84_E2**3 / 3072) * math.sin(6 * phi)
    )

    easting = (
        K0 * n * (a + (1 - t + c) * a**3 / 6 + (5 - 18 * t + t**2 + 72 * c - 58 * WGS84_E2 / (1 - WGS84_E2)) * a**5 / 120)
        + FALSE_EASTING
    )
    northing = K0 * (
        m
        + n
        * math.tan(phi)
        * (
            a**2 / 2
            + (5 - t + 9 * c + 4 * c**2) * a**4 / 24
            + (61 - 58 * t + t**2 + 600 * c - 330 * WGS84_E2 / (1 - WGS84_E2)) * a**6 / 720
        )
    )
    if latitude < 0:
        northing += FALSE_NORTHING

    band = _latitude_band(latitude)
    return f"{zone}{band} {easting:.0f}E {northing:.0f}N"


def _latitude_band(latitude: float) -> str:
    bands = "CDEFGHJKLMNPQRSTUVWX"
    if latitude < -80 or latitude > 84:
        return "Z"
    index = int((latitude + 80) / 8)
    return bands[min(index, len(bands) - 1)]


def format_decimal(latitude: float, longitude: float) -> str:
    return f"{latitude:.6f}, {longitude:.6f}"


def format_dms(latitude: float, longitude: float) -> str:
    def component(value: float, positive: str, negative: str) -> str:
        hemisphere = positive if value >= 0 else negative
        value = abs(value)
        degrees = int(value)
        minutes_float = (value - degrees) * 60
        minutes = int(minutes_float)
        seconds = (minutes_float - minutes) * 60
        return f"{degrees}°{minutes:02d}'{seconds:05.2f}\"{hemisphere}"

    return f"{component(latitude, 'N', 'S')} {component(longitude, 'E', 'W')}"


def parse_coordinate(raw: str) -> ParsedCoordinate:
    """Parse decimal degrees, DMS or UTM text into a WGS84 coordinate."""
    text = raw.strip().replace("−", "-")
    if not text:
        raise CoordinateParseError("Empty coordinate string")

    dms = _DMS_RE.match(text)
    if dms:
        latitude = _dms_to_decimal(
            dms.group("lat_deg"), dms.group("lat_min"), dms.group("lat_sec"), dms.group("lat_hem")
        )
        longitude = _dms_to_decimal(
            dms.group("lon_deg"), dms.group("lon_min"), dms.group("lon_sec"), dms.group("lon_hem")
        )
        return _build(latitude, longitude, "dms")

    decimal = _DECIMAL_RE.match(text)
    if decimal:
        return _build(float(decimal.group("lat")), float(decimal.group("lon")), "decimal")

    utm = _UTM_RE.match(text)
    if utm:
        band = (utm.group("band") or "").upper()
        hemisphere = (utm.group("hemisphere") or "").upper()
        northern = True
        if band:
            northern = band >= "N"
        elif hemisphere:
            northern = hemisphere == "N"
        latitude, longitude = utm_to_latlon(
            int(utm.group("zone")), float(utm.group("easting")), float(utm.group("northing")), northern
        )
        return _build(latitude, longitude, "utm")

    raise CoordinateParseError(f"Unrecognised coordinate format: {raw!r}")


def _build(latitude: float, longitude: float, fmt: str) -> ParsedCoordinate:
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise CoordinateParseError(f"Coordinate out of range: {latitude}, {longitude}")
    return ParsedCoordinate(
        latitude=round(latitude, 8),
        longitude=round(longitude, 8),
        format=fmt,  # type: ignore[arg-type]
        normalized=format_decimal(latitude, longitude),
        utm=latlon_to_utm(latitude, longitude),
    )


def looks_like_coordinate(raw: str) -> bool:
    try:
        parse_coordinate(raw)
    except CoordinateParseError:
        return False
    return True


def haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371008.8
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = phi2 - phi1
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))
