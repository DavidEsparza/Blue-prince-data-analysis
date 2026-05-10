from PIL import Image
import copy
import streamlit as st
from . import config
from wrapper import get_rooms


def show_run_capture_page(save_callback=None):
    """Render the run capture UI and persist per-run state in session."""
    from pathlib import Path

    MEDIA_PATH = Path(__file__).resolve().parents[3] / "media"
    room_options, room_labels = get_rooms()
    image_list = sorted(
        MEDIA_PATH.glob("CursedMode*.png"),
        key=lambda p: int(p.stem.replace("CursedMode(", "").replace(")", "")),
    )[:1]

    st.session_state.image_list_names = [img.name for img in image_list]

    if "image_index" not in st.session_state:
        st.session_state.image_index = 0

    current_index = st.session_state.image_index
    image = image_list[current_index]

    st.caption(f"Run {current_index + 1} of {len(image_list)}  —  {image.name}")

    mansion = [["" for _ in range(9)] for _ in range(5)]

    if "list_of_mansions" not in st.session_state or len(
        st.session_state.list_of_mansions
    ) != len(image_list):
        st.session_state.list_of_mansions = [
            copy.deepcopy(mansion) for _ in range(len(image_list))
        ]

    if "list_of_run_stats" not in st.session_state or len(
        st.session_state.list_of_run_stats
    ) != len(image_list):
        st.session_state.list_of_run_stats = [
            {
                "steps_taken": 0,
                "items": 0,
                "new_rooms": 0,
                "outer_room": room_options[0] if room_options else 0,
                "current_allowance": 0,
                "current_stars": 0,
                "rank_reached": 1,
            }
            for _ in range(len(image_list))
        ]

    def persist_current_run():
        """Copy current widget values into session state for this run index."""
        run_matrix = st.session_state.list_of_mansions[current_index]
        for row_i in range(5):
            for col_j in range(9):
                key = f"{image.stem}_{row_i}_{col_j}"
                if row_i == 2 and col_j == 0 and len(room_options) > 45:
                    run_matrix[row_i][col_j] = room_options[45]
                elif row_i == 2 and col_j == 8 and len(room_options) > 2:
                    run_matrix[row_i][col_j] = room_options[2]
                else:
                    run_matrix[row_i][col_j] = st.session_state.get(key, "")

        st.session_state.list_of_run_stats[current_index] = {
            "steps_taken": st.session_state.get(f"{image.stem}_steps_taken", 0),
            "items": st.session_state.get(f"{image.stem}_items", 0),
            "new_rooms": st.session_state.get(f"{image.stem}_new_rooms", 0),
            "outer_room": st.session_state.get(f"{image.stem}_outer_room", 0),
            "current_allowance": st.session_state.get(
                f"{image.stem}_current_allowance", 0
            ),
            "current_stars": st.session_state.get(f"{image.stem}_current_stars", 0),
            "rank_reached": st.session_state.get(f"{image.stem}_rank_reached", 1),
        }

    current_stats = st.session_state.list_of_run_stats[current_index]

    im = Image.open(image)
    st.image(im)
    rank_reached = st.number_input(
        "Rank Reached",
        min_value=1,
        max_value=10,
        step=1,
        value=current_stats.get("rank_reached", 1),
        key=f"{image.stem}_rank_reached",
    )
    steps_taken = st.number_input(
        "Steps Taken",
        min_value=0,
        step=1,
        value=current_stats.get("steps_taken", 0),
        key=f"{image.stem}_steps_taken",
    )
    items = st.number_input(
        "Items",
        min_value=0,
        step=1,
        value=current_stats.get("items", 0),
        key=f"{image.stem}_items",
    )
    new_rooms = st.number_input(
        "New Rooms",
        min_value=0,
        step=1,
        value=current_stats.get("new_rooms", 0),
        key=f"{image.stem}_new_rooms",
    )
    outer_room_saved = current_stats.get(
        "outer_room", room_options[0] if room_options else 0
    )
    outer_room_index = (
        room_options.index(outer_room_saved) if outer_room_saved in room_options else 0
    )
    outer_room = st.selectbox(
        "Outer Room",
        options=room_options,
        index=outer_room_index,
        format_func=lambda room_id: room_labels.get(room_id, ""),
        key=f"{image.stem}_outer_room",
    )
    current_allowance = st.number_input(
        "Current Allowance",
        min_value=0,
        step=1,
        value=current_stats.get("current_allowance", 0),
        key=f"{image.stem}_current_allowance",
    )
    current_stars = st.number_input(
        "Current Stars",
        min_value=0,
        step=1,
        value=current_stats.get("current_stars", 0),
        key=f"{image.stem}_current_stars",
    )

    for i in range(len(mansion)):
        for j in range(len(mansion[i])):
            start_x = config.BOX_START_X + ((i + 1) * config.ROOM_PIXEL_SIZE)
            start_y = config.BOX_START_Y + ((j + 1) * config.ROOM_PIXEL_SIZE)
            end_x = start_x + config.ROOM_PIXEL_SIZE
            end_y = start_y + config.ROOM_PIXEL_SIZE
            box = (start_x, start_y, end_x, end_y)

            cropped = im.crop(box)
            # print(pytesseract.image_to_string(cropped))

            col1, col2 = st.columns([1, 2])
            with col1:
                st.image(cropped)
            with col2:
                if i == 2 and j == 0:
                    st.selectbox(
                        "room",
                        options=room_options,
                        key=f"{image.stem}_{i}_{j}",
                        label_visibility="hidden",
                        index=45,
                        format_func=lambda room_id: room_labels.get(room_id, ""),
                        disabled=True,
                    )
                elif i == 2 and j == 8:
                    st.selectbox(
                        "room",
                        options=room_options,
                        key=f"{image.stem}_{i}_{j}",
                        label_visibility="hidden",
                        index=2,
                        format_func=lambda room_id: room_labels.get(room_id, ""),
                        disabled=True,
                    )
                else:
                    saved_value = st.session_state.list_of_mansions[current_index][i][j]
                    saved_index = (
                        room_options.index(saved_value)
                        if saved_value in room_options
                        else 0
                    )
                    st.selectbox(
                        "room",
                        options=room_options,
                        key=f"{image.stem}_{i}_{j}",
                        label_visibility="hidden",
                        index=saved_index,
                        format_func=lambda room_id: room_labels.get(room_id, ""),
                    )

    st.divider()
    nav_col1, nav_col2, nav_col3 = st.columns(3)

    with nav_col1:
        if st.button("← Back to Profile", use_container_width=True):
            persist_current_run()
            st.session_state.current_page = "profile"
            st.rerun()

    with nav_col2:
        if st.button(
            "← Previous Run", use_container_width=True, disabled=current_index == 0
        ):
            persist_current_run()
            st.session_state.image_index -= 1
            st.rerun()

    with nav_col3:
        if current_index < len(image_list) - 1:
            if st.button("Next Run →", use_container_width=True):
                persist_current_run()
                st.session_state.image_index += 1
                st.rerun()
        else:
            if st.button("✓ Save Run Data", use_container_width=True):
                persist_current_run()
                if save_callback:
                    save_callback()
                    st.success("Run data saved successfully!")
                else:
                    st.error(
                        "Save callback is not configured in the main interface file."
                    )
