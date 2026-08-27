import pytest

from app.services.coordinates import (
    CoordinateParseError,
    format_dms,
    latlon_to_utm,
    parse_coordinate,
    utm_to_latlon,
)


def test_parse_decimal_degrees():
    parsed = parse_coordinate("37.7749, -122.4194")
    assert parsed.format == "decimal"
    assert parsed.latitude == pytest.approx(37.7749)
    assert parsed.longitude == pytest.approx(-122.4194)


def test_parse_dms():
    parsed = parse_coordinate("37°45'12.5\"N 1°30'00\"W")
    assert parsed.format == "dms"
    assert parsed.latitude == pytest.approx(37.753472, abs=1e-5)
    assert parsed.longitude == pytest.approx(-1.5, abs=1e-6)


def test_parse_utm_round_trip():
    utm_text = latlon_to_utm(37.7601, -1.5028)
    parsed = parse_coordinate(utm_text.replace("E", "").replace("N", " N"))
    assert parsed.latitude == pytest.approx(37.7601, abs=1e-4)
    assert parsed.longitude == pytest.approx(-1.5028, abs=1e-4)


def test_utm_inverse_matches_epsg_32630_reference():
    # Reference values produced by PROJ for EPSG:32630 -> EPSG:4326.
    latitude, longitude = utm_to_latlon(30, 500000, 4000000, northern_hemisphere=True)
    assert latitude == pytest.approx(36.144718, abs=1e-6)
    assert longitude == pytest.approx(-3.0, abs=1e-9)


def test_utm_forward_matches_epsg_32630_reference():
    assert latlon_to_utm(37.7601, -1.5028) == "30S 631881E 4180253N"


def test_format_dms_south_west():
    assert format_dms(-33.8688, -151.2093).startswith("33°52'")
    assert format_dms(-33.8688, -151.2093).endswith("W")


def test_invalid_input_raises():
    with pytest.raises(CoordinateParseError):
        parse_coordinate("not a coordinate")
    with pytest.raises(CoordinateParseError):
        parse_coordinate("120.0, 500.0")
