import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from app.main import create_app
from app.services import research

NOMINATIM_REVERSE = {
    "display_name": "Totana, Región de Murcia, España",
    "osm_type": "relation",
    "address": {
        "town": "Totana",
        "county": "Comarca del Guadalentín",
        "state": "Región de Murcia",
        "country": "España",
        "country_code": "es",
    },
}

NOMINATIM_SEARCH = [
    {
        "display_name": "Totana, Región de Murcia, España",
        "lat": "37.7714",
        "lon": "-1.5023",
        "type": "town",
        "boundingbox": ["37.6", "37.9", "-1.7", "-1.3"],
    }
]

WIKIPEDIA_GEOSEARCH = {
    "query": {
        "geosearch": [
            {"title": "Castillo de Totana", "dist": 850.2},
            {"title": "Yacimiento de La Bastida", "dist": 4200.0},
        ]
    }
}

WIKIPEDIA_EXTRACTS = {
    "query": {
        "pages": {
            "1": {
                "title": "Castillo de Totana",
                "fullurl": "https://en.wikipedia.org/wiki/Castillo_de_Totana",
                "extract": "A medieval castle and watchtower erected in 1266 during al-Andalus rule.",
            },
            "2": {
                "title": "Yacimiento de La Bastida",
                "fullurl": "https://en.wikipedia.org/wiki/La_Bastida",
                "extract": "Bronze age archaeological site excavated since 1869; the fortified settlement "
                "contains a necropolis and defensive ramparts.",
            },
        }
    }
}

PHOTON_REVERSE = {
    "features": [
        {
            "geometry": {"coordinates": [-1.5023, 37.7714]},
            "properties": {
                "name": "Avenida Rambla de la Santa",
                "city": "Totana",
                "county": "Bajo Guadalentín",
                "state": "Región de Murcia",
                "country": "España",
                "countrycode": "ES",
                "osm_type": "W",
            },
        }
    ]
}

PHOTON_SEARCH = {
    "features": [
        {
            "geometry": {"coordinates": [-1.5025376, 37.7697645]},
            "properties": {
                "name": "Totana",
                "county": "Bajo Guadalentín",
                "state": "Región de Murcia",
                "country": "España",
                "osm_value": "town",
                "extent": [-1.67, 37.89, -1.33, 37.66],
            },
        }
    ]
}

ARCHIVE_RESULT = {
    "response": {
        "docs": [
            {
                "identifier": "historia-de-totana",
                "title": "Historia de Totana",
                "year": "1902",
                "description": "<p>Local chronicle describing the Roman road and the old mill.</p>",
                "creator": "Anon",
            }
        ]
    }
}


@pytest.fixture
def client() -> TestClient:
    research.clear_cache()
    return TestClient(create_app())


def test_health(client: TestClient):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_layers_catalogue(client: TestClient):
    payload = client.get("/api/layers").json()
    assert any(layer["group"] == "lidar" for layer in payload)
    assert any(layer["group"] == "historical" and layer["epoch"] for layer in payload)
    epochs = client.get("/api/layers/epochs").json()
    assert epochs == sorted(epochs) and epochs


def test_search_detects_coordinates(client: TestClient):
    payload = client.get("/api/search", params={"q": "37.7714, -1.5023"}).json()
    assert payload["interpretation"] == "coordinate"
    assert payload["coordinate"]["utm"].startswith("30S")


@respx.mock
def test_search_geocodes_place(client: TestClient):
    respx.get("https://nominatim.openstreetmap.org/search").mock(
        return_value=httpx.Response(200, json=NOMINATIM_SEARCH)
    )
    payload = client.get("/api/search", params={"q": "Totana"}).json()
    assert payload["interpretation"] == "place"
    assert payload["results"][0]["display_name"].startswith("Totana")


@respx.mock
def test_research_returns_structured_report(client: TestClient):
    respx.get("https://nominatim.openstreetmap.org/reverse").mock(
        return_value=httpx.Response(200, json=NOMINATIM_REVERSE)
    )
    respx.get("https://en.wikipedia.org/w/api.php", params={"list": "geosearch"}).mock(
        return_value=httpx.Response(200, json=WIKIPEDIA_GEOSEARCH)
    )
    respx.get("https://en.wikipedia.org/w/api.php", params={"prop": "extracts|info"}).mock(
        return_value=httpx.Response(200, json=WIKIPEDIA_EXTRACTS)
    )
    respx.get("https://archive.org/advancedsearch.php").mock(
        return_value=httpx.Response(200, json=ARCHIVE_RESULT)
    )

    report = client.post(
        "/api/research", json={"latitude": 37.7714, "longitude": -1.5023}
    ).json()

    assert report["place_label"] == "Totana"
    assert report["administrative_context"]["country"] == "España"
    assert report["archaeological_potential"]["rating"] in ("High", "Medium", "Low")
    assert report["archaeological_potential"]["markers"]
    assert report["timeline"] and report["timeline"][0]["year"] <= report["timeline"][-1]["year"]
    assert {source["provider"] for source in report["sources"]} == {"wikipedia", "internet_archive"}
    assert report["provider_status"]["europeana"].startswith("skipped")
    assert report["synthesis_engine"] == "heuristic"
    assert report["cached"] is False

    cached = client.get(
        "/api/research", params={"lat": 37.7714, "lon": -1.5023}
    ).json()
    assert cached["cached"] is True


@respx.mock
def test_reverse_geocoding_falls_back_to_photon(client: TestClient):
    respx.get("https://nominatim.openstreetmap.org/reverse").mock(return_value=httpx.Response(403))
    respx.get("https://photon.komoot.io/reverse").mock(return_value=httpx.Response(200, json=PHOTON_REVERSE))
    respx.get("https://en.wikipedia.org/w/api.php").mock(return_value=httpx.Response(200, json={"query": {"geosearch": []}}))
    respx.get("https://archive.org/advancedsearch.php").mock(
        return_value=httpx.Response(200, json={"response": {"docs": []}})
    )

    report = client.post("/api/research", json={"latitude": 37.7714, "longitude": -1.5023}).json()
    assert report["provider_status"]["geocoder"] == "ok: photon"
    assert report["place_label"] == "Totana"
    assert report["administrative_context"]["country"] == "España"


@respx.mock
def test_search_falls_back_to_photon(client: TestClient):
    respx.get("https://nominatim.openstreetmap.org/search").mock(return_value=httpx.Response(429))
    respx.get("https://photon.komoot.io/api").mock(return_value=httpx.Response(200, json=PHOTON_SEARCH))
    payload = client.get("/api/search", params={"q": "Totana"}).json()
    assert payload["results"][0]["source"] == "photon"
    assert payload["results"][0]["latitude"] == pytest.approx(37.7697645)
    assert payload["results"][0]["bounding_box"] == [37.66, 37.89, -1.67, -1.33]


@respx.mock
def test_research_degrades_when_providers_fail(client: TestClient):
    respx.get("https://nominatim.openstreetmap.org/reverse").mock(side_effect=httpx.ConnectError("boom"))
    respx.get("https://photon.komoot.io/reverse").mock(side_effect=httpx.ConnectError("boom"))
    respx.get("https://en.wikipedia.org/w/api.php").mock(side_effect=httpx.ConnectError("boom"))
    respx.get("https://archive.org/advancedsearch.php").mock(side_effect=httpx.ConnectError("boom"))

    report = client.post("/api/research", json={"latitude": 0.0, "longitude": 0.0}).json()
    assert report["sources"] == []
    assert report["archaeological_potential"]["rating"] == "Low"
    assert report["provider_status"]["wikipedia"].startswith("error")
    assert report["provider_status"]["geocoder"].startswith("error")
    assert "No authoritative records" in report["narrative"]
