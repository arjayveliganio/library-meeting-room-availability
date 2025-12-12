import os, json
from datetime import datetime, timezone
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
    try:
        body = req.get_json()
    except Exception:
        return func.HttpResponse("Invalid JSON body", status_code=400)

    date = (body.get("date") or "").strip()
    room_id = (body.get("roomId") or "").strip().upper()
    slot = (body.get("slot") or "").replace(" ", "")  # handles "15:00 - 16:00"
    name = (body.get("name") or "").strip()
    email = (body.get("email") or "").strip()

    if not (date and room_id and slot and name and email):
        return func.HttpResponse("Required fields: date, roomId, slot, name, email", status_code=400)
    if room_id not in ROOMS:
        return func.HttpResponse("Invalid roomId", status_code=400)
    if slot not in SLOTS:
        return func.HttpResponse("Invalid slot format. Use e.g. 15:00-16:00", status_code=400)

    container = _container()

    conflict_q = "SELECT VALUE COUNT(1) FROM c WHERE c.date=@date AND c.roomId=@roomId AND c.slot=@slot"
    conflict = list(container.query_items(
        query=conflict_q,
        parameters=[
            {"name": "@date", "value": date},
            {"name": "@roomId", "value": room_id},
            {"name": "@slot", "value": slot},
        ],
        enable_cross_partition_query=False
    ))[0]

    if conflict > 0:
        return func.HttpResponse("That room/slot is already booked.", status_code=409)

    booking_id = f"{date}__{room_id}__{slot}"  # lets us parse date for deletes
    doc = {
        "id": booking_id,
        "date": date,
        "roomId": room_id,
        "slot": slot,
        "name": name,
        "email": email,
        "createdAt": datetime.now(timezone.utc).isoformat()
    }

    container.create_item(body=doc)
    return func.HttpResponse(json.dumps(doc), mimetype="application/json", status_code=201)
