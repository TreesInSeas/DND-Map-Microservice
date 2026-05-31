from pathlib import Path

import requests
from PIL import Image

BASE_URL = "http://127.0.0.1:5002"
SAMPLE_IMAGE = Path("sample_map.png")


def create_sample_image():
    """Create a tiny valid PNG image for upload testing."""
    if not SAMPLE_IMAGE.exists():
        image = Image.new("RGB", (100, 100), color="white")
        image.save(SAMPLE_IMAGE)


def test_upload_map():
    print("Testing POST /api/maps...")
    create_sample_image()

    with SAMPLE_IMAGE.open("rb") as file:
        response = requests.post(
            f"{BASE_URL}/api/maps",
            files={
                "map_file": (SAMPLE_IMAGE.name, file, "image/png")
            },
            data={
                "map_name": "Dungeon Level 1",
                "room_id": "room_1038"
            },
        )

    print(response.status_code)
    print(response.json())
    return response.json()


def test_get_map_by_id(map_id):
    print("\nTesting GET /api/maps/{map_id}...")
    response = requests.get(f"{BASE_URL}/api/maps/{map_id}")
    print(response.status_code)
    print(response.json())


def test_get_maps_in_room(room_id):
    print("\nTesting GET /api/rooms/{room_id}/maps...")
    response = requests.get(f"{BASE_URL}/api/rooms/{room_id}/maps")
    print(response.status_code)
    print(response.json())


def test_get_uploaded_image(map_url):
    print("\nTesting GET uploaded image...")
    response = requests.get(f"{BASE_URL}{map_url}")
    print(response.status_code)
    print(response.headers.get("content-type"))
    print(f"Received {len(response.content)} bytes")


if __name__ == "__main__":
    upload_result = test_upload_map()

    if upload_result.get("success"):
        test_get_map_by_id(upload_result["map_id"])
        test_get_maps_in_room(upload_result["room_id"])
        test_get_uploaded_image(upload_result["map_url"])
    else:
        print("Upload failed, so follow-up tests were skipped.")
