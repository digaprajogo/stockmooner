# risk_guard.py
"""
The Risk Guard (Gatekeeper)
"200 IQ" Logic involving Market Regime filtering and Dynamic Position Sizing.
"""

import pandas as pd
from typing import Tuple, Optional
from utils import calculate_ema, calculate_atr, round_to_tick
import config

class RiskGatekeeper:
    def __init__(self, initial_capital: float = config.INITIAL_CAPITAL):
        self.max_capital = initial_capital
        
    def check_market_regime(self, ihsg_data: pd.DataFrame) -> str:
        """
        Determines the broad market health using the Composite Index (IHSG).
        Logic: If IHSG Close < EMA(200) -> DEFENSIVE (Bearish/Correction).
        """
        if len(ihsg_data) < 200:
            # Default to slightly cautious if not enough data
            return "DEFENSIVE"
            
        ihsg_data['EMA_200'] = calculate_ema(ihsg_data, 200, column='close')
        current = ihsg_data.iloc[-1]
        
        if current['close'] < current['EMA_200']:
            return "DEFENSIVE"
        else:
            return "BULLISH"

    def calculate_chandelier_stop(self, entry_price: float, atr_value: float) -> int:
        """
        Calculates the initial Stop Loss using Chandelier Exit logic.
        Formula: Entry - (ATR * 3.0)
        """
        raw_stop = entry_price - (atr_value * 3.0)
        return round_to_tick(raw_stop)

    def validate_entry(
        self, 
        ticker: str,
        entry_price: float,
        cash_balance: float, 
        current_equity: float,
        ihsg_data: pd.DataFrame, 
        bandar_ratio: float,
        top_buyer: str,
        atr_value: float
    ) -> Tuple[bool, str, int, int]:
        """
        Completes a rigorous multi-factor check before approving a trade.
        
        Steps:
        1. Market Regime Filter (Reduces size in Bear markets).
        2. Bad Actor Filter (Retail Top Buyer).
        3. Dynamic Sizing based on Conviction (Bandar Ratio).
        4. Cash Sufficiency Check.
        
        Returns:
            (Approved_Bool, Reason, Lot_Size, Stop_Loss_Price)
        """
        
        # 1. Bad Actor Filter
        if top_buyer in config.RETAIL_CROWD:
            return False, f"REJECTED: Top Buyer {top_buyer} is Retail Crowd.", 0, 0
            
        # 2. Market Regime Check
        regime = self.check_market_regime(ihsg_data)
        regime_multiplier = 1.0
        if regime == "DEFENSIVE":
            regime_multiplier = 0.5  # Cut size by 50% in bad markets
            
        # 3. Dynamic Position Sizing (Kelly-ish)
        # Determine Risk Percentage
        if bandar_ratio > 2.5:
            # High Conviction Setup
            risk_pct = config.AGGRESSIVE_RISK # 3.0%
        else:
            risk_pct = config.BASE_RISK_PER_TRADE # 1.5%
            
        # Calculate Risk Amount (IDR)
        risk_amount = current_equity * risk_pct * regime_multiplier
        
        # Calculate Stop Loss Distance (Risk per share)
        stop_loss_price = self.calculate_chandelier_stop(entry_price, atr_value)
        risk_per_share = entry_price - stop_loss_price
        
        if risk_per_share <= 0:
            # Fallback if ATR is abnormally low or calculation errs
            risk_per_share = entry_price * 0.05 # Minimum 5% risk width
            stop_loss_price = round_to_tick(entry_price - risk_per_share)
            
        # Calculate Number of Shares
        # Risk_Amount = Shares * Risk_Per_Share
        # Shares = Risk_Amount / Risk_Per_Share
        num_shares = int(risk_amount / risk_per_share)
        
        # Convert to Lots (1 Lot = 100 Shares in IDX)
        num_lots = num_shares // 100
        
        # 4. Cash Check
        required_capital = num_lots * 100 * entry_price
        if cash_balance < required_capital:
            # Try to adjust max lots to available cash
            max_affordable_lots = int(cash_balance // (100 * entry_price))
            if max_affordable_lots < 1:
                return False, "REJECTED: Insufficient Cash.", 0, 0
            num_lots = max_affordable_lots
            
        if num_lots == 0:
             return False, "REJECTED: Calculated position size is 0.", 0, 0

        approval_msg = (
            f"APPROVED: {regime} Market. "
            f"Conviction: {'HIGH' if bandar_ratio > 2.5 else 'NORMAL'}. "
            f"Risk: {risk_pct*100}%. Size: {num_lots} Lots."
        )
        
        return True, approval_msg, num_lots, stop_loss_price
