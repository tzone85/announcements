from fastapi import FastAPI, HTTPException
from models import Announcement

app = FastAPI(docs_url="/swagger")


@app.post("/announcements", status_code=201)
async def send_announcement(announcement: Announcement):
    if not announcement.message:
        raise HTTPException(status_code=400, detail=(
                                "Announcement message cannot be empty"
                                ))

    print(f"Sending announcement: {announcement.message}")

    return {"message": (
                "Eyo! Tomorrow is Friday the 13th, we've all seen the Final"
                " Destination movies, so nobody comes"
                "to work tomorrow, okay? Okay"
    )}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        docs_url="/swagger",
        redoc_url=None,  # Optional: Disable ReDoc documentation
    )
