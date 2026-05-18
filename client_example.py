import requests
print("Testing get map by ID...")
response = requests.get("http://127.0.0.1:5002/api/maps/test-map-id")

print(response.json())
print("\nTesting get maps in room...")

response = requests.get("http://127.0.0.1:5002/api/rooms/test-room-id/maps")
print(response.json())
