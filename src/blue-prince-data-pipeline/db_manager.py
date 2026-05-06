import sqlite3
import pickle
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "blue-prince-data.db"


def initialize_db():
    """Runs only once to ensure the database schema exists."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS rooms (    
                    number INTEGER PRIMARY KEY,
                    title TEXT, 
                    image TEXT, 
                    description TEXT,
                    gem_cost INTEGER, 
                    type INTEGER,
                    rarity TEXT, 
                    shape TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS players
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mode TEXT,
                    west_gate_unlock_day INTEGER,
                    gemstone_cavern_unlock_day INTEGER,
                    apple_orchard_unlock_day INTEGER,
                    blackbridge_unlock_day INTEGER,
                    satelite_dish_unlock_day INTEGER,
                    name TEXT UNIQUE)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS types
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS room_types
                    (room INTEGER,
                    type INTEGER,
                    FOREIGN KEY(room) REFERENCES rooms(number),
                    FOREIGN KEY(type) REFERENCES types(id),
                    PRIMARY KEY(room, type))""")
    conn.execute("""CREATE TABLE IF NOT EXISTS days
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player INTEGER,
                    day INTEGER,
                    steps_taken INTEGER,
                    items INTEGER, 
                    new_rooms INTEGER, 
                    outer_room INTEGER,
                    current_allowance INTEGER,
                    current_stars INTEGER,
                    FOREIGN KEY(outer_room) REFERENCES rooms(number),
                    FOREIGN KEY(player) REFERENCES players(name))""")
    conn.execute("""CREATE TABLE IF NOT EXISTS mansion
                    (
                    day INTEGER,
                    room INTEGER,
                    position_x INTEGER,
                    position_y INTEGER,
                    FOREIGN KEY(day) REFERENCES days(id),
                    FOREIGN KEY(room) REFERENCES rooms(number),
                    PRIMARY KEY(day, position_x, position_y))""")
    conn.commit()
    conn.close()


def save_rooms_to_db(room_info):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR REPLACE INTO rooms VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            room_info["title"],
            room_info["number"],
            room_info["image"],
            room_info["description"],
            room_info["gem_cost"],
            room_info["rarity"],
            room_info["shape"],
        ),
    )
    for room_type in room_info["type"]:
        conn.execute(
            "INSERT OR IGNORE INTO room_types VALUES (?, ?)",
            (room_info["number"], room_type),
        )

    conn.commit()
    conn.close()


def get_from_db(title):
    conn = sqlite3.connect(DB_PATH)
    result = conn.execute("SELECT * FROM rooms WHERE title=?", (title,)).fetchone()
    conn.close()
    if result:
        result = dict(
            zip(
                [
                    "title",
                    "number",
                    "image",
                    "description",
                    "gem_cost",
                    "type",
                    "rarity",
                    "shape",
                ],
                result,
            )
        )
        result["type"] = pickle.loads(result["type"])
    print(result)
    return result
