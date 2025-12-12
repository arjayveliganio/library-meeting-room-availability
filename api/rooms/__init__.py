import os, json
import azure.functions as func
from azure.cosmos import CosmosClient

ROOMS = ["ROOM-A", "ROOM-B", "ROOM-C", "ROOM-D", "ROOM-E"]
SLOTS = ["09:00-10:00", "10:00-11:00", "11:00-12:00", "13:00-14:00", "14:00-15:00", "15:00-16:00"]

def _container():
    conn = os.environ["COSMOS_CONNECTION_STRING"]
    db_name = os.environ.get("COSMOS_DB_NAME", "librarydb")
    c_name = os.environ.get("COSMOS_CONTAINER_NAME", "bookings")
    client = CosmosClient.from_connection_string(conn)
    return client.get_database_client(db_name).get_container_client(c_name)

def main(req: func.HttpRequest) -> func.HttpResponse:
    date = req.params.get("date")
    if not date:
        return func.HttpResponse("Missing required query param: date", status_code=400)

    container = _container()

    query = "SELECT c.roomId, c.slot, c.id, c.name, c.email FROM c WHERE c.date = @date"
    items = list(container.query_items(
        query=query,
        parameters=[{"name": "@date", "value": date}],
        enable_cross_partition_query=False
    ))

    taken = {room: set() for room in ROOMS}
    bookings = []
    for it in items:
        taken[it["roomId"]].add(it["slot"])
        bookings.append(it)

    availability = []
    for room in ROOMS:
        availability.append({
            "roomId": room,
            "slots": [{"slot": s, "status": "booked" if s in taken[room] else "available"} for s in SLOTS]
        })

    return func.HttpResponse(
        json.dumps({"date": date, "rooms": availability, "bookings": bookings}),
        mimetype="application/json",
        status_code=200
    )
