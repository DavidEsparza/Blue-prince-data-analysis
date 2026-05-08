import streamlit as st
from pathlib import Path
from db_manager import query_db, save_to_db

# Initialize session state for page navigation
if "current_page" not in st.session_state:
    st.session_state.current_page = "profile"

# Page configuration
st.set_page_config(
    page_title="Blue Prince Data Collection", page_icon="👑", layout="wide"
)

st.title("Blue Prince Data Collection")


def save_all_data():
    lines = []

    profile = st.session_state.get("profile_data", {})
    player_id = save_to_db("players", profile)

    print("#@$#@$@#$@$@#$@#$@#$@#$@#$@#$@#$@#$")
    for key, value in profile.items():
        lines.append(f"  {key}: {value}")

    image_list_names = st.session_state.get("image_list_names", [])
    list_of_mansions = st.session_state.get("list_of_mansions", [])
    list_of_run_stats = st.session_state.get("list_of_run_stats", [])
    for idx, image_name in enumerate(image_list_names):

        if idx < len(list_of_run_stats):
            stats = list_of_run_stats[idx]
            lines.append(f"  Steps Taken: {stats.get('steps_taken', 0)}")
            lines.append(f"  Items: {stats.get('items', 0)}")
            lines.append(f"  New Rooms: {stats.get('new_rooms', 0)}")
            lines.append(f"  Outer Room: {stats.get('outer_room', '')}")
            lines.append(f"  Current Allowance: {stats.get('current_allowance', 0)}")
            lines.append(f"  Current Stars: {stats.get('current_stars', 0)}")

        if idx < len(list_of_mansions):
            for row_i, row in enumerate(list_of_mansions[idx]):
                lines.append(f"  Row {row_i}: {row}")
        else:
            lines.append("  No data captured for this run")

    payload = "\n".join(lines)
    st.session_state.last_saved_dump = payload
    print(payload, flush=True)


# Page routing
if st.session_state.current_page == "profile":
    from pages.profile_information import show_profile_page

    show_profile_page()
elif st.session_state.current_page == "run_capture":
    from pages.complete_run_capture import show_run_capture_page

    show_run_capture_page(save_callback=save_all_data)

if "last_saved_dump" in st.session_state:
    with st.expander("Last Saved Data", expanded=False):
        st.code(st.session_state.last_saved_dump)
