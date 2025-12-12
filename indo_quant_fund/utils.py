# utils.py
"""
Utility functions for IndoQuantFund.
Handles IDX specific tick sizes and Technical Analysis indicators.
"""

import pandas as pd
import numpy as np

def round_to_tick(price: float) -> int:
    """
    Rounds price to the nearest valid IDX tick size.
    
    IDX Tick Rules:
    < 200       : Tick 1
    200 - 500   : Tick 2
    500 - 2000  : Tick 5
    2000 - 5000 : Tick 10
    >= 5000     : Tick 25
    """
    price = float(price)
    
    if price < 200:
        tick = 1
    elif price < 500:
        tick = 2
    elif price < 2000:
        tick = 5
    elif price < 5000:
        tick = 10
    else:
        # Note: The prompt says "= 5000: Tick 25", implying >= 5000
        tick = 25
        
    return int(round(price / tick) * tick)

def calculate_ema(df: pd.DataFrame, period: int, column: str = 'close') -> pd.Series:
    """
    Calculates Exponential Moving Average (EMA).
    """
    return df[column].ewm(span=period, adjust=False).mean()

def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculates Average True Range (ATR).
    """
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    
    # Calculate ATR using Wilder's Smoothing (RMA) or standard EMA. 
    # Standard practice is typically RMA (Rolling Mean) or EMA. 
    # Here we use proper Wilder's Smoothing method logic via EWM for accuracy.
    atr = true_range.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    
    return atr

def calculate_bollinger_bands(df: pd.DataFrame, period: int = 20, std_dev: float = 2.0):
    """
    Calculates Bollinger Bands and Band Width.
    """
    sma = df['close'].rolling(window=period).mean()
    std = df['close'].rolling(window=period).std()
    
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)
    
    # Band Width = (Upper - Lower) / Middle
    bandwidth = (upper - lower) / sma
    
    return upper, lower, bandwidth
