import logging
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Database:
    messages = []
    id_counter = 0


class Announcement(BaseModel):
    id: Optional[int]
    message: str


app = FastAPI(docs_url="/swagger")


@app.get("/")
async def read_root():
    return {"message": "HelloooooOOOooOOO, family!! (by Vusi Thembekwayo)"}


@app.get("/api/v1/announcements", response_model=List[Announcement])
async def get_announcements():
    return Database.messages


@app.post("/api/v1/announcements", response_model=Announcement,
          status_code=201)
async def create_announcement(announcement: Announcement):
    try:
        Database.id_counter += 1
        announcement.id = Database.id_counter
        Database.messages.append(announcement)
        return announcement
    except Exception as e:
        logger.error(f"Failed to create announcement: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.put("/api/v1/announcements/{announcement_id}",
         response_model=Announcement)
async def update_announcement(announcement_id: int,
                              announcement: Announcement):
    try:
        if announcement_id < 1 or announcement_id > Database.id_counter:
            raise HTTPException(status_code=404, detail=(
                "Announcement not found"
            ))
        if announcement.id != announcement_id:
            raise HTTPException(status_code=400, detail=(
                "Cannot change announcement ID"
            ))
        Database.messages[announcement_id - 1] = announcement
        return announcement
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Failed to update announcement: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.delete("/api/v1/announcements/{announcement_id}")
async def delete_announcement(announcement_id: int):
    try:
        if announcement_id < 1 or announcement_id > Database.id_counter:
            raise HTTPException(status_code=404, detail=(
                "Announcement not found"
            ))
        del Database.messages[announcement_id - 1]
        return {"message": "Announcement deleted successfully"}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Failed to delete announcement: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        docs_url="/swagger",
        redoc_url=None,
    )
