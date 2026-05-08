from db_manager import query_db, save_to_db


def get_rooms():
    rooms = query_db("SELECT number, title FROM rooms ORDER BY number")
    room_ids = [0]
    room_labels = {0: ""}
    for room_number, room_title in rooms:
        room_ids.append(room_number)
        room_labels[room_number] = room_title
    return room_ids, room_labels


def save_info_to_db(table, data):
    return save_to_db(table, data)
