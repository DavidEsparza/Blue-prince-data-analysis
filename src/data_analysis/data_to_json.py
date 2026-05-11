from fetch_data import get_player_runs_data, get_all_rooms_data
import pandas as pd
import numpy as np
from pathlib import Path
import json

ROOM_COLORS = [
    "bedroom",
    "blueprint",
    "blackprint",
    "blueprint",
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


def join_runs_and_rooms(runs, rooms):
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
    df = (
        df_exploded.merge(df_rooms, on="room_number", how="left")
        .explode("type")
        .reset_index(drop=True)
    )

    return df, df_exploded


def generate_room_distribution_json(
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


def main():

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Get run data of a specific player
    runs = get_player_runs_data(9)
    rooms = get_all_rooms_data()

    # Join runs and rooms meta-data
    df, df_without_types = join_runs_and_rooms(runs, rooms)

    # Get the day when reached room 46 and separate and mask for filter data
    rank_10_days = df.loc[df["rank_reached"].eq(10), "day"]
    if rank_10_days.empty:
        raise ValueError("No row with rank_reached == 10 found.")

    goal_reached_day = rank_10_days.iloc[0]

    pre_win_df = df[df["day"].le(goal_reached_day)]
    pre_win_df_without_types = df_without_types[
        df_without_types["day"].le(goal_reached_day)
    ]

    # generate_room_distribution_json(
    #     pre_win_df,
    #     pre_win_df_without_types,
    #     file_name="pre_win_room_color_distribution.json",
    # )
    # generate_room_distribution_json(df, df_without_types)


if __name__ == "__main__":
    main()
