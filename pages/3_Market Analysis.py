import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time, os, requests
import warnings
warnings.filterwarnings('ignore')
import plotly.graph_objects as go
import streamlit as st
from personnalized_strategy import strategy_widget
import importlib.util
import sys
from alerte import alerte
holdings = {"AAPL": 1, "BTC_USD": 0.1, "TSLA": 0.5}
import joblib
model = joblib.load('C:\\Users\\ramib\\OneDrive\\Bureau\\assistant de gestion de patrimoine\\RandomForest_Risk_J+1_20251019_0536.joblib')
scaler = joblib.load('C:\\Users\\ramib\\OneDrive\\Bureau\\assistant de gestion de patrimoine\\scaler_20251019_0537.joblib')
le = joblib.load('C:\\Users\\ramib\\OneDrive\\Bureau\\assistant de gestion de patrimoine\\label_encoder_20251019_0537.joblib')
# Full path to your module
profile = st.session_state.get("profile")
import os
from RandomForestprediction import predict_asset_risk
# On part d'un asset_map vide
file_to_symbol = {
    "BTC.csv": "BTC-USD",
    "ETH.csv": "ETH-USD",
    "SOL.csv": "SOL-USD",
    "AAPL.csv": "AAPL",
    "TSLA.csv": "TSLA",
    "GOOGL.csv": "GOOGL",
    "AMZN.csv": "AMZN",
    "MSFT.csv": "MSFT"
}

# Dossier contenant les CSV
DATA_DIR = "market_validation_system"

asset_map = {}




# ------------------------ CONFIGURATION ------------------------
class Config:
    STOCKS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    CRYPTO = ['BTC-USD', 'ETH-USD', 'SOL-USD']
    ALL_SYMBOLS = STOCKS + CRYPTO

    OUTPUT_DIR = "market_validation_system"
    LOOKBACK_HOURS = 24
    REQUEST_DELAY = 0.5

    VOLUME_RATIO_THRESHOLD = 2.0
    PRICE_CHANGE_THRESHOLD = 5.0
    PRICE_ACTIVITY_CORRELATION = 0.3
    MIN_LEGITIMACY_SCORE = 60

    COINGECKO_API = "https://api.coingecko.com/api/v3"
    BLOCKCHAIN_INFO_API = "https://blockchain.info"

config = Config()

# ---------------------- DATA EXTRACTION ----------------------
class MarketDataExtractor:
    def __init__(self):
        self.data = {}

    def extract(self, symbols, hours=24):
        end_date = datetime.now()
        start_date = end_date - timedelta(hours=hours)
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                data = ticker.history(start=start_date, end=end_date, interval='1h')
                if data.empty:
                    start_date_ext = end_date - timedelta(days=7)
                    data = ticker.history(start=start_date_ext, end=end_date, interval='1h')
                    if not data.empty and len(data) > hours:
                        data = data.tail(hours)
                if not data.empty:
                    features = ['Open','High','Low','Close','Volume']
                    if 'Dividends' in data.columns: features.append('Dividends')
                    if 'Stock Splits' in data.columns: features.append('Stock Splits')
                    self.data[symbol] = data[features]
            except Exception as e:
                print(f"Error on {symbol}: {e}")
            time.sleep(config.REQUEST_DELAY)
        return self.data

class BlockchainDataExtractor:
    def __init__(self):
        self.data = {}

    def extract_bitcoin_metrics(self):
        try:
            url = f"{config.BLOCKCHAIN_INFO_API}/stats?format=json"
            stats = requests.get(url, timeout=10).json()
            metrics = {
                'market_price_usd': stats.get('market_price_usd', 0),
                'hash_rate': stats.get('hash_rate',0)/1e9,
                'transactions_per_day': stats.get('n_tx',0),
                'network_health_score': min(100,(stats.get('hash_rate',0)/1e18)*10)
            }
            return metrics
        except:
            return {}

    def extract_coingecko_metrics(self, crypto_id):
        try:
            url = f"{config.COINGECKO_API}/coins/{crypto_id}"
            params = { 'localization':'false', 'tickers':'true', 'market_data':'true' }
            data = requests.get(url, params=params, timeout=10).json()
            market_data = data.get('market_data',{})
            metrics = {
                'current_price': market_data.get('current_price', {}).get('usd', 0),
                'total_volume_24h': market_data.get('total_volume', {}).get('usd', 0),
                'market_cap': market_data.get('market_cap', {}).get('usd', 0),
                'price_change_24h_pct': market_data.get('price_change_percentage_24h',0),
                'liquidity_score': data.get('liquidity_score',0)*10 if data.get('liquidity_score') else 0
            }
            return metrics
        except:
            return {}

    def extract_all(self, symbols):
        crypto_map = {'BTC-USD':'bitcoin','ETH-USD':'ethereum','SOL-USD':'solana'}
        for symbol in symbols:
            if symbol in crypto_map:
                crypto_id = crypto_map[symbol]
                blockchain_metrics = self.extract_bitcoin_metrics() if symbol=='BTC-USD' else {}
                coingecko_metrics = self.extract_coingecko_metrics(crypto_id)
                self.data[symbol] = {**blockchain_metrics, **coingecko_metrics}
                time.sleep(config.REQUEST_DELAY)
        return self.data

# ---------------------- VALIDATION ENGINE ----------------------
class ValidationEngine:
    def __init__(self, market_data, blockchain_data):
        self.market_data = market_data
        self.blockchain_data = blockchain_data
        self.results = {}

    def calculate_volume_ratio(self, symbol):
        yf_volume = self.market_data[symbol]['Volume'].sum()
        bc_volume = self.blockchain_data.get(symbol, {}).get('total_volume_24h', yf_volume)
        ratio = yf_volume / bc_volume if bc_volume>0 else 1
        status = "✅ HIGHLY LEGITIMATE" if ratio <= 1.5 else \
                 "⚠️ MODERATE RISK" if ratio <= config.VOLUME_RATIO_THRESHOLD else \
                 f"🚨 HIGH RISK"
        return ratio,status

    def calculate_activity_correlation(self, symbol):
        price_change = abs((self.market_data[symbol]['Close'].iloc[-1] - self.market_data[symbol]['Open'].iloc[0])/self.market_data[symbol]['Open'].iloc[0]*100)
        activity_score = self.blockchain_data.get(symbol,{}).get('liquidity_score',50)
        expected_activity = price_change*2
        correlation = min(1.0, activity_score / max(expected_activity,20))
        return correlation

    def calculate_legitimacy_score(self,symbol):
        scores,weights=[],[]
        vol_ratio,_ = self.calculate_volume_ratio(symbol)
        scores.append(max(0,100-(vol_ratio-1)*50)); weights.append(0.4)
        correlation = self.calculate_activity_correlation(symbol)
        scores.append(correlation*100); weights.append(0.3)
        network_health = self.blockchain_data.get(symbol,{}).get('network_health_score',50)
        scores.append(network_health); weights.append(0.3)
        total_score = sum(s*w for s,w in zip(scores,weights))/sum(weights)
        return int(total_score)

    def validate_all(self):
        for symbol in self.market_data.keys():
            vol_ratio,leg_status = self.calculate_volume_ratio(symbol)
            correlation = self.calculate_activity_correlation(symbol)
            leg_score = self.calculate_legitimacy_score(symbol)
            alerts=[]
            if vol_ratio>config.VOLUME_RATIO_THRESHOLD: alerts.append(f"Volume manipulation suspected ({vol_ratio:.2f}x)")
            if correlation<config.PRICE_ACTIVITY_CORRELATION: alerts.append(f"Price-activity mismatch ({correlation:.2f})")
            if leg_score<config.MIN_LEGITIMACY_SCORE: alerts.append(f"Low legitimacy score: {leg_score}/100")
            if symbol in config.STOCKS and leg_score>=80:
                leg_status="✅ HIGHLY LEGITIMATE"
            elif leg_score>=config.MIN_LEGITIMACY_SCORE:
                leg_status="⚠️ MODERATE RISK"
            else:
                leg_status="🚨 HIGH RISK"
            self.results[symbol]={
                'legitimacy_status': leg_status,
                'legitimacy_score': leg_score,
                'alerts': alerts
            }
        return self.results

# ---------------------- UTILITIES ----------------------
def save_market_data_to_csv(market_data, output_dir="market_validation_system"):
    os.makedirs(output_dir, exist_ok=True)
    for symbol, df in market_data.items():
        if not df.empty:
            fname = os.path.join(output_dir, symbol.replace('-USD','')+'.csv')
            df.to_csv(fname)

def plot_asset_chart(asset_symbol, df):
    dfp = df.copy()
    vola = dfp['Close'].rolling(5).std()
    upper = dfp['Close'] + vola.fillna(0)*2
    lower = dfp['Close'] - vola.fillna(0)*2

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dfp.index, y=dfp['Close'],
        mode='lines+markers', line=dict(color="#1976D2", width=4),
        marker=dict(size=8, color="#1976D2", symbol="circle"),
        name=asset_symbol
    ))
    fig.add_traces([
        go.Scatter(x=dfp.index, y=upper,
                   fill='tonexty', fillcolor='rgba(25,118,210,0.10)', 
                   mode='lines', line=dict(width=0), showlegend=False),
        go.Scatter(x=dfp.index, y=lower,
                   fill=None, mode='lines', line=dict(width=0), showlegend=False)
    ])
    fig.add_annotation(
        x=dfp.index[np.argmax(dfp['Close'])],
        y=max(dfp['Close']),
        text="🚀 ATH",
        showarrow=True, arrowhead=1, ax=40, ay=-40, bgcolor="#C8E6C9"
    )
    fig.add_annotation(
        x=dfp.index[np.argmin(dfp['Close'])],
        y=min(dfp['Close']),
        text="🛑 Low",
        showarrow=True, arrowhead=1, ax=-40, ay=40, bgcolor="#FFCDD2"
    )
    fig.update_layout(
        title=f"<b>{asset_symbol} Premium Chart (24h)</b>",
        xaxis=dict(title="Time (UTC)", showgrid=False, showline=True),
        yaxis=dict(title="Price ($)", showgrid=True),
        font=dict(family="Montserrat, sans-serif", size=15),
        plot_bgcolor="#F4F7FA",
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

def get_synoptic_asset_info(market_data):
    rows = []
    for symbol, df in market_data.items():
        if df.empty or len(df) == 0:
            continue
        change = round((df['Close'].iloc[-1] - df['Open'].iloc[0]) / df['Open'].iloc[0] * 100, 2)
        type_ = "Stock" if symbol in config.STOCKS else "Crypto"
        rows.append({"symbol": symbol, "type": type_, "change": change})
    return pd.DataFrame(rows)

def get_selected_score_and_decision(selected_symbol, validation_results):
    res = validation_results.get(selected_symbol, {})
    return res.get("legitimacy_score"), res.get("legitimacy_status")

# ---------------------- MODULARIZED BUY INTERACTION ---------------
def get_buy_decision_interaction(asset_table, market_data, validation_results):
    # 1. Génération de asset_map (à chaque lancement, une fois pour tous les fichiers)
    asset_map = {}
    for filename in os.listdir(DATA_DIR):
        if not filename.endswith(".csv"):
            continue
        if filename not in file_to_symbol:
            continue
        symbol = file_to_symbol[filename]
        csv_path = os.path.join(DATA_DIR, filename)
        
        # Récupérer le risque prédit (index 1 = score entre 0 et 1)
        risk_result = predict_asset_risk(csv_path, model, scaler, le)
        predicted_risk = risk_result[0]  # score entre 0 et 1
        
        # Récupérer le score de légitimité si disponible
        score = None
        if validation_results and symbol in validation_results:
            score, _ = get_selected_score_and_decision(symbol, validation_results)
        
        asset_map[symbol] = [predicted_risk, score]
    
    st.session_state['purshase'] = asset_map

    print("\nAsset map généré automatiquement :")
    print(asset_map)

    # 2. UI Interactif par Streamlit
    selected = None
    score = None
    decision = None
    
    if not asset_table.empty:
        selected = st.selectbox("Select asset for price chart:", asset_table['symbol'])
        
        if selected in market_data:
            plot_asset_chart(selected, market_data[selected])

        # BUY : affichage risk
        buy = st.button("💵 Buy", key=f"buy_{selected}")
        if buy:
            risk = alerte(selected, asset_map)
            print(f"Selected asset: {selected}, Risk: {risk}")
            
            if risk == "high":
                st.error("🚨 High combined risk (financial and security) detected. Please proceed with extreme caution!")
            elif risk == "medium":
                st.warning("⚠️ Medium overall risk (financial and security). Assess your position before trading.")
            elif risk == "low":
                st.success("✅ Asset presents a low combined risk for finance and security.")
            else:
                st.info("Risk: unknown – not enough data or asset not found.")
            
            score, decision = get_selected_score_and_decision(selected, validation_results)
            #st.info(f"Your decision: {decision} (Score: {score})")
            
        # Stratégie personnalisée (exécutée juste si l'utilisateur clique)
        if st.button("🔍 Personalized Strategy"):
            st.info("Launching personalized strategy!")
            strategy_widget(asset_map, holdings, profile)
    
    return selected, score, decision



# ---------------------- MAIN STREAMLIT APP ----------------------
def main():
    st.title("📊 Market Validation & Modern Visualization")
    with st.spinner("Loading data..."):
        extractor = MarketDataExtractor()
        market_data = extractor.extract(config.ALL_SYMBOLS, hours=config.LOOKBACK_HOURS)
        save_market_data_to_csv(market_data)
        blockchain_extractor = BlockchainDataExtractor()
        blockchain_data = blockchain_extractor.extract_all(config.CRYPTO)
        engine = ValidationEngine(market_data, blockchain_data)
        validation_results = engine.validate_all()
        asset_table = get_synoptic_asset_info(market_data)
    st.dataframe(asset_table, use_container_width=True)
    selected, score, decision = get_buy_decision_interaction(asset_table, market_data, validation_results)
    # After calling, you can use selected, score, decision for any workflow (not shown).
    if selected is not None:
     print("Symbole sélectionné :", selected)
     print("Score de légitimité :", score)
     print("Verdict :", decision)
if __name__ == "__main__":
    main()
