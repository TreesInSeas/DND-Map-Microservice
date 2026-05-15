import fastapi
from fastapi import Request
from fastapi.responses import StreamingResponse
import uvicorn
import PIL
import sqlite3
import uuid
from io import BytesIO

app = fastapi.FastAPI()
conn = sqlite3.connect('maps.db')
cursor = conn.cursor()


@app.post("/api/maps")
async def add_map(request: Request):
    # get data from request body
    data = await request.json()
    map_file = data.get("map_file")
    map_name = data.get("map_name")
    room_id = data.get("room_id")

    # validate the input
    if not map_file or not map_name:
        return {"success": False, "error": "map_file and map_name are required."}
    img = PIL.Image.open(map_file)
    if img.format not in ["PNG", "JPEG", "WEBP"]:
        return {"success": False, "error": "Invalid file type. Only png, jpg, jpeg, and webp files are allowed."}
    if img.verify() is not None:
        return {"success": False, "error": "Invalid image file."}
    
    # genrate a unique map ID and URL
    map_id = f"map_{str(uuid.uuid4())}"
    map_url = f"/uploads/{map_id}.{img.format.lower()}"

    # save to database
    cursor.execute('''
        INSERT INTO maps (id, name, url, room_id, data)
        VALUES (?, ?, ?, ?, ?)
    ''', (map_id, map_name, map_url, room_id, img.tobytes()))
    conn.commit()

    # return all data
    return {
        "success": True,
        "map_id": map_id,
        "map_name": map_name,
        "map_url": map_url,
        "room_id": room_id
        }

@app.get("/api/maps/{map_id}")
async def get_map_data(map_id: str):
    # returns the map name, map ID, room_id, and map URL for the map with the matching map ID
    pass

@app.get("/api/rooms/{room_id}/maps")
async def get_maps_in_room(room_id: str):
    # returns an array of all maps with matching room ID
    # each map in the array should include the map name, map ID, room_id, and map URL
    pass

@app.get('/uploads/{map_filename}')
async def get_map(map_filename: str):
    # query the database for the map data, searching via map filename
    cursor.execute('SELECT data FROM maps WHERE url = ?', (f"/uploads/{map_filename}",))
    result = cursor.fetchone()

    # if no map is found, return an error message
    if result is None:
        return {"success": False, "error": "Map not found."}
    
    # return the map data as a streaming response with the correct MIME type
    image_data = BytesIO(result[0])
    data_mime_type = f"image/{map_filename.split('.')[-1]}"
    return StreamingResponse(image_data, media_type=data_mime_type)


if __name__ == "__main__":
    # create maps table if it doesn't aleady exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS maps (
            id TEXT PRIMARY KEY NOT NULL,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            room_id TEXT,
            data BLOB NOT NULL
        )
    ''')
    uvicorn.run(app, host="0.0.0.0", port=5002)
