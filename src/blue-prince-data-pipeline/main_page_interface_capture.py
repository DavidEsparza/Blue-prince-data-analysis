import streamlit as st
from db_manager import save_to_db

# Initialize session state for page navigation
if "current_page" not in st.session_state:
    st.session_state.current_page = "profile"

# Page configuration
st.set_page_config(
    page_title="Blue Prince Data Collection", page_icon="👑", layout="wide"
)

st.title("Blue Prince Data Collection")


def save_all_data():

    profile = st.session_state.get("profile_data", {})
    if not profile or not profile.get("name"):
        st.error("Missing profile data. Please complete the profile page first.")
        return

    player_id = save_to_db("players", profile)

    image_list_names = st.session_state.get("image_list_names", [])
    list_of_mansions = st.session_state.get("list_of_mansions", [])
    list_of_run_stats = st.session_state.get("list_of_run_stats", [])
    for idx, image_name in enumerate(image_list_names):

        stats = list_of_run_stats[idx] if idx < len(list_of_run_stats) else {}
        day_data = {
            "player": player_id,
            "day": idx + 1,
            "steps_taken": int(stats.get("steps_taken", 0) or 0),
            "items": int(stats.get("items", 0) or 0),
            "new_rooms": int(stats.get("new_rooms", 0) or 0),
            "outer_room": int(stats.get("outer_room", 0) or 0),
            "current_allowance": int(stats.get("current_allowance", 0) or 0),
            "current_stars": int(stats.get("current_stars", 0) or 0),
            "rank_reached": int(stats.get("rank_reached", 0) or 0),
        }
        day_id = save_to_db("days", day_data)

        if idx < len(list_of_mansions):
            saved_rooms = 0
            for row_i, row in enumerate(list_of_mansions[idx]):
                for col_j, room_number in enumerate(row):
                    room_value = int(room_number) if room_number else 0
                    if room_value <= 0:
                        continue
                    save_to_db(
                        "mansion",
                        {
                            "day": day_id,
                            "room": room_value,
                            "position_x": row_i,
                            "position_y": col_j,
                        },
                    )
                    saved_rooms += 1


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
