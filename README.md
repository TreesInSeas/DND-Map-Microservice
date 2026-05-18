# DND Map Microservice

This microservice allows a DND game to upload and retrieve battle maps through a REST API.


## Features

- Upload battle maps
- Retrieve map data using a map ID
- Retrieve all maps connected to a room
- Returns JSON responses
- Supports png, jpg, jpeg, and webp image files

## Install

pip install -r requirements.txt

## Run

python main.py

The service runs at:

http://127.0.0.1:5002

## Endpoints

### POST /api/maps

Uploads a battle map.

Request body:

```json
{
  "map_file": "map image",
  "map_name": "Dungeon Level 1",
  "room_id": "room_1038"
}
```

Success response:

```json
{
  "success": true,
  "map_id": "map_2041",
  "map_name": "Dungeon Level 1",
  "map_url": "/uploads/map_2041.png",
  "room_id": "room_1038"
}
```

### GET /api/maps/{map_id}

Returns map information for the provided map ID.

Example request:

```python
import requests

response = requests.get(
    "http://127.0.0.1:5002/api/maps/test-map-id"
)

print(response.json())
```

### GET /api/rooms/{room_id}/maps

Returns all maps connected to the provided room ID.

Example request:

```python
import requests

response = requests.get(
    "http://127.0.0.1:5002/api/rooms/test-room-id/maps"
)

print(response.json())
```

Example response:

```json
{
  "success": true,
  "maps": []
}
```

## Test

python client_example.py
