# Announcement API (PoC)

This repository contains a Proof-of-Concept (PoC) API developed with FastAPI to simulate announcements sent to employees
in a company. The API is built using Python 3.9.2 and FastAPI 0.110.0.

### Project Structure

```
.
├── Dockerfile
├── README.md
├── nginx
│   └── Dockerfile
├── nginx.conf
├── postman
│   └── eyo-halla-at-me-systems.postman_collection.json
├── requirements.txt
├── src
│   ├── main.py
│   └── models.py
└── tests
    └── unit
        └── tests.py
```

# Eyo Halla At Me Announcement Systems

### Introduction

>Eyo Halla At Me Systems is a simple FastAPI application that allows sending announcements. This README provides instructions on how to set up and run the project using Docker.

### Prerequisites

- Docker installed on your machine. You can download and install Docker from [here](https://docs.docker.com/get-docker/).

### Getting Started

1. Clone this repository to your local machine:

    ```bash
    git clone https://github.com/tzone85/announcements.git
    cd announcements
    ```

2. Install a virtual environment and activate it:

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd src
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload 
    You can now access the FastAPI application at `http://localhost:8000/api/v1/announcements`.
    It will be empty initially, but you can add announcements using the POST `/api/v1/announcements` endpoint.
    
   Example Payload:
       {
        "message": "Eyo Halla At Me",
        "id": "1"
       }
   
   Example Response:
       {
        "message": "Eyo Halla At Me",
        "id": "1"
       }
   
    You can also access the Swagger documentation at `http://localhost:8000/swagger`.
    ```

3. Build the Docker images for the application and Nginx server:

    ```bash
    docker build -t announcement-systems .
    docker build -t nginx-server ./nginx
    ```

4. Run the Docker containers:

    ```bash
    docker run -d --name announcement_systems_app announcement-systems
    docker run -d --name nginx-server -p 80:80 nginx-server
    ```

   The FastAPI application will be accessible at `http://localhost:80`.

## Running Tests

### Unit Tests

To run the unit tests for the FastAPI application, execute the following command:

```bash
docker exec announcement_systems pytest /app/tests/unit
