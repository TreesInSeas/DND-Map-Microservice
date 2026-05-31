from io import BytesIO
import sqlite3
import uuid

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse, StreamingResponse
from PIL import Image, UnidentifiedImageError
import uvicorn

app = FastAPI(title="DND Map Microservice")

DATABASE_NAME = "maps.db"
ALLOWED_IMAGE_FORMATS = {"PNG", "JPEG", "WEBP"}

FORMAT_TO_EXTENSION = {
    "PNG": "png",
    "JPEG": "jpg",
    "WEBP": "webp",
}

FORMAT_TO_MIME_TYPE = {
    "PNG": "image/png",
    "JPEG": "image/jpeg",
    "WEBP": "image/webp",
}


def get_connection():
    """Create a new SQLite connection for each request."""
    return sqlite3.connect(DATABASE_NAME)


def init_database():
    """Create the maps table and add missing columns for older databases."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS maps (
                id TEXT PRIMARY KEY NOT NULL,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                room_id TEXT,
                data BLOB NOT NULL,
                mime_type TEXT NOT NULL DEFAULT 'application/octet-stream'
            )
        """)

        cursor.execute("PRAGMA table_info(maps)")
        existing_columns = {column[1] for column in cursor.fetchall()}

        if "mime_type" not in existing_columns:
            cursor.execute(
                "ALTER TABLE maps ADD COLUMN mime_type TEXT NOT NULL DEFAULT 'application/octet-stream'"
            )

        conn.commit()


def error_response(message: str, status_code: int = 400):
    """Return errors in the JSON shape expected by the main program."""
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": message
        },
    )


def validate_image_file(file_bytes: bytes):
    """
    Verify that the uploaded bytes are a safe supported image type.
    Returns the detected image format, extension, and MIME type.
    """
    if not file_bytes:
        return None, "Uploaded file is empty."

    try:
        image = Image.open(BytesIO(file_bytes))
        image.verify()
    except (UnidentifiedImageError, OSError):
        return None, "Invalid image file."

    image_format = image.format

    if image_format not in ALLOWED_IMAGE_FORMATS:
        return None, "Invalid file type. Only png, jpg, jpeg, and webp files are allowed."

    return {
        "format": image_format,
        "extension": FORMAT_TO_EXTENSION[image_format],
        "mime_type": FORMAT_TO_MIME_TYPE[image_format],
    }, None


def save_map_record(
    map_id: str,
    map_name: str,
    map_url: str,
    room_id: str | None,
    image_bytes: bytes,
    mime_type: str
):
    """Save one uploaded map record to the SQLite database."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO maps (id, name, url, room_id, data, mime_type)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (map_id, map_name, map_url, room_id, image_bytes, mime_type))
        conn.commit()


@app.on_event("startup")
def startup_event():
    init_database()


@app.post("/api/maps")
async def add_map(
    map_file: UploadFile = File(...),
    map_name: str = Form(...),
    room_id: str | None = Form(None),
):
    """
    Upload a battle map using multipart/form-data.
    Required form fields: map_file, map_name
    Optional form field: room_id
    """
    if not map_name.strip():
        return error_response("map_name is required.")

    image_bytes = await map_file.read()

    image_info, validation_error = validate_image_file(image_bytes)
    if validation_error:
        return error_response(validation_error)

    map_id = f"map_{uuid.uuid4()}"
    map_url = f"/uploads/{map_id}.{image_info['extension']}"

    save_map_record(
        map_id=map_id,
        map_name=map_name.strip(),
        map_url=map_url,
        room_id=room_id,
        image_bytes=image_bytes,
        mime_type=image_info["mime_type"],
    )

    return {
        "success": True,
        "map_id": map_id,
        "map_name": map_name.strip(),
        "map_url": map_url,
        "room_id": room_id,
    }


@app.get("/api/maps/{map_id}")
async def get_map_data(map_id: str):
    """Return map metadata for one map ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, url, room_id FROM maps WHERE id = ?",
            (map_id,)
        )
        result = cursor.fetchone()

    if result is None:
        return error_response("Map not found.", status_code=404)

    return {
        "success": True,
        "map_id": result[0],
        "map_name": result[1],
        "map_url": result[2],
        "room_id": result[3],
    }


@app.get("/api/rooms/{room_id}/maps")
async def get_maps_in_room(room_id: str):
    """Return all map metadata records connected to one room ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, url, room_id FROM maps WHERE room_id = ?",
            (room_id,)
        )
        results = cursor.fetchall()

    maps = [
        {
            "map_id": result[0],
            "map_name": result[1],
            "map_url": result[2],
            "room_id": result[3],
        }
        for result in results
    ]

    return {
        "success": True,
        "maps": maps
    }


@app.get("/uploads/{map_filename}")
async def get_map(map_filename: str):
    """Return the original uploaded image bytes for a saved map."""
    map_url = f"/uploads/{map_filename}"

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT data, mime_type FROM maps WHERE url = ?",
            (map_url,)
        )
        result = cursor.fetchone()

    if result is None:
        return error_response("Map not found.", status_code=404)

    image_bytes, mime_type = result
    return StreamingResponse(BytesIO(image_bytes), media_type=mime_type)


if __name__ == "__main__":
    init_database()
    uvicorn.run(app, host="0.0.0.0", port=5002)
