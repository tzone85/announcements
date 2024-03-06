from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


async def test_send_announcement():
    data = {
        "message": (
            "Eyo! Tomorrow is Friday the 13th, we've all seen "
            "the Final Destination movies, so nobody"
            " comes to work tomorrow, okay? Okay."
        )
    }
    response = client.post("/api/v1/announcements", json=data)
    assert response.status_code == 201
    assert response.json()["message"] == data["message"]

    response = client.get("/api/v1/announcements")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["message"] == data["message"]

    new_message = "New message for testing update functionality"
    announcement_id = response.json()[0]["id"]
    response = client.put(
        f"/api/v1/announcements/{announcement_id}",
        json={"id": announcement_id, "message": new_message},
    )
    assert response.status_code == 200
    assert response.json()["message"] == new_message

    response = client.delete(f"/api/v1/announcements/{announcement_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Announcement deleted successfully"
