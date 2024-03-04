from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Eyo! Tomorrow is Friday the 13th, we've all seen the Final Destination movies, so nobody comes to work tomorrow, okay? Okay."}