from src.main import app
from src.models import Announcement

async def test_send_announcement():
    data = Announcement(message="Eyo! Tomorrow is Friday the 13th, we've all seen the Final Destination movies, so nobody comes to work tomorrow, okay? Okay.")
    response = await app.client.post("/announcements", json=data.dict())
    assert response.status_code == 200
    assert response.json() == {"message": "Eyo! Tomorrow is Friday the 13th, we've all seen the Final Destination movies, so nobody comes to work tomorrow, okay? Okay."}
    