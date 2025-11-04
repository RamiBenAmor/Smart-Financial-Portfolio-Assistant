# gemini_recs_english.py
from typing import Dict, List, Tuple, Optional
from google import genai
import json

# -------- configure Gemini client (replace API key) ----------
client = genai.Client(api_key="xxxx")
import streamlit as st
user_profile = st.session_state.get("profile")

# -------- compact recommend_transactions (same rules, simplified) ----------
def recommend_transactions(
    asset_map: Dict[str, List[float]],
    user_holdings: Dict[str, float],
    user_profile: str
) -> Tuple[Dict[str, List[str]], List[Tuple[str, List[str]]]]:
   user_profile = st.session_state.get("profile")
   normalized_holdings = {k.lower(): v for k, v in user_holdings.items()}

   recommendations: Dict[str, List[str]] = {}
   txs: List[Tuple[str, List[str]]] = []

   def holding_amount(name: str) -> float:
        return normalized_holdings.get(name.lower(), 0.0)

   for asset, values in asset_map.items():

        try:
            r1_raw = float(values[0])
        except Exception:
            r1_raw = 0.0
        try:
            r2_raw = float(values[1])
        except Exception:
            r2_raw = 0.0

        # clamp to [0,1]
        r1_raw = max(0.0, min(1.0, r1_raw))
        r2_raw = max(0.0, min(1.0, r2_raw))

        # convert r2 to binary and attenuate r1
        r2_bin = 0 if r2_raw < 0.5 else 1
        r1_effective = r1_raw * r2_bin  # if r2_bin == 0, this becomes 0

        # determine risk label from r1_effective
        if r1_effective == 0.0:
            risk_label = "unknown"  # source attenuated / not legit
        elif 0 < r1_effective <= 0.33:
            risk_label = "low"
        elif 0.33 < r1_effective <= 0.66:
            risk_label = "medium"
        else:
            risk_label = "high"

        actions = set()

        # if r1_effective == 0 => hold + mark as not legit
        if r1_effective == 0.0:
            actions.add("hold")
        else:
            # base rules
            if risk_label == "low":
                actions.add("buy")
            if risk_label == "medium":
                actions.add("hold")
            if risk_label == "high" and holding_amount(asset) > 0:
                actions.add("sell")

            # profile overrides (keep same logic as before)
            if user_profile in ("aggressive", "agressive"):
                if risk_label == "medium":
                    actions.discard("hold")
                    actions.add("buy")
                if risk_label == "high":
                    actions.add("buy")
                    if holding_amount(asset) > 0:
                        actions.add("sell")
            elif user_profile == "balanced":
                if risk_label == "medium":
                    actions.discard("hold")
                    actions.add("buy")
                    if holding_amount(asset) > 0:
                        actions.add("sell")
                if risk_label == "high" and holding_amount(asset) > 0:
                    actions.add("sell")
            elif user_profile == "conservative":
                if risk_label == "medium":
                    actions.clear()
                    actions.add("hold")
                if risk_label == "high":
                    actions.clear()
                    if holding_amount(asset) > 0:
                        actions.add("sell")
            else:
                if risk_label == "medium":
                    actions.clear()
                    actions.add("hold")

        if not actions:
            actions.add("hold")

        action_list = sorted(actions)
        recommendations[asset] = action_list

        if "buy" in actions or "sell" in actions:
            txs.append((asset, action_list))

   return recommendations, txs
def ask_gemini_to_explain(
    recommendations: Dict[str, List[str]],
    transact_list: List[Tuple[str, List[str]]],
    user_holdings: Dict[str, float],
    user_profile: str,
    asset_map: Optional[Dict[str, List[float]]] = None
) -> str:
    """
    Send the computed recommendations to Gemini and request:
      - English-only human-readable recommendations with justification per asset
      - Short next steps

    If `asset_map` is provided (asset -> [r1, r2]) the prompt will instruct the model to
    print each recommended asset with its combined risk value next to it (e.g. "ACME (the combined risk value = 0.20)").
    Everything else is unchanged.
    """
    # Build combined_risk map (r1 gated by r2 -> r1_effective) if asset_map provided
    combined_risk = {}
    if asset_map:
        for asset, vals in asset_map.items():
            try:
                r1_raw = float(vals[0])
            except Exception:
                r1_raw = 0.0
            try:
                r2_raw = float(vals[1])
            except Exception:
                r2_raw = 0.0

            # clamp to [0,1]
            r1_raw = max(0.0, min(1.0, r1_raw))
            r2_raw = max(0.0, min(1.0, r2_raw))

            # replicate the same gating logic used in recommend_transactions:
            # r2 becomes binary (0 if < 0.5 else 1) and r1 is multiplied by that bit.
            r2_bin = 0 if r2_raw < 0.5 else 1
            r1_effective = r1_raw * r2_bin

            combined_risk[asset] = r1_effective
    
    payload = {
        "user_profile": user_profile,
        "holdings": user_holdings,
        "recommendations": recommendations,
        "transact_list": transact_list
    }

    # If we have combined risk values, include them in the payload so the model can reference them.
    if combined_risk:
        payload["combined_risk"] = combined_risk

    # IMPORTANT: instruct the model explicitly to append the combined risk value next to each asset when combined_risk is present
    prompt = (
    "You are an assistant that must produce a clear, professional, and thorough set of "
    "investment recommendations for a retail user. IMPORTANT: Answer ONLY in English. Do NOT use Arabic.\n\n"
    "Input (do not change):\n"
    f"{json.dumps(payload, indent=2)}\n\n"
    "Task (output requirements):\n"
    "1) Produce a short one-line headline (1 sentence).\n"
    "2) For each asset in the recommendations, provide TWO clearly labeled parts:\n"
    "   A) Professional assessment (1-2 sentences) — written in the voice of a seasoned asset/finance professional (asset manager or buy-side analyst). "
    "       Be concise, use professional terminology where helpful, and summarize the key risk/reward view from a professional perspective.\n"
    "   B) Client-facing justification (2-4 sentences) — non-technical, written for a retail user. This must:\n"
    "       - reference the user's holdings and profile (e.g., 'because you hold X' or 'given your conservative profile')\n"
    "       - reference the asset's risk label from the recommendations\n"
    "       - IF a combined risk value is available for that asset in `combined_risk`, append the combined risk value next to the asset name in parentheses, "
    "         formatted exactly like: AssetName (the combined risk value = 0.20). If no combined value is available, do not append anything.\n"
    "       - explain clearly why the recommended action (buy / hold / sell) follows from the above, avoiding vague phrases.\n"
    "3) Provide a brief 'Next steps' section with 3 practical steps the user can take.\n\n"
    "CRITICAL: Do NOT include any JSON, code blocks, or machine-readable blocks anywhere in your response. "
    "Output only human-readable English text.\n\n"
    "Tone & style: For the professional assessment use a professional, succinct tone. For the client-facing justification use a clear, non-technical tone that a retail investor will understand. "
    "Be concrete and specific (for example, 'because you hold 100 shares' or 'given your aggressive profile'). When appropriate, indicate uncertainty or assumptions (for example, 'based on the provided risk indicators').\n\n"
    "Compliance note: This response should be educational and explanatory. If the user needs personalized financial advice, recommend they consult a licensed financial advisor.\n\n"
    "Length: be thorough but not excessively long — professional assessment 1-2 sentences and justification 2-4 sentences per asset is fine.\n\n"
    "Now produce the requested output in English only."
)


    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )
    return response.text
