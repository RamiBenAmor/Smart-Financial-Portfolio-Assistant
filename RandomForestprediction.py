import numpy as np
import pandas as pd
import ta.momentum as ta_momentum

def predict_asset_risk(csv_path, model, scaler, label_encoder):
    df_new = pd.read_csv(csv_path)
    df_new = df_new.rename(columns={'Open': 'open', 'Close': 'close', 'Volume': 'volume'})
    df_new['volatility'] = (df_new['High'] - df_new['Low']) / df_new['open']
    df_new['daily_return'] = df_new['close'].pct_change().abs()
    df_new['volume_change'] = df_new['volume'].pct_change().abs().fillna(0)
    df_new['rsi'] = ta_momentum.RSIIndicator(close=df_new['close'], window=14).rsi()
    df_new['rsi_deviation'] = np.abs(df_new['rsi'] - 50)
    df_new.replace([np.inf, -np.inf], np.nan, inplace=True)
    df_new.dropna(inplace=True)
    if df_new.empty:
        return 0.0

    X_pred_raw = df_new[['open', 'close', 'volume']].reset_index(drop=True)
    X_features = df_new[['volatility', 'daily_return', 'volume_change', 'rsi_deviation']]
    X_features_norm = pd.DataFrame(scaler.transform(X_features), columns=X_features.columns)
    X_pred_final = pd.concat([X_pred_raw, X_features_norm], axis=1)

    y_pred = model.predict(X_pred_final)  # labels (int: 0, 1, 2)
    y_proba = model.predict_proba(X_pred_final)  # shape: (n_samples, n_classes)
    risk_labels = label_encoder.inverse_transform(y_pred)  # labels texte

    # Obtenir la "confiance" de la prédiction du modèle sur ses derniers ticks
    last_scores = []
    for i in range(-3, 0):  # sur les 3 dernières lignes
        classe_idx = y_pred[i]
        score_reel = y_proba[i, classe_idx]
        last_scores.append(score_reel)

    score_financier = float(np.mean(last_scores))  # moyenne confiance des 3 dernières prédictions

    return score_financier  # valeur continue [0,1], reflète la confiance réelle du modèle

    # Si besoin, tu peux aussi renvoyer le label majoritaire ou le risk_label[-1]
