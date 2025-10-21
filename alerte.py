def alerte(name: str, asset_map: dict[str, list[float]]) -> str:
    # Cherche uniquement la ligne pour 'name' !
    if name not in asset_map:
        return "unknown"
    values = asset_map[name]
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

    r2_bin = 0 if r2_raw < 0.5 else 1
    r1_effective = r1_raw * r2_bin

    if r1_effective == 0.0:
        risk_label = "unknown"
    elif 0 < r1_effective <= 0.33:
        risk_label = "low"
    elif 0.33 < r1_effective <= 0.66:
        risk_label = "medium"
    else:
        risk_label = "high"
    return risk_label
