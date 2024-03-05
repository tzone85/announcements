# Announcement API (PoC)

This repository contains a Proof-of-Concept (PoC) API developed with FastAPI to simulate announcements sent to employees.

## Case Study Tasks
   - Propose at least 2 reasons why employees might be receiving the same
     announcement more than once.
   >__Concurrency Issues__: Sometimes, the system that handles the announcements may be poorly syncrhonized.
> This can lead to multiple instances of the scheduler, attempting to send announcements at the same time. This could result in duplicate notifications being dispatched to users.
   
> __Missing Message Delivery Confirmation__:  If there is no acknowledgement mechanism in place, say, it's an asynchronous system, sending the same messages again is highly possible.

> __Database Transaction Failures__: Should the database transaction fail after the scheduler marks the announcement as sent, but before it's actually sent, the scheduler will attempt to send the announcement again, resulting in duplicate notifications.
 
> __Inconsistent Message Queue Processing__: If the message queue processing mechanism is not robust, it might process the same announcement multiple times due to message processing failures or retries.

## Propose An Architecture That Could Fix This Problem
> __Event Sourcing Architecture__: Implement an event-driven architecture where announcements are stored as events in a log. Consumers process these events and send notifications. This ensures that each announcement is processed exactly once.
Elaboration: Events are immutable and appended to the log. Consumers maintain their state and process events sequentially, guaranteeing exactly-once processing.
> Another way could be to simply use a cloud service like AWS EventBridge, with your Event Busses that have rules containing your lambda functions, this could be appropriate especially if there are times whereby there would be a huge amount of messages that get sent out to employees or lots of messages that get sent out to a large number of people. 

> By using cloud providers like AWS, we'd be able to leverage on it's elasticity based on the high volumes needed. And be able to continue when we don't need such high volumes without having to change any infrastructural setup.


## Project Structure

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

## Introduction

>Eyo Halla At Me Systems is a simple FastAPI application that allows sending announcements. This README provides instructions on how to set up and run the project using Docker.

## Prerequisites

- Docker installed on your machine. You can download and install Docker from [here](https://docs.docker.com/get-docker/).

## Getting Started

1. Clone this repository to your local machine:

    ```bash
    git clone git@github.com:tzone85/announcements.git
    cd announcements
    ```

2. Build the Docker images for the application and Nginx server:

    ```bash
    docker build -t announcement-systems .
    docker build -t nginx-server ./nginx
    ```

3. Run the Docker containers:

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
