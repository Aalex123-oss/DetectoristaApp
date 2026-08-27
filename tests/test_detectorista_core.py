import folium
import pytest
from shapely.geometry import Point, Polygon

import detectorista_core as core


def marker_icon_color(marker):
    icon = next(c for c in marker._children.values() if isinstance(c, folium.Icon))
    return icon.options["marker_color"]


def marker_popup_text(marker):
    popup = next(c for c in marker._children.values() if isinstance(c, folium.Popup))
    return popup.html.render()


def square(lon, lat, size=0.01):
    """Polígono cuadrado centrado en (lon, lat)."""
    half = size / 2
    return Polygon(
        [
            (lon - half, lat - half),
            (lon + half, lat - half),
            (lon + half, lat + half),
            (lon - half, lat + half),
        ]
    )


class TestValidateCoordinates:
    def test_returns_floats(self):
        assert core.validate_coordinates("37.5", "-1.5") == (37.5, -1.5)

    @pytest.mark.parametrize("lat", [-90.0, 0.0, 90.0])
    @pytest.mark.parametrize("lon", [-180.0, 0.0, 180.0])
    def test_accepts_range_limits(self, lat, lon):
        assert core.validate_coordinates(lat, lon) == (lat, lon)

    @pytest.mark.parametrize("lat", [90.1, -90.1, 1000])
    def test_rejects_latitude_out_of_range(self, lat):
        with pytest.raises(ValueError, match="Latitud"):
            core.validate_coordinates(lat, 0.0)

    @pytest.mark.parametrize("lon", [180.1, -180.1, 1000])
    def test_rejects_longitude_out_of_range(self, lon):
        with pytest.raises(ValueError, match="Longitud"):
            core.validate_coordinates(0.0, lon)

    def test_rejects_non_numeric(self):
        with pytest.raises(ValueError):
            core.validate_coordinates("norte", 0.0)


class TestMakePoint:
    def test_uses_lon_lat_order(self):
        point = core.make_point(37.7701, -1.5020)
        assert (point.x, point.y) == (-1.5020, 37.7701)

    def test_validates_coordinates(self):
        with pytest.raises(ValueError):
            core.make_point(91.0, 0.0)


class TestIsFree:
    def test_free_without_restricted_areas(self):
        assert core.is_free(Point(-1.5020, 37.7701)) is True

    def test_free_when_outside_restricted_areas(self):
        area = square(-1.6, 37.7)
        assert core.is_free(Point(-1.5020, 37.7701), [area]) is True

    def test_restricted_when_inside_area(self):
        area = square(-1.5020, 37.7701)
        assert core.is_free(Point(-1.5020, 37.7701), [area]) is False

    def test_restricted_when_on_area_boundary(self):
        area = square(-1.5, 37.0, size=0.02)
        boundary_point = Point(-1.49, 37.0)
        assert core.is_free(boundary_point, [area]) is False

    def test_restricted_if_any_area_matches(self):
        areas = [square(-2.0, 38.0), square(-1.5020, 37.7701)]
        assert core.is_free(Point(-1.5020, 37.7701), areas) is False

    def test_accepts_generator(self):
        areas = (square(-1.5020, 37.7701) for _ in range(1))
        assert core.is_free(Point(-1.5020, 37.7701), areas) is False


class TestPresentationHelpers:
    def test_marker_color(self):
        assert core.marker_color(True) == "green"
        assert core.marker_color(False) == "red"

    def test_marker_popup(self):
        assert core.marker_popup(True) == "Libre"
        assert core.marker_popup(False) == "Prohibido"

    def test_report_message(self):
        assert core.report_message(True) == core.FREE_REPORT
        assert core.report_message(False) == core.RESTRICTED_REPORT


class TestBuildMap:
    def test_centered_on_coordinates_with_default_zoom(self):
        mapa = core.build_map(37.7701, -1.5020, True)
        assert isinstance(mapa, folium.Map)
        assert mapa.location == [37.7701, -1.5020]
        assert mapa.options["zoom"] == core.DEFAULT_ZOOM

    def test_custom_zoom(self):
        mapa = core.build_map(37.7701, -1.5020, True, zoom=10)
        assert mapa.options["zoom"] == 10

    @pytest.mark.parametrize(
        "free, color, popup",
        [(True, "green", "Libre"), (False, "red", "Prohibido")],
    )
    def test_marker_reflects_result(self, free, color, popup):
        mapa = core.build_map(37.7701, -1.5020, free)
        markers = [c for c in mapa._children.values() if isinstance(c, folium.Marker)]
        assert len(markers) == 1
        marker = markers[0]
        assert marker.location == [37.7701, -1.5020]
        assert marker_icon_color(marker) == color
        assert popup in marker_popup_text(marker)

    def test_validates_coordinates(self):
        with pytest.raises(ValueError):
            core.build_map(0.0, -181.0, True)


class TestAnalyze:
    def test_free_point(self):
        free, report, mapa = core.analyze(37.7701, -1.5020)
        assert free is True
        assert report == core.FREE_REPORT
        assert mapa.location == [37.7701, -1.5020]

    def test_restricted_point(self):
        free, report, mapa = core.analyze(
            37.7701, -1.5020, restricted_areas=[square(-1.5020, 37.7701)]
        )
        assert free is False
        assert report == core.RESTRICTED_REPORT
        markers = [c for c in mapa._children.values() if isinstance(c, folium.Marker)]
        assert marker_icon_color(markers[0]) == "red"

    def test_consumes_generator_once(self):
        areas = (square(-1.5020, 37.7701) for _ in range(1))
        free, _, _ = core.analyze(37.7701, -1.5020, restricted_areas=areas)
        assert free is False

    def test_propagates_invalid_coordinates(self):
        with pytest.raises(ValueError, match="Latitud"):
            core.analyze(120.0, 0.0)

    def test_forwards_zoom(self):
        _, _, mapa = core.analyze(37.7701, -1.5020, zoom=8)
        assert mapa.options["zoom"] == 8
