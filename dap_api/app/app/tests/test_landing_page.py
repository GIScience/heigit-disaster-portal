from fastapi.testclient import TestClient


def test_get_landing_page(
        client: TestClient
) -> None:
    r = client.get(
        f"/"
    )
    assert r.status_code == 200
    assert r.text == '"TODO: static landing page"'
