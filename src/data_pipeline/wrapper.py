from db_manager import query_db


def get_rooms():
    """Return room ids and labels for UI select boxes."""
    rooms = query_db("SELECT number, title FROM rooms ORDER BY number")
    room_ids = [0]
    room_labels = {0: ""}
    for room_number, room_title in rooms:
        room_ids.append(room_number)
        room_labels[room_number] = room_title
    return room_ids, room_labels
