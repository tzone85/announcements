from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Eyo! Tomorrow is Friday the 13th, we've all seen the Final Destination movies, so nobody comes to work tomorrow, okay? Okay."}
