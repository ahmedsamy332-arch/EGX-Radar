import pandas as pd
import numpy as np

def calculate_rsi(data, window=14):
    """RSI باستخدام Wilder's Smoothing (متوافق مع TradingView)"""
    delta = data.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    # Wilder's smoothing: alpha = 1/window
    ema_up = up.ewm(alpha=1/window, adjust=False).mean()
    ema_down = down.ewm(alpha=1/window, adjust=False).mean()
    rs = ema_up / (ema_down + 1e-10)
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
    return tr.ewm(alpha=1/window, adjust=False).mean()

def calculate_obv_trend(close, volume, ema_window=10):
    direction = pd.Series(0, index=close.index)
    direction[close > close.shift(1)] = 1
    direction[close < close.shift(1)] = -1
    obv = (direction * volume).cumsum()
    obv_ema = obv.ewm(span=ema_window, adjust=False).mean()
    return obv, obv_ema

def calculate_vwap(high, low, close, volume, window=14):
    typical_price = (high + low + close) / 3
    tp_vol = typical_price * volume
    vwap = tp_vol.rolling(window=window).sum() / volume.rolling(window=window).sum()
    return vwap

def calculate_adx(high, low, close, window=14):
    up_move = high - high.shift(1)
    down_move = low.shift(1) - low
    
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    
    plus_dm = pd.Series(plus_dm, index=close.index)
    minus_dm = pd.Series(minus_dm, index=close.index)
    
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    atr = tr.ewm(alpha=1/window, adjust=False).mean()
    plus_di = 100 * (plus_dm.ewm(alpha=1/window, adjust=False).mean() / atr)
    minus_di = 100 * (minus_dm.ewm(alpha=1/window, adjust=False).mean() / atr)
    
    dx = (plus_di - minus_di).abs() / (plus_di + minus_di + 1e-10) * 100
    adx = dx.ewm(alpha=1/window, adjust=False).mean()
    
    return adx, plus_di, minus_di

def calculate_supertrend(high, low, close, period=10, multiplier=3):
    """SuperTrend محسّن — متوافق مع TradingView (ترتيب Band Clamping الصحيح)"""
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/period, adjust=False).mean()
    
    hl2 = (high + low) / 2
    basic_upper = hl2 + (multiplier * atr)
    basic_lower = hl2 - (multiplier * atr)
    
    final_upper = basic_upper.copy()
    final_lower = basic_lower.copy()
    supertrend = pd.Series(0.0, index=close.index)
    direction = pd.Series(1, index=close.index)
    
    # ضبط القيمة الأولية بناءً على وضع السوق الفعلي
    if close.iloc[0] > basic_upper.iloc[0]:
        direction.iloc[0] = 1
    else:
        direction.iloc[0] = -1
    
    for i in range(1, len(close)):
        # الخطوة 1: تثبيت النطاقات (Band Clamping) — قبل فحص الاتجاه
        if basic_lower.iloc[i] > final_lower.iloc[i-1] or close.iloc[i-1] < final_lower.iloc[i-1]:
            final_lower.iloc[i] = basic_lower.iloc[i]
        else:
            final_lower.iloc[i] = final_lower.iloc[i-1]
            
        if basic_upper.iloc[i] < final_upper.iloc[i-1] or close.iloc[i-1] > final_upper.iloc[i-1]:
            final_upper.iloc[i] = basic_upper.iloc[i]
        else:
            final_upper.iloc[i] = final_upper.iloc[i-1]
        
        # الخطوة 2: تحديد الاتجاه بعد تثبيت النطاقات
        if direction.iloc[i-1] == 1:  # كان صاعد
            if close.iloc[i] < final_lower.iloc[i]:
                direction.iloc[i] = -1  # انعكس لهابط
            else:
                direction.iloc[i] = 1   # استمرار صعود
        else:  # كان هابط
            if close.iloc[i] > final_upper.iloc[i]:
                direction.iloc[i] = 1   # انعكس لصاعد
            else:
                direction.iloc[i] = -1  # استمرار هبوط
        
        # الخطوة 3: تحديد قيمة SuperTrend
        if direction.iloc[i] == 1:
            supertrend.iloc[i] = final_lower.iloc[i]
        else:
            supertrend.iloc[i] = final_upper.iloc[i]
            
    return supertrend, direction

def calculate_bb_squeeze(close, window=20, lookback=120):
    """عصرة البولينجر: تقارن العرض الحالي مع الـ percentile 10 لآخر lookback شمعة"""
    sma = close.rolling(window=window).mean()
    std = close.rolling(window=window).std(ddof=0)
    upper = sma + (std * 2)
    lower = sma - (std * 2)
    bb_width = (upper - lower) / (sma + 1e-10)
    # مقارنة مع الـ 10th percentile لآخر lookback شمعة (وليس min)
    width_pct10 = bb_width.rolling(window=lookback, min_periods=window).quantile(0.10)
    squeeze_on = bb_width <= width_pct10
    return squeeze_on

def calculate_cmf(high, low, close, volume, window=20):
    money_flow_mult = ((close - low) - (high - close)) / (high - low + 1e-10)
    money_flow_vol = money_flow_mult * volume
    cmf = money_flow_vol.rolling(window=window).sum() / volume.rolling(window=window).sum()
    return cmf

# === المؤشرات الجديدة V3.0 ===

def detect_rsi_divergence(close, rsi, lookback=20):
    """
    كشف التباعد بين السعر و RSI (Bullish & Bearish Divergence)
    يرجع:
      1 = Bullish Divergence (السعر قاع أدنى + RSI قاع أعلى → ارتداد متوقع)
     -1 = Bearish Divergence (السعر قمة أعلى + RSI قمة أدنى → هبوط متوقع)
      0 = لا يوجد تباعد
    """
    if len(close) < lookback + 5:
        return 0
    
    recent_close = close.iloc[-lookback:]
    recent_rsi = rsi.iloc[-lookback:]
    half = lookback // 2
    
    # البحث عن القيعان (Swing Lows)
    first_half_close = recent_close.iloc[:half]
    second_half_close = recent_close.iloc[half:]
    first_half_rsi = recent_rsi.iloc[:half]
    second_half_rsi = recent_rsi.iloc[half:]
    
    price_low_1 = first_half_close.min()
    price_low_2 = second_half_close.min()
    rsi_low_1 = first_half_rsi.iloc[first_half_close.values.argmin()]
    rsi_low_2 = second_half_rsi.iloc[second_half_close.values.argmin()]
    
    # Bullish Divergence: سعر قاع أدنى + RSI قاع أعلى
    if price_low_2 < price_low_1 and rsi_low_2 > rsi_low_1 + 2:
        return 1
    
    # البحث عن القمم (Swing Highs)
    price_high_1 = first_half_close.max()
    price_high_2 = second_half_close.max()
    rsi_high_1 = first_half_rsi.iloc[first_half_close.values.argmax()]
    rsi_high_2 = second_half_rsi.iloc[second_half_close.values.argmax()]
    
    # Bearish Divergence: سعر قمة أعلى + RSI قمة أدنى
    if price_high_2 > price_high_1 and rsi_high_2 < rsi_high_1 - 2:
        return -1
    
    return 0

def calculate_stochastic_rsi(close, rsi_period=14, stoch_period=14, k_smooth=3, d_smooth=3):
    """
    Stochastic RSI — أكثر حساسية من RSI العادي لكشف القمم والقيعان
    يرجع (K, D) حيث:
      K < 20 = تشبع بيعي
      K > 80 = تشبع شرائي
      K يقطع D لأعلى = إشارة شراء
      K يقطع D لأسفل = إشارة بيع
    """
    rsi = calculate_rsi(close, window=rsi_period)
    
    rsi_min = rsi.rolling(window=stoch_period).min()
    rsi_max = rsi.rolling(window=stoch_period).max()
    
    stoch_rsi = (rsi - rsi_min) / (rsi_max - rsi_min + 1e-10) * 100
    
    k = stoch_rsi.rolling(window=k_smooth).mean()
    d = k.rolling(window=d_smooth).mean()
    
    return k, d

def calculate_pivot_points(high, low, close):
    """
    حساب مستويات الدعم والمقاومة (Pivot Points) من آخر شمعة مكتملة
    يستخدم الطريقة الكلاسيكية (Standard Pivot):
      PP = (H + L + C) / 3
      S1 = 2*PP - H,   R1 = 2*PP - L
      S2 = PP - (H-L),  R2 = PP + (H-L)
    """
    h = float(high.iloc[-1])
    l = float(low.iloc[-1])
    c = float(close.iloc[-1])
    
    pp = (h + l + c) / 3.0
    s1 = (2 * pp) - h
    r1 = (2 * pp) - l
    s2 = pp - (h - l)
    r2 = pp + (h - l)
    
    return {
        "PP": round(pp, 3),
        "S1": round(s1, 3),
        "S2": round(s2, 3),
        "R1": round(r1, 3),
        "R2": round(r2, 3)
    }
