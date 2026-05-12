from fetch_data import get_player_runs_data, get_all_rooms_data
import pandas as pd
import numpy as np
from pathlib import Path
import json

ROOM_COLORS = [
    "bedroom",
    "blueprint",
    "blackprint",
    "green room",
    "hallway",
    "red room",
    "shop",
]

PRELOADED_ROOMS = [
    "Antechamber",
    "Entrance Hall",
]

OUTPUT_DIR = Path(__file__).resolve().parents[2] / "data"


def normalize_run_room_data(runs, rooms):
    """Join runs and rooms meta-data."""
    df_runs = pd.DataFrame(
        runs,
        columns=[
            "day",
            "steps_taken",
            "items",
            "new_rooms",
            "rank_reached",
            "outer_room",
            "rooms_in_mansion",
            "mansion",
        ],
    )

    df_runs["outer_room"] = df_runs["outer_room"].fillna("None")
    # Split and explode list of rooms in mansions
    df_runs["room_list"] = df_runs["mansion"].str.split(";")
    df_runs.drop("mansion", axis=1, inplace=True)
    df_exploded = df_runs.explode("room_list")

    # Split and explode room position and name into separate columns
    room_details = df_exploded["room_list"].str.split(",", expand=True)
    df_exploded.drop("room_list", axis=1, inplace=True)
    df_exploded["room_number"] = room_details[0].astype(int)
    df_exploded["room_name"] = room_details[1]
    df_exploded["pos_x"] = room_details[2].astype(int)
    df_exploded["pos_y"] = room_details[3].astype(int)

    # Get all rooms meta-data
    df_rooms = pd.DataFrame(
        rooms, columns=["room_number", "title", "gem_cost", "rarity", "shape", "type"]
    )
    df_rooms["type"] = df_rooms["type"].str.split(",")

    # Merge runs and rooms meta-data
    df_exploded = df_exploded.merge(df_rooms, on="room_number", how="left")
    df = df_exploded.explode("type").reset_index(drop=True)
    return df, df_exploded


def save_room_distribution(
    df, df_without_types, file_name="room_color_distribution.json"
):
    """Generate JSON files with room distribution data."""
    color_distibution = {}

    color_counts = (
        df_without_types.groupby(["pos_x", "pos_y"]).size().reset_index(name="count")
    )

    color_distibution["all"] = color_counts.to_dict(orient="records")

    for color in ROOM_COLORS:
        color_counts = (
            df[df["type"] == color]
            .groupby(["pos_x", "pos_y"])
            .size()
            .reset_index(name="count")
        )
        color_distibution[color] = color_counts.to_dict(orient="records")

    pd.Series(color_distibution).to_json(OUTPUT_DIR / file_name)
    with open(OUTPUT_DIR / file_name, "w", encoding="utf-8") as f:
        json.dump(color_distibution, f, indent=2, ensure_ascii=False, sort_keys=True)


def save_color_progression_by_day(df, file_name="cumulative_room_quantity_by_day.json"):
    """Generate JSON files with room cumulative quantity by day data."""
    daily_counts = df.groupby(["day", "type"]).size().reset_index(name="count")
    type_pivot = daily_counts.pivot(index="day", columns="type", values="count")
    type_pivot = type_pivot.reindex(columns=ROOM_COLORS).fillna(0)
    df_cumulative_types = type_pivot.cumsum()
    df_cumulative_types = df_cumulative_types.astype(int)
    json_output = df_cumulative_types.to_dict(orient="list")
    with open(OUTPUT_DIR / file_name, "w", encoding="utf-8") as f:
        json.dump(json_output, f, indent=2, ensure_ascii=False, sort_keys=True)


def save_room_count(df, max_rank=False, file_name="room_quantity.json"):
    """Generate JSON with room quantity data."""
    room_counts = (
        df[~df["room_name"].isin(PRELOADED_ROOMS)]
        .groupby("room_name")
        .agg(
            count=("room_name", "size"),
            cost=("gem_cost", "first"),
            rarity=("rarity", "first"),
            shape=("shape", "first"),
            max_rank_reached=("rank_reached", "max"),
        )
        .sort_values(by="count", ascending=False)
        .reset_index()
    )
    json_output = room_counts.to_dict(orient="records")
    with open(OUTPUT_DIR / file_name, "w", encoding="utf-8") as f:
        json.dump(json_output, f, indent=2, ensure_ascii=False, sort_keys=True)


def save_outer_room_stats(df, file_name="outer_room_stats.json"):
    """Generate JSON with outer room stats data."""
    outer_room_statistics = (
        df.groupby("day")
        .agg(
            outer_room=("outer_room", "first"),
            items=("items", "first"),
            rooms_in_mansion=("rooms_in_mansion", "first"),
            rank_reached=("rank_reached", "first"),
        )
        .groupby("outer_room")
        .agg(
            count=("rooms_in_mansion", "size"),
            mean_items=("items", "mean"),
            mean_rank_reached=("rank_reached", "mean"),
            mean_rooms_in_mansion=("rooms_in_mansion", "mean"),
        )
        .sort_values(by="count", ascending=False)
        .reset_index()
    )
    json_output = outer_room_statistics.to_dict(orient="records")
    with open(OUTPUT_DIR / file_name, "w", encoding="utf-8") as f:
        json.dump(json_output, f, indent=2, ensure_ascii=False, sort_keys=True)


def save_shape_placement(df, file_name="room_shape_distribution.json"):
    """Generate JSON with room distribution by shapedata."""
    shape_types = df["shape"].unique()
    shape_distibution = {}
    for shape_type in shape_types:
        if shape_type == "Special":
            continue
        shape_counts = (
            df[df["shape"] == shape_type]
            .groupby(["pos_x", "pos_y"])
            .size()
            .reset_index(name="count")
        )
        shape_distibution[shape_type] = shape_counts.to_dict(orient="records")

    with open(OUTPUT_DIR / file_name, "w", encoding="utf-8") as f:
        json.dump(shape_distibution, f, indent=2, ensure_ascii=False, sort_keys=True)

    # json_output = shape_distribution.to_dict(orient="records")
    # with open(OUTPUT_DIR / file_name, "w", encoding="utf-8") as f:
    #     json.dump(json_output, f, indent=2, ensure_ascii=False, sort_keys=True)


def save_stats_on_tomorrow_rooms(df, file_name="stats_on_tomorrow_rooms.json"):
    """Generate JSON with stats on tomorrow rooms data."""
    # Format data for stats on tomorrow rooms, excluding aquarim since it does not affect the next day
    daily_stats_shifted = (
        df[(df["room_name"] != "Aquarium")]
        .groupby("day")
        .agg(
            number_of_tomorrow_rooms=("type", lambda x: (x == "tomorrow").sum()),
            rank_reached=("rank_reached", "first"),
            rooms_in_mansion=("rooms_in_mansion", "first"),
            items=("items", "first"),
            steps_taken=("steps_taken", "first"),
        )
        .reset_index()
    )

    # Shift stats to the next day to align with the number of tomorrow rooms
    daily_stats_shifted["rank_reached"] = daily_stats_shifted["rank_reached"].shift(-1)
    daily_stats_shifted["rooms_in_mansion"] = daily_stats_shifted[
        "rooms_in_mansion"
    ].shift(-1)
    daily_stats_shifted["items"] = daily_stats_shifted["items"].shift(-1)
    daily_stats_shifted["steps_taken"] = daily_stats_shifted["steps_taken"].shift(-1)
    daily_stats_shifted = daily_stats_shifted.iloc[:-1]
    tomorrow_room_impact = (
        daily_stats_shifted.groupby("number_of_tomorrow_rooms")
        .mean()
        .drop("day", axis=1)
    )
    tomorrow_room_impact.to_json(OUTPUT_DIR / file_name)
    with open(OUTPUT_DIR / file_name, "w", encoding="utf-8") as f:
        json.dump(
            tomorrow_room_impact.to_dict(),
            f,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )


def main():

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Get run data of a specific player
    runs = get_player_runs_data(9)
    rooms = get_all_rooms_data()

    # Join runs and rooms meta-data
    df, df_without_types = normalize_run_room_data(runs, rooms)

    # Get the day when reached room 46 and separate and mask for filter data
    rank_10_days = df.loc[df["rank_reached"].eq(10), "day"]
    if rank_10_days.empty:
        raise ValueError("No row with rank_reached == 10 found.")

    goal_reached_day = rank_10_days.iloc[0]

    # Pre-win data
    pre_win_df = df[df["day"].le(goal_reached_day)]
    pre_win_df_without_types = df_without_types[
        df_without_types["day"].le(goal_reached_day)
    ]

    # ------------------------------------------------------------------------------

    # How often was a room with shaped placed in each location of the mansion before reaching rank 10
    save_shape_placement(
        pre_win_df_without_types, file_name="pre_win_room_shape_distribution.json"
    )
    # How often was a room with shaped placed in each location of the mansion
    save_shape_placement(df_without_types, file_name="room_shape_distribution.json")

    # Statistics on performance based on outer room
    save_outer_room_stats(df_without_types)
    # Statistics on performance based on outer room before reaching rank 10
    save_outer_room_stats(
        pre_win_df_without_types, file_name="pre_win_outer_room_stats.json"
    )

    # How many times a room was drafted in the mansion
    save_room_count(df_without_types, max_rank=False, file_name="room_quantity.json")
    # How many times a room was drafted in the mansion before reaching rank 10
    save_room_count(
        pre_win_df_without_types, max_rank=True, file_name="pre_win_room_quantity.json"
    )
    # How many times a room was drafted in a full mansion
    save_room_count(
        df[(df["type"].isin(ROOM_COLORS)) & (df["rooms_in_mansion"] == 45)],
        max_rank=False,
        file_name="room_quantity_on_full_mansion.json",
    )

    # How many times a color has been picked over time before reaching rank 10
    save_color_progression_by_day(pre_win_df[(pre_win_df["type"].isin(ROOM_COLORS))])
    # How many times a color has been picked over time
    save_color_progression_by_day(
        df[(df["type"].isin(ROOM_COLORS))],
        "pre_win_cumulative_room_quantity_by_day.json",
    )

    # How many times a color has been picked over time before reaching rank 10 excluding aquarium
    save_color_progression_by_day(
        pre_win_df[
            (pre_win_df["type"].isin(ROOM_COLORS))
            & ~(pre_win_df["room_name"] == "Aquarium")
        ],
        "pre_win_cumulative_room_quantity_by_day_without_aquarium.json",
    )

    # How many times a color has been picked over time excluding aquarium
    save_color_progression_by_day(
        df[(df["type"].isin(ROOM_COLORS)) & ~(df["room_name"] == "Aquarium")],
        "cumulative_room_quantity_by_day_without_aquarium.json",
    )

    # How often was a room type placed in each location of the mansion before reaching rank 10
    save_room_distribution(
        pre_win_df,
        pre_win_df_without_types,
        file_name="pre_win_room_color_distribution.json",
    )
    # How often was a room type placed in each location of the mansion
    save_room_distribution(df, df_without_types)

    # Statisctics on performance the next day based on tomorrow rooms of such day
    save_stats_on_tomorrow_rooms(df)


if __name__ == "__main__":
    main()
