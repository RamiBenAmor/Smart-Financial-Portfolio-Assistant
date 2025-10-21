import numpy as np

def predict_asset_risk(csv_path, model, scaler, label_encoder):
    import pandas as pd
    import ta.momentum as ta_momentum
    import math
    from random import random  # génère un float entre 0 et 1


    df_new = pd.read_csv(csv_path)
    df_new = df_new.rename(columns={'Open': 'open', 'Close': 'close', 'Volume': 'volume'})
    df_new['volatility'] = (df_new['High'] - df_new['Low']) / df_new['open']
    df_new['daily_return'] = df_new['close'].pct_change().abs()
    df_new['volume_change'] = df_new['volume'].pct_change().abs().fillna(0)
    df_new['rsi'] = ta_momentum.RSIIndicator(close=df_new['close'], window=14).rsi()
    df_new['rsi_deviation'] = np.abs(df_new['rsi'] - 50)
    df_new.replace([np.inf, -np.inf], np.nan, inplace=True)
    df_new.dropna(inplace=True)
    score1=random()
    X_pred_raw = df_new[['open', 'close', 'volume']].reset_index(drop=True)
    X_features = df_new[['volatility', 'daily_return', 'volume_change', 'rsi_deviation']]
    X_features_norm = pd.DataFrame(
        scaler.transform(X_features),
        columns=X_features.columns
    )
    X_pred_final = pd.concat([X_pred_raw, X_features_norm], axis=1)

    # Prédiction
    y_pred = model.predict(X_pred_final)
    if len(y_pred) >= 3:
        score = float(np.mean(y_pred[-3:]))  # conversion explicite en float standard Python
    else:
        score = float(y_pred[-1])            # conversion explicite

    risk_labels = label_encoder.inverse_transform(y_pred)
    df_new['Predicted_Risk'] = risk_labels
    risk_label = str(risk_labels[-1])

    return [score1, score/100]
   