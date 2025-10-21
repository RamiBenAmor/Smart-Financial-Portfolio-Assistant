import streamlit as st
import pandas as pd
from alerte import alerte  # Ajoute l'import !
purshase = st.session_state.get('purshase')
def show_purchased_dashboard(holdings_df, asset_map):
    st.title("🛒 Assets You Have Purchased")
    if holdings_df.empty:
        st.info("You have not purchased any assets yet.")
        return

    st.markdown("#### Select assets to sell:")

    sell_flags = []
    header_cols = st.columns([3,2,2,2,1,1])
    header_cols[0].markdown("**Symbol**")
    header_cols[1].markdown("**Type**")
    header_cols[2].markdown("**Change (%)**")
    header_cols[3].markdown("**Quantity**")
    header_cols[4].markdown("**Select to Sell**")
    header_cols[5].markdown("**Sell**")

    for idx, row in holdings_df.iterrows():
        col1, col2, col3, col4, col5, col6 = st.columns([3,2,2,2,1,1])
        col1.write(row['symbol'])
        col2.write(row['type'])
        col3.write(f"{row['change']} %")
        col4.write(row['quantity'])
        sell_flags.append(col5.checkbox("", key=f"sell_chk_{row['symbol']}"))
        
        # Bouton "Sell" individuel
        sell_btn = col6.button("Sell", key=f"sell_btn_{row['symbol']}")
        if sell_btn:
            risk = alerte(row['symbol'], asset_map)
            # Affiche le risque + score détaillé
            risk_details = asset_map.get(row['symbol'], ["unknown", None])
            risk_label, risk_score = risk_details
            st.info(f"Sell action for {row['symbol']} triggered.")

            if risk == "high":
                st.error("🚨 High combined risk (financial and security) detected. Selling is risky!")
            elif risk == "medium":
                st.warning("⚠️ Medium overall risk (financial and security). Consider before selling.")
            elif risk == "low":
                st.success("✅ Asset has a low combined risk for finance and security. Sell order is safe.")
            else:
                st.info("Risk: unknown – not enough data or asset not found.")

    # Bouton global "Sell Selected"
    if st.button("Sell Selected"):
        sold_symbols = holdings_df.loc[[f for f in sell_flags]].symbol.tolist()
        if sold_symbols:
            st.success(f"Sell order initiated for: {', '.join(sold_symbols)}")
            # Logique de vente à ajouter ici !
        else:
            st.warning("Please select at least one asset to sell.")
# Example data
data = {
    "symbol": ["AAPL", "BTC-USD", "TSLA"],
    "type": ["Stock", "Crypto", "Stock"],
    "change": [1.23, -0.34, 2.3]
}
holdings_df = pd.DataFrame(data)
holdings = {"AAPL": 1, "BTC_USD": 0.1, "TSLA": 0.5}
holdings_df['quantity'] = holdings_df['symbol'].map(lambda x: holdings.get(x.replace("-", "_"), 0))
show_purchased_dashboard(holdings_df,purshase)
