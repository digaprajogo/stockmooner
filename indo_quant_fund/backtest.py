# backtest.py
"""
Simple Backtesting Engine for IndoQuantFund.
Simulates the strategy over historical data to estimate performance.
"""

import pandas as pd
import matplotlib.pyplot as plt
from brain import StrategyEngine
from risk_guard import RiskGatekeeper
from data_engine import GoAPILoader
from utils import calculate_atr
import config

def run_backtest(ticker: str, initial_capital: float = 100_000_000):
    print(f"--- BACKTESTING {ticker} ---")
    
    # 1. Setup
    loader = GoAPILoader()
    brain = StrategyEngine()
    risk = RiskGatekeeper(initial_capital)
    
    # 2. Get Data (Full History)
    df = loader.get_ohlcv(ticker, days=500)
    broker_data = loader.get_broker_summary(ticker) # Note: In real backtest, this needs to be historical too
    
    # 3. Simulation Loop
    cash = initial_capital
    shares_held = 0
    df['portfolio_value'] = initial_capital
    trade_log = []
    
    # We need at least 150 days for EMA
    start_index = 150
    
    for i in range(start_index, len(df)):
        # "Slice" the data to simulate "Today"
        # We only see data up to index 'i'
        current_slice = df.iloc[:i+1].copy()
        current_date = current_slice.iloc[-1]['date']
        current_price = current_slice.iloc[-1]['close']
        
        # Calculate Indicators on the slice
        # Note: Optimization would calculate once and slice, but this is safer to prevent look-ahead bias
        current_slice = brain.prepare_indicators(current_slice) 
        
        # Check Signals
        s1, _, _ = brain.analyze_stage2_breakout(current_slice, broker_data)
        s2, _, _ = brain.analyze_stage1_accumulation(current_slice, broker_data)
        
        signal = s1 or s2
        
        # Logic: BUY if Signal and No Position
        if signal and shares_held == 0:
            atr = calculate_atr(current_slice).iloc[-1]
            ihsg_mock = loader.get_composite_index() # Mock IHSG
            
            # Risk Check
            approved, reason, lots, sl = risk.validate_entry(
                ticker, current_price, cash, cash, ihsg_mock, 
                broker_data['acc_ratio'], broker_data['top_buyer'], atr
            )
            
            if approved and lots > 0:
                shares_bought = lots * 100
                cost = shares_bought * current_price
                if cost <= cash:
                    cash -= cost
                    shares_held += shares_bought
                    trade_log.append({
                        'date': current_date, 'action': 'BUY', 'price': current_price, 'shares': shares_bought
                    })
                    print(f"[{current_date.date()}] BUY  @ {current_price:.0f} | {reason}")

        # Logic: SELL (Chandelier Exit - ATR Based)
                elif shares_held > 0:
                    # Hitung ATR
                    atr = calculate_atr(current_slice).iloc[-1]
                    # Hitung Stop Price Berbasis Volatilitas (Trailing)
                    # Kita ambil High 20 hari terakhir sebagai acuan trailing
                    highest_high = current_slice['high'].tail(20).max() 
                    stop_price = highest_high - (atr * 3.0) 
                     
                    # Eksekusi Jual jika harga tembus Stop Price
                    if current_price < stop_price:
                        revenue = shares_held * current_price
                        cash += revenue
                        print(f"[{current_date.date()}] SELL @ {current_price:.0f} | Chandelier Exit Hit (Stop: {stop_price:.0f})")
                        trade_log.append({
                                'date': current_date, 'action': 'SELL', 'price': current_price, 'shares': shares_held
                            })
                        shares_held = 0
        
        # Track Value
        market_value = shares_held * current_price
        total_value = cash + market_value
        df.at[i, 'portfolio_value'] = total_value

    # Summary
    final_value = df.iloc[-1]['portfolio_value']
    profit = final_value - initial_capital
    print(f"\nInitial: {initial_capital:,.0f}")
    print(f"Final  : {final_value:,.0f}")
    print(f"Profit : {profit:,.0f} ({(profit/initial_capital)*100:.2f}%)")
    print("-" * 30)

if __name__ == "__main__":
    run_backtest("BBCA")
