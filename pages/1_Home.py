import streamlit as st

st.set_page_config(
    page_title="Smart AI Risk & Portfolio Assistant",
    page_icon="📈",
    layout="wide"
)

st.title("Smart AI Risk & Portfolio Assistant")

st.markdown(
    """
---

### 🎯 Project Purpose

Welcome to your next-generation investment assistant—designed to empower you with **AI-driven risk analysis, actionable investment recommendations, and transparent portfolio management**.

---

#### Key Features

- **Automatic Risk Classification**  
  Instantly assess stocks and crypto using a machine learning engine that combines technical, fundamental, and sentiment indicators.
- **Personalized Buy/Sell Recommendations**  
  All guidance is tailored to your selected investor profile (Aggressive / Moderate / Conservative) and adapts in real time to market conditions.
- **Interactive Portfolio Dashboard**  
  Monitor your real investment portfolio.
- **Explainable Actions & Alerts**  
  Each recommendation is justified.
---

### 🧾 Navigation

Use the sidebar to access:

- 🟢 **Profile Selection** — Set your individual risk tolerance and investment style.
- 🟡 **Market Analysis** — Browse all supported stocks, cryptocurrencies, and ETFs; instantly see risk ratings and receive **personalized buy/sell/hold recommendations** powered by AI and matched to your active profile.
- 🟣 **Portfolio Dashboard** — Track your actual portfolio with asset names, types, current risk ratings, and performance metrics.

---

### 🛡️ Best Practices

- Choose your risk profile wisely to ensure the best-fit recommendations.
- Review risk ratings and recommendations before making any investment decisions.
---

> *Making investment decisions smarter, safer, and more transparent—powered by AI.*

---
"""
)
