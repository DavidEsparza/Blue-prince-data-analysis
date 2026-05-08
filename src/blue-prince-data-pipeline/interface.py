import streamlit as st
from pathlib import Path

# Initialize session state for page navigation
if "current_page" not in st.session_state:
    st.session_state.current_page = "profile"

# Page configuration
st.set_page_config(
    page_title="Blue Prince Data Collection",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.title("Blue Prince Data Collection")


def save_all_data():
    lines = []
    lines.append("=== Profile Info ===")
    profile = st.session_state.get("profile_data", {})
    for key, value in profile.items():
        lines.append(f"  {key}: {value}")

    lines.append("")
    lines.append("=== Mansion Run Data ===")
    image_list_names = st.session_state.get("image_list_names", [])
    for idx, image_name in enumerate(image_list_names):
        stem = Path(image_name).stem
        lines.append("")
        lines.append(f"Run {idx + 1} - {image_name}:")
        for i in range(5):
            row = [st.session_state.get(f"{stem}_{i}_{j}", "") for j in range(9)]
            lines.append(f"  Row {i}: {row}")

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
