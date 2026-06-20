import pandas as pd

def calculate_rsi(data, window=7):
    delta = data.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ema_up = up.ewm(com=window-1, adjust=False).mean()
    ema_down = down.ewm(com=window-1, adjust=False).mean()
    rs = ema_up / ema_down
    return 100 - (100 / (1 + rs))

def calculate_macd(close):
    ema_12 = close.ewm(span=12, adjust=False).mean()
    ema_26 = close.ewm(span=26, adjust=False).mean()
    macd = ema_12 - ema_26
    signal = macd.ewm(span=9, adjust=False).mean()
    hist = macd - signal
    return macd, signal, hist

def calculate_bb(close, window=20):
    sma = close.rolling(window=window).mean()
    std = close.rolling(window=window).std(ddof=0)
    upper = sma + (std * 2)
    lower = sma - (std * 2)
    return upper, lower

def calculate_atr(high, low, close, window=14):
    high_low = high - low
    high_close = (high - close.shift()).abs()
    low_close = (low - close.shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.ewm(com=window-1, adjust=False).mean()

def calculate_obv_trend(close, volume, ema_window=10):
    direction = pd.Series(0, index=close.index)
    direction[close > close.shift(1)] = 1
    direction[close < close.shift(1)] = -1
    obv = (direction * volume).cumsum()
    obv_ema = obv.ewm(span=ema_window, adjust=False).mean()
    return obv, obv_ema

def calculate_stoch_rsi(rsi_series, window=14, smooth_k=3, smooth_d=3):
    rsi_min = rsi_series.rolling(window=window).min()
    rsi_max = rsi_series.rolling(window=window).max()
    stoch_rsi = (rsi_series - rsi_min) / (rsi_max - rsi_min + 1e-10)
    stoch_rsi_k = stoch_rsi.rolling(window=smooth_k).mean() * 100
    stoch_rsi_d = stoch_rsi_k.rolling(window=smooth_d).mean()
    return stoch_rsi_k, stoch_rsi_d

def calculate_vwap(high, low, close, volume, window=14):
    typical_price = (high + low + close) / 3
    tp_vol = typical_price * volume
    vwap = tp_vol.rolling(window=window).sum() / volume.rolling(window=window).sum()
    return vwap
