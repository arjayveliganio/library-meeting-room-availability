import os, json
import azure.functions as func
from azure.cosmos import CosmosClient

def _container():
    conn = os.environ["COSMOS_CONNECTION_STRING"]
    db_name = os.environ.get("COSMOS_DB_NAME", "librarydb")
    c_name = os.environ.get("COSMOS_CONTAINER_NAME", "bookings")
    client = CosmosClient.from_connection_string(conn)
    return client.get_database_client(db_name).get_container_client(c_name)

def main(req: func.HttpRequest) -> func.HttpResponse:
    booking_id = req.route_params.get("id")
    if not booking_id or "__" not in booking_id:
        return func.HttpResponse("Invalid booking id", status_code=400)

    # id format: YYYY-MM-DD__ROOM-X__HH:MM-HH:MM
    date = booking_id.split("__", 1)[0]

    container = _container()
    try:
        container.delete_item(item=booking_id, partition_key=date)
    except Exception as e:
        # Keep it simple for the assignment
        return func.HttpResponse("Booking not found (or already deleted).", status_code=404)

    return func.HttpResponse(json.dumps({"deleted": booking_id}), mimetype="application/json", status_code=200)
