import streamlit as st


def show_profile_page():
    """Render and save basic player profile inputs."""
    st.subheader("Player Profile Information")

    name = st.text_input("Player Name")
    mode = st.selectbox("Mode", ["Normal", "Curse"])
    west_gate_unlock_day = st.number_input("West Gate Unlock Day", min_value=0, step=1)
    gemstone_cavern_unlock_day = st.number_input(
        "Gemstone Cavern Unlock Day", min_value=0, step=1
    )
    apple_orchard_unlock_day = st.number_input(
        "Apple Orchard Unlock Day", min_value=0, step=1
    )
    blackbridge_unlock_day = st.number_input(
        "Blackbridge Unlock Day", min_value=0, step=1
    )
    satelite_dish_unlock_day = st.number_input(
        "Satelite Dish Unlock Day", min_value=0, step=1
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✓ Proceed to Run Capture", use_container_width=True):
            st.session_state.profile_data = {
                "name": name,
                "mode": mode,
                "west_gate_unlock_day": west_gate_unlock_day,
                "gemstone_cavern_unlock_day": gemstone_cavern_unlock_day,
                "apple_orchard_unlock_day": apple_orchard_unlock_day,
                "blackbridge_unlock_day": blackbridge_unlock_day,
                "satelite_dish_unlock_day": satelite_dish_unlock_day,
            }
            st.session_state.current_page = "run_capture"
            st.rerun()

    with col2:
        if st.button("Cancel", use_container_width=True):
            st.info("Cancelled")
