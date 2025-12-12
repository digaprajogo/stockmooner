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
    
    # 1. Setup (Pass API KEY here!)
    loader = GoAPILoader(config.API_KEY)
    brain = StrategyEngine()
    risk = RiskGatekeeper(initial_capital)
    
    # 2. Get Data (Full History)
    # Fetch enough data to handle indicators
    df = loader.get_ohlcv(ticker, days=500)
    
    # NOTE: In this simplified backtest, Broker Summary is static (fetched once).
    # For accurate Bandarmology backtest, you need Historical Broker Data.
    broker_data = loader.get_broker_summary(ticker) 
    
    if df.empty or len(df) < 150:
        print("Not enough data to run backtest.")
        return

    # 3. Simulation Loop
    cash = initial_capital
    shares_held = 0
    df['portfolio_value'] = initial_capital
    trade_log = []
    
    # We need at least 150 days for EMA calculation
    start_index = 150
    
    for i in range(start_index, len(df)):
        # "Slice" the data to simulate "Today" (Avoiding Look-ahead Bias)
        current_slice = df.iloc[:i+1].copy()
        current_date = current_slice.iloc[-1]['date']
        current_price = current_slice.iloc[-1]['close']
        
        # Calculate Indicators on the slice
        current_slice = brain.prepare_indicators(current_slice) 
        
        # --- LOGIC CABANG (BRANCHING) ---
        
        # CABANG 1: BELUM PUNYA BARANG (Cari Sinyal Beli)
        if shares_held == 0:
            # Check Signals
            s1, _, _ = brain.analyze_stage2_breakout(current_slice, broker_data)
            s2, _, _ = brain.analyze_stage1_accumulation(current_slice, broker_data)
            signal = s1 or s2
            
            if signal:
                atr = calculate_atr(current_slice).iloc[-1]
                ihsg_mock = loader.get_composite_index() # Mock IHSG/Market Regime
                
                # Risk Check
                approved, reason, lots, sl = risk.validate_entry(
                    ticker, current_price, cash, cash, ihsg_mock, 
                    broker_data['acc_ratio'], broker_data['top_buyer'], atr
                )
                
                if approved and lots > 0:
                    shares_bought = lots * 100
                    cost = shares_bought * current_price
                    # Double check cash logic
                    if cost <= cash:
                        cash -= cost
                        shares_held += shares_bought
                        trade_log.append({
                            'date': current_date, 'action': 'BUY', 'price': current_price, 'shares': shares_bought
                        })
                        print(f"[{current_date.date()}] BUY  @ {current_price:,.0f} | {reason}")

        # CABANG 2: SUDAH PUNYA BARANG (Cek Sinyal Jual / Chandelier Exit)
        elif shares_held > 0:
            # Hitung ATR saat ini
            atr = calculate_atr(current_slice).iloc[-1]
            
            # Hitung Chandelier Stop (Highest High 20 hari terakhir - 3x ATR)
            # Kita pakai tail(20) untuk mensimulasikan 'Highest High Since Entry' secara dinamis
            highest_high = current_slice['high'].tail(20).max()
            stop_price = highest_high - (atr * 3.0) 
            
            # Eksekusi Jual jika harga Close tembus di bawah Stop Price
            if current_price < stop_price:
                revenue = shares_held * current_price
                cash += revenue
                
                # Hitung Profit Trade Ini
                last_buy = [t for t in trade_log if t['action'] == 'BUY'][-1]
                pnl = (current_price - last_buy['price']) / last_buy['price'] * 100
                
                print(f"[{current_date.date()}] SELL @ {current_price:,.0f} | Chandelier Exit Hit (Stop: {stop_price:,.0f}) | PnL: {pnl:.2f}%")
                
                trade_log.append({
                    'date': current_date, 'action': 'SELL', 'price': current_price, 'shares': shares_held
                })
                shares_held = 0
        
        # Track Value (Mark to Market)
        market_value = shares_held * current_price
        total_value = cash + market_value
        df.at[i, 'portfolio_value'] = total_value

    # Summary Result
    final_value = df.iloc[-1]['portfolio_value']
    profit = final_value - initial_capital
    print("-" * 30)
    print(f"FINAL REPORT: {ticker}")
    print(f"Initial: {initial_capital:,.0f}")
    print(f"Final  : {final_value:,.0f}")
    print(f"Profit : {profit:,.0f} ({(profit/initial_capital)*100:.2f}%)")
    print("-" * 30)

if __name__ == "__main__":
    # Test Run
    run_backtest("BBCA")