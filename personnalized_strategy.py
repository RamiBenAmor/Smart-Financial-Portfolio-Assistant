import streamlit as st
from typing import Dict, List
import importlib.util
import sys
profile_selection = st.session_state.get("profile")
def strategy_widget(asset_map: Dict[str, List[float]],
                    user_holdings: Dict[str, float],
                    user_profile: str):
    from recommand_transactions import recommend_transactions, ask_gemini_to_explain
    user_profile = user_profile
    user_holdings = {"AAPL": 1, "BTC_USD": 0.1, "TSLA": 0.5}
    recs, txs = recommend_transactions(asset_map, user_holdings, user_profile)
    gemini_text = ask_gemini_to_explain(recs, txs, user_holdings, user_profile)
    # Display in an expandable box for clarity
    with st.expander("Personalized Strategy Recommendation", expanded=True):
        st.write(gemini_text)