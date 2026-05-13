import argparse
import sys
from fetch_data import get_player_runs_data, get_all_rooms_data
import pandas as pd
from save_to_json import OUTPUT_DIR, write_json, dataframe_to_json_payload

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

EXPORT_DETAILS = {
    "dead_ends_before_rank_4": {
        "label": "Dead Ends Before Rank 4",
        "description": "Grouped dead-end counts in deeper rows before progressing.",
    },
    "shelter_stats": {
        "label": "Shelter Comparison",
        "description": "Red-room performance with and without Shelter.",
    },
    "pre_win_shape_placement": {
        "label": "Pre-Win Shape Placement",
        "description": "Room-shape placement heatmap before rank 10.",
    },
    "shape_placement": {
        "label": "Shape Placement",
        "description": "Room-shape placement heatmap across all runs.",
    },
    "outer_room_stats": {
        "label": "Outer Room Stats",
        "description": "Performance averages grouped by outer room across all runs.",
    },
    "pre_win_outer_room_stats": {
        "label": "Pre-Win Outer Room Stats",
        "description": "Performance averages grouped by outer room before rank 10.",
    },
    "room_count": {
        "label": "Room Quantity",
        "description": "Draft frequency and metadata for all non-preloaded rooms.",
    },
    "pre_win_room_count": {
        "label": "Pre-Win Room Quantity",
        "description": "Room frequency before rank 10, including max rank reached.",
    },
    "full_mansion_room_count": {
        "label": "Full Mansion Room Quantity",
        "description": "Room frequency only for complete 45-room mansions.",
    },
    "pre_win_color_progression": {
        "label": "Pre-Win Color Progression",
        "description": "Cumulative room-color picks before rank 10.",
    },
    "color_progression": {
        "label": "Color Progression",
        "description": "Cumulative room-color picks across all runs.",
    },
    "pre_win_color_progression_without_aquarium": {
        "label": "Pre-Win Color Progression Without Aquarium",
        "description": "Pre-rank-10 cumulative colors excluding Aquarium.",
    },
    "color_progression_without_aquarium": {
        "label": "Color Progression Without Aquarium",
        "description": "All-run cumulative colors excluding Aquarium.",
    },
    "pre_win_room_distribution": {
        "label": "Pre-Win Room Distribution",
        "description": "Room-color placement heatmap before rank 10.",
    },
    "room_distribution": {
        "label": "Room Distribution",
        "description": "Room-color placement heatmap across all runs.",
    },
    "tomorrow_room_stats": {
        "label": "Tomorrow Room Impact",
        "description": "Next-day performance grouped by tomorrow-room count.",
    },
}


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
    """Save room placement density by color of rooms.

    Builds a position heatmap over the mansion grid using ``pos_x`` and ``pos_y``.
    The output contains one key named ``all`` with counts for all room regardless of type,
    plus one key per room color from ``ROOM_COLORS``.

    Args:
        df: Exploded run/room DataFrame that includes a ``type`` column.
        df_without_types: Room-placement DataFrame without type explosion.
        file_name: Target JSON filename in OUTPUT_DIR.
    """
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

    write_json(file_name, color_distibution)


def save_color_progression_by_day(df, file_name="cumulative_room_quantity_by_day.json"):
    """Save cumulative room-color picks over time.

    Aggregates daily counts by room ``type``, keeps only ``ROOM_COLORS`` in a fixed
    order, then computes a cumulative sum across days. The JSON payload maps each
    color to a list of cumulative totals aligned by day index.

    Args:
        df: DataFrame containing at least ``day`` and ``type`` columns.
        file_name: Target JSON filename in OUTPUT_DIR.
    """
    daily_counts = df.groupby(["day", "type"]).size().reset_index(name="count")
    type_pivot = daily_counts.pivot(index="day", columns="type", values="count")
    full_day_range = pd.RangeIndex(df["day"].min(), df["day"].max() + 1)
    type_pivot = type_pivot.reindex(index=full_day_range, columns=ROOM_COLORS).fillna(0)
    df_cumulative_types = type_pivot.cumsum()
    df_cumulative_types = df_cumulative_types.astype(int)
    write_json(file_name, dataframe_to_json_payload(df_cumulative_types, orient="list"))


def save_room_count(df, max_rank=False, file_name="room_quantity.json"):
    """Save room usage frequency and static room metadata.

    Excludes preloaded rooms and groups by ``room_name`` to compute draft count.
    Includes representative room metadata (cost, rarity, shape) and the maximum
    rank reached among runs where each room appears when requested.

    Args:
        df: DataFrame with room-level rows and room metadata columns.
        max_rank: Whether to include ``max_rank_reached`` in the output.
        file_name: Target JSON filename in OUTPUT_DIR.
    """
    agg_map = {
        "count": ("room_name", "size"),
        "cost": ("gem_cost", "first"),
        "rarity": ("rarity", "first"),
        "shape": ("shape", "first"),
    }
    if max_rank:
        agg_map["max_rank_reached"] = ("rank_reached", "max")

    room_counts = (
        df[~df["room_name"].isin(PRELOADED_ROOMS)]
        .groupby("room_name")
        .agg(**agg_map)
        .sort_values(by="count", ascending=False)
        .reset_index()
    )
    write_json(file_name, dataframe_to_json_payload(room_counts, orient="records"))


def save_outer_room_stats(df, file_name="outer_room_stats.json"):
    """Save run performance grouped by chosen outer room.

    First collapses rows to one record per day, then groups by ``outer_room`` to
    compute how frequently each outer room appears and average performance metrics
    (items, rank reached, mansion size).

    Args:
        df: DataFrame containing daily run information and ``outer_room``.
        file_name: Target JSON filename in OUTPUT_DIR.
    """
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
    write_json(
        file_name,
        dataframe_to_json_payload(
            outer_room_statistics,
            orient="records",
            round_digits=2,
        ),
    )


def save_shape_placement(df, file_name="room_shape_distribution.json"):
    """Save room placement density separated by room shape.

    For each non-``Special`` shape, counts how often that shape is placed at each
    mansion coordinate (``pos_x``, ``pos_y``). Output is a dictionary keyed by
    shape with ``[{pos_x, pos_y, count}, ...]`` entries.

    Args:
        df: DataFrame containing ``shape``, ``pos_x``, and ``pos_y``.
        file_name: Target JSON filename in OUTPUT_DIR.
    """
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

    write_json(file_name, shape_distibution)


def save_stats_on_tomorrow_rooms(df, file_name="stats_on_tomorrow_rooms.json"):
    """Save next-day performance impact by number of "tomorrow" rooms.

    Counts how many ``tomorrow`` room types were drafted on each day (excluding
    Aquariums), then shifts performance metrics by one day so the grouped
    averages represent next-day outcomes conditioned on today's tomorrow-room count.

    Args:
        df: DataFrame with ``day``, ``type``, and performance metric columns.
        file_name: Target JSON filename in OUTPUT_DIR.
    """

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
    write_json(
        file_name, dataframe_to_json_payload(tomorrow_room_impact, round_digits=2)
    )


def save_shelter_stats(df, file_name="shelter_stats.json"):
    """Compare red-room performance with and without selecting Shelter.

    Builds two cohorts (outer room is Shelter vs not Shelter), counts drafted red
    rooms per day (excluding Aquarium), and summarizes average outcomes for days
    with 4 to 7 drafted red rooms. Saves two lists under ``with_shelter`` and
    ``without_shelter``.

    Args:
        df: DataFrame with room type, outer room, and performance columns.
        file_name: Target JSON filename in OUTPUT_DIR.
    """
    aggregated_shelter_df = (
        df[
            (df["type"] == "red room")
            & (df["outer_room"] == "Shelter")
            & ~(df["room_name"] == "Aquarium")
        ]
        .groupby("day")
        .agg(
            count=("room_name", "size"),
            steps_taken=("steps_taken", "first"),
            rank_reached=("rank_reached", "first"),
            items=("items", "first"),
            rooms_in_mansion=("rooms_in_mansion", "first"),
        )
    )
    aggregated_no_shelter_df = (
        df[
            (df["type"] == "red room")
            & ~(df["outer_room"] == "Shelter")
            & ~(df["room_name"] == "Aquarium")
        ]
        .groupby("day")
        .agg(
            count=("room_name", "size"),
            steps_taken=("steps_taken", "first"),
            rank_reached=("rank_reached", "first"),
            items=("items", "first"),
            rooms_in_mansion=("rooms_in_mansion", "first"),
        )
    )
    shelter_stats = {}

    shelter_stats_by_red_room_count = (
        aggregated_shelter_df[
            (aggregated_shelter_df["count"] >= 4)
            & (aggregated_shelter_df["count"] <= 7)
        ]
        .groupby("count")
        .mean()
        .reset_index()
    )

    no_shelter_stats_by_red_room_count = (
        aggregated_no_shelter_df[
            (aggregated_no_shelter_df["count"] >= 4)
            & (aggregated_no_shelter_df["count"] <= 7)
        ]
        .groupby("count")
        .mean()
        .reset_index()
    )

    shelter_stats["with_shelter"] = shelter_stats_by_red_room_count.round(2).to_dict(
        orient="records"
    )
    shelter_stats["without_shelter"] = no_shelter_stats_by_red_room_count.round(
        2
    ).to_dict(orient="records")

    write_json(file_name, shelter_stats)


def save_dead_ends_before_rank_4(df, file_name="dead_ends_before_rank_3.json"):
    """Save grouped statistics for dead-end drafts in deeper mansion rows.

    Counts per-day drafts of ``Dead End`` shapes in rows ``pos_y >= 5``, fills in
    missing days with zero drafts, then groups consecutive 10-day windows to report
    mean count and actual day ranges for each batch.

    Args:
        df: DataFrame containing ``shape``, ``pos_y``, and ``day``.
        file_name: Target JSON filename in OUTPUT_DIR.
    """

    dead_ends_by_day = (
        df[(df["shape"] == "Dead End") & (df["pos_y"] >= 5)]
        .groupby("day")
        .size()
        .reset_index(name="count")
    )

    full_day_range = pd.RangeIndex(df["day"].min(), df["day"].max() + 1)
    dead_ends_before_rank_4 = (
        dead_ends_by_day.set_index("day")
        .reindex(full_day_range, fill_value=0)
        .rename_axis("day")
        .reset_index()
    )
    dead_ends_before_rank_4["group_id"] = (
        dead_ends_before_rank_4["day"] - dead_ends_before_rank_4["day"].min()
    ) // 10

    dead_ends_before_rank_4_grouped = (
        dead_ends_before_rank_4.groupby("group_id")
        .agg(
            mean=("count", "mean"),
            range=("day", lambda days: f"{days.min()}-{days.max()}"),
        )
        .reset_index(drop=True)
    )

    write_json(
        file_name,
        dataframe_to_json_payload(
            dead_ends_before_rank_4_grouped,
            orient="records",
            round_digits=2,
        ),
    )


def build_export_jobs(df, df_without_types, pre_win_df, pre_win_df_without_types):
    """Build the available export jobs keyed by a user-facing export name."""
    return {
        "dead_ends_before_rank_4": lambda: save_dead_ends_before_rank_4(
            df_without_types
        ),
        "shelter_stats": lambda: save_shelter_stats(df),
        "pre_win_shape_placement": lambda: save_shape_placement(
            pre_win_df_without_types,
            file_name="pre_win_room_shape_distribution.json",
        ),
        "shape_placement": lambda: save_shape_placement(
            df_without_types,
            file_name="room_shape_distribution.json",
        ),
        "outer_room_stats": lambda: save_outer_room_stats(df_without_types),
        "pre_win_outer_room_stats": lambda: save_outer_room_stats(
            pre_win_df_without_types,
            file_name="pre_win_outer_room_stats.json",
        ),
        "room_count": lambda: save_room_count(
            df_without_types,
            max_rank=False,
            file_name="room_quantity.json",
        ),
        "pre_win_room_count": lambda: save_room_count(
            pre_win_df_without_types,
            max_rank=True,
            file_name="pre_win_room_quantity.json",
        ),
        "full_mansion_room_count": lambda: save_room_count(
            df[(df["type"].isin(ROOM_COLORS)) & (df["rooms_in_mansion"] == 45)],
            max_rank=False,
            file_name="room_quantity_on_full_mansion.json",
        ),
        "pre_win_color_progression": lambda: save_color_progression_by_day(
            pre_win_df[(pre_win_df["type"].isin(ROOM_COLORS))],
            "pre_win_cumulative_room_quantity_by_day.json",
        ),
        "color_progression": lambda: save_color_progression_by_day(
            df[(df["type"].isin(ROOM_COLORS))],
            "cumulative_room_quantity_by_day.json",
        ),
        "pre_win_color_progression_without_aquarium": lambda: save_color_progression_by_day(
            pre_win_df[
                (pre_win_df["type"].isin(ROOM_COLORS))
                & ~(pre_win_df["room_name"] == "Aquarium")
            ],
            "pre_win_cumulative_room_quantity_by_day_without_aquarium.json",
        ),
        "color_progression_without_aquarium": lambda: save_color_progression_by_day(
            df[(df["type"].isin(ROOM_COLORS)) & ~(df["room_name"] == "Aquarium")],
            "cumulative_room_quantity_by_day_without_aquarium.json",
        ),
        "pre_win_room_distribution": lambda: save_room_distribution(
            pre_win_df,
            pre_win_df_without_types,
            file_name="pre_win_room_color_distribution.json",
        ),
        "room_distribution": lambda: save_room_distribution(df, df_without_types),
        "tomorrow_room_stats": lambda: save_stats_on_tomorrow_rooms(df),
    }


def parse_args():
    """Parse CLI arguments for export selection."""
    parser = argparse.ArgumentParser(
        description="Generate one or more Blue Prince analysis exports."
    )
    parser.add_argument(
        "--exports",
        nargs="+",
        metavar="EXPORT_NAME",
        help="Export names to generate, or 'all' to generate every export.",
    )
    parser.add_argument(
        "--list-exports",
        action="store_true",
        help="Print the available export names and exit.",
    )
    return parser.parse_args()


def display_export_options(export_jobs):
    """Print available exports with labels and descriptions."""
    for index, export_name in enumerate(export_jobs, start=1):
        export_detail = EXPORT_DETAILS[export_name]
        print(
            f"{index}. {export_detail['label']} ({export_name}) - "
            f"{export_detail['description']}"
        )
    print("all. Generate every export")


def normalize_export_selection(selection, export_jobs):
    """Normalize requested export names and validate them."""
    if not selection:
        return []

    export_names = list(export_jobs.keys())
    requested_exports = []
    for item in selection:
        requested_exports.extend(part.strip() for part in item.split(","))

    requested_exports = [item for item in requested_exports if item]
    if not requested_exports or "all" in requested_exports:
        return export_names

    normalized_exports = []
    for export_name in requested_exports:
        if export_name.isdigit():
            export_index = int(export_name) - 1
            if 0 <= export_index < len(export_names):
                normalized_exports.append(export_names[export_index])
                continue
        normalized_exports.append(export_name)

    invalid_exports = [name for name in normalized_exports if name not in export_jobs]
    if invalid_exports:
        available = ", ".join(export_jobs.keys())
        invalid = ", ".join(invalid_exports)
        raise ValueError(
            f"Unknown export selection: {invalid}. Available exports: {available}"
        )

    return normalized_exports


def prompt_for_exports(export_jobs):
    """Ask the user which exports to generate when running interactively."""
    print("Available exports:")
    display_export_options(export_jobs)

    selection = input(
        "Enter one or more numbers or export names separated by commas, or 'all': "
    )
    return normalize_export_selection([selection], export_jobs)


def run_export_jobs(selected_exports, export_jobs):
    """Run the selected export jobs in order."""
    for export_name in selected_exports:
        export_jobs[export_name]()


def main():
    args = parse_args()

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

    export_jobs = build_export_jobs(
        df, df_without_types, pre_win_df, pre_win_df_without_types
    )

    if args.list_exports:
        print("Available exports:")
        display_export_options(export_jobs)
        return

    if args.exports:
        selected_exports = normalize_export_selection(args.exports, export_jobs)
    elif sys.stdin.isatty():
        selected_exports = prompt_for_exports(export_jobs)
    else:
        selected_exports = list(export_jobs.keys())

    run_export_jobs(selected_exports, export_jobs)


if __name__ == "__main__":
    main()
