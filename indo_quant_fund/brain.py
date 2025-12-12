# brain.py
"""
The Alpha Engine (Brain)
Contains the core strategy logic combining Technicals + Bandarmology.
"""

import pandas as pd
from typing import Tuple, Dict, Any
from utils import calculate_ema, calculate_bollinger_bands, calculate_atr
import config

class StrategyEngine:
    def __init__(self):
        pass

    def prepare_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates necessary indicators for the strategies.
        """
        df['EMA_50'] = calculate_ema(df, 50)
        df['EMA_150'] = calculate_ema(df, 150)
        
        upper, lower, bandwidth = calculate_bollinger_bands(df, period=20, std_dev=2.0)
        df['BB_Upper'] = upper
        df['BB_Lower'] = lower
        df['BB_Width'] = bandwidth
        
        # Calculate 52 Week Low (approx 252 trading days)
        df['52_Week_Low'] = df['low'].rolling(window=252, min_periods=50).min()
        
        return df

    def analyze_stage2_breakout(self, df: pd.DataFrame, broker_data: Dict) -> Tuple[bool, float, str]:
        """
        Strategy 1: Stage 2 Breakout (Momentum + Bandar)
        
        Logic:
        1. Technical: Close > EMA(50) AND EMA(50) > EMA(150) (Uptrend Structure)
        2. Bandarmology: Acc_Ratio > 1.5 AND Top Buyer NOT in RETAIL_CROWD
        
        Returns:
            (Signal_Bool, Ratio_Value, Top_Buyer)
        """
        if len(df) < 150:
            return False, 0.0, "N/A"
            
        current = df.iloc[-1]
        
        # 1. Technical Checks
        is_uptrend = (current['close'] > current['EMA_50']) and (current['EMA_50'] > current['EMA_150'])
        
        # 2. Bandarmology Checks
        acc_ratio = broker_data.get('acc_ratio', 0)
        top_buyer = broker_data.get('top_buyer', 'Unknown')
        
        is_accumulation = acc_ratio > 1.5
        is_smart_money = top_buyer not in config.RETAIL_CROWD
        
        signal = is_uptrend and is_accumulation and is_smart_money
        
        return signal, acc_ratio, top_buyer

    def analyze_stage1_accumulation(self, df: pd.DataFrame, broker_data: Dict) -> Tuple[bool, float, str]:
        """
        Strategy 2: Silent Accumulation (Bottom Fishing)
        
        Logic:
        1. Technical: BB Width < 0.15 (Squeeze) AND Price < 1.15 * 52_Week_Low
        2. Bandarmology: Acc_Ratio > 2.0 AND Top Buyer IS inside SMART_MONEY
        
        Returns:
            (Signal_Bool, Ratio_Value, Top_Buyer)
        """
        if len(df) < 252:
            return False, 0.0, "N/A"
            
        current = df.iloc[-1]
        
        # 1. Technical Checks
        # Volatility Squeeze
        is_squeeze = current['BB_Width'] < 0.15
        
        # Near Bottom (within 15% of 52 week low)
        near_low = current['close'] < (1.15 * current['52_Week_Low'])
        
        # 2. Bandarmology Checks
        acc_ratio = broker_data.get('acc_ratio', 0)
        top_buyer = broker_data.get('top_buyer', 'Unknown')
        
        strong_accumulation = acc_ratio > 2.0
        smart_money_buyer = top_buyer in config.SMART_MONEY
        
        signal = is_squeeze and near_low and strong_accumulation and smart_money_buyer
        
        return signal, acc_ratio, top_buyer
