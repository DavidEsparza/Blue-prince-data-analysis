# This script collects room data from the Blue Prince Wiki and saves it to a SQLite database.
# Run it once to populate the data base

import json
import re

from urllib.parse import urlencode
from urllib.request import Request, urlopen
from db_manager import initialize_db, save_rooms_to_db

BASE_URL = "https://blueprince.wiki.gg/api.php"

QUERY_PARAMS_ROOMS = {
    "action": "query",
    "prop": "revisions",
    "rvprop": "content",
    "rvslots": "main",
    "formatversion": "2",
    "format": "json",
}

QUERY_PARAMS = {
    "action": "query",
    "list": "categorymembers",
    "cmtitle": "Category:Rooms#Show_all_room_spoilers-0",
    "format": "json",
    "cmlimit": "150",
}


TYPES = [
    "Blueprint",
    "Objective",
    "Red Room",
    "Green Room",
    "Hallway",
    "Bedroom",
    "Shop",
    "Blackprint",
    "Dead End",
    "Entry",
    "Puzzle",
    "Mechanical",
    "Outer Room",
    "Addition",
    "Drafting",
    "Tomorrow",
    "Spread",
    "Permanent",
]


def extract_template_block(text, template_name):
    start_token = "{{" + template_name
    start = text.find(start_token)
    if start == -1:
        return ""

    depth = 0
    i = start
    while i < len(text) - 1:
        pair = text[i : i + 2]
        if pair == "{{":
            depth += 1
            i += 2
            continue
        if pair == "}}":
            depth -= 1
            i += 2
            if depth == 0:
                return text[start:i]
            continue
        i += 1

    return ""


def parse_infobox_fields(infobox_text):
    fields = {}
    for line in infobox_text.splitlines():
        if not line.startswith("|"):
            continue
        if "=" not in line:
            continue
        key, value = line[1:].split("=", 1)
        fields[key.strip()] = value.strip()
    return fields


def parse_gem_cost(value):
    if not value:
        return 0
    match = re.search(r"-?\d+", value)
    return int(match.group(0)) if match else 0


def get_revision_content(page):
    revisions = page.get("revisions", [])
    if not revisions:
        return ""

    revision = revisions[0]

    # Supports both deprecated legacy output and modern slot-based output.
    if "*" in revision:
        return revision["*"]

    slots = revision.get("slots", {})
    main_slot = slots.get("main", {})
    return main_slot.get("content", main_slot.get("*", ""))


def extract_room_info(page_title, wikitext):
    infobox = extract_template_block(wikitext, "RoomInfobox")
    if not infobox:
        return None

    fields = parse_infobox_fields(infobox)
    room_types = [
        part.strip().strip('"')
        for part in fields.get("Type", "").split(",")
        if part.strip()
    ]

    return {
        "number": fields.get("Number", ""),
        "title": fields.get("title", page_title),
        "image": fields.get("image", ""),
        "description": fields.get("Description", ""),
        "gem_cost": parse_gem_cost(fields.get("Gem Cost", "0")),
        "type": room_types,
        "rarity": fields.get("Rarity", ""),
        "shape": fields.get("Shape", "Outer Room"),
    }


def fetch_json(base_url, params):
    query = urlencode(params)
    url = f"{base_url}?{query}"
    request = Request(
        url,
        headers={
            "User-Agent": "BluePrinceDataCollector/1.0 (david.fernando.esp@gmail.com) requests/2.28.2",
        },
    )
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def populate_rooms():
    data = fetch_json(BASE_URL, QUERY_PARAMS)
    rooms = [
        member["title"].replace(" ", "_")
        for member in data["query"]["categorymembers"]
        if not member["title"].startswith("Category:")
    ]
    extracted_rooms = []
    for room in rooms:
        room_params = QUERY_PARAMS_ROOMS.copy()
        room_params["titles"] = room

        room_data = fetch_json(BASE_URL, room_params)
        for page in room_data.get("query", {}).get("pages", []):
            title = page.get("title", room)
            wikitext = get_revision_content(page)
            if not wikitext:
                continue

            room_info = extract_room_info(title, wikitext)
            if room_info:
                extracted_rooms.append(room_info)
                save_rooms_to_db(room_info)


def main():
    initialize_db()
    populate_rooms()


if __name__ == "__main__":
    main()
