import streamlit as st

st.set_page_config(page_title="Investor Profile Selection", layout="wide")

st.markdown("<h2 style='text-align: center; color: #0366d6;'>Select Your Investor Risk Profile</h2>", unsafe_allow_html=True)

profiles = [
    {
        "name": "Aggressive",
        "risk": "High Risk Tolerance",
        "desc": "Favors maximizing returns by accepting higher market volatility.",
        "color": "#e74c3c",
        "icon": "⚡️"
    },
    {
        "name": "Moderate",
        "risk": "Balanced Risk/Return",
        "desc": "Targets stable growth with a controlled level of risk.",
        "color": "#f1c40f",
        "icon": "🎯"
    },
    {
        "name": "Conservative",
        "risk": "Low Risk Tolerance",
        "desc": "Prioritizes security and capital preservation.",
        "color": "#27ae60",
        "icon": "🛡️"
    }
]

# Store selection in st.session_state
if "profile" not in st.session_state:
    st.session_state.profile = None

cols = st.columns(3)
for idx, prof in enumerate(profiles):
    selected = (st.session_state.profile == prof["name"])
    frame_color = prof["color"] if selected else "#cccccc"
    box_shadow = "0 4px 16px #00000020" if selected else "0 2px 6px #00000005"
    
    with cols[idx]:
        st.markdown(
            f"""
            <div style='border: 3px solid {frame_color}; border-radius: 18px; box-shadow: {box_shadow}; padding:28px 12px 28px 12px; min-height:320px; display:flex; flex-direction:column; justify-content:space-between; background-color: #f9f9f9; margin-bottom:20px;'>
                <h3 style='text-align:center;'>{prof["icon"]} {prof["name"]}</h3>
                <p style='text-align:center; color: {prof["color"]}; font-weight: bold;'>{prof["risk"]}</p>
                <p style='text-align:center; font-size:1em;'>{prof["desc"]}</p>
            <form action="" method="post">
                <input type="hidden" name="profile" value="{prof["name"]}">
            </form>
            </div>
            """, unsafe_allow_html=True
        )
        if st.button(f"Select {prof['name']}", key=f"btn_{prof['name']}"):
            st.session_state.profile = prof["name"]

# Show selection at the bottom
if st.session_state.profile:
    st.markdown(
        f"""
        <hr>
        <h4 style='text-align:center;'>Selected Profile:
        <span style='color: #0366d6; font-weight:bold;'>{st.session_state.profile}</span></h4>
        """, unsafe_allow_html=True
    )
def get_user_profile():
    import streamlit as st
    return st.session_state.get("profile")

