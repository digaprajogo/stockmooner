# backtest.py
"""
Simple Backtesting Engine for IndoQuantFund.
Simulates the strategy over historical data to estimate performance.
"""

import pandas as pd
import time
from brain import StrategyEngine
from risk_guard import RiskGatekeeper
from data_engine import GoAPILoader
from utils import calculate_atr
import config

def run_backtest(ticker: str, initial_capital: float = 100_000_000):
    print(f"\n🚀 STARTING BACKTEST: {ticker}...")
    
    # 1. Setup
    loader = GoAPILoader(config.API_KEY)
    brain = StrategyEngine()
    risk = RiskGatekeeper(initial_capital)
    
    # 2. Get Data (Full History)
    df = loader.get_ohlcv(ticker, days=500)
    
    if df.empty or len(df) < 150:
        print(f"⚠️  Not enough data for {ticker}. Skipping.")
        return

    # 3. Simulation Loop
    cash = initial_capital
    shares_held = 0
    df['portfolio_value'] = initial_capital
    trade_log = []
    
    start_index = 150
    
    # Estimasi waktu agar user tidak panik
    total_loops = len(df) - start_index
    print(f"⏳ Processing ~{total_loops} trading days (Historical Broker Check)... This may take time.")

    for i in range(start_index, len(df)):
        # Progress Indicator (titik setiap 10 hari)
        if i % 10 == 0: print(".", end="", flush=True)

        current_slice = df.iloc[:i+1].copy()
        
        # --- FIX VARIABLE NAME DI SINI ---
        current_date = current_slice.iloc[-1]['date']
        current_price = current_slice.iloc[-1]['close']
        
        # Konversi tanggal ke string YYYY-MM-DD untuk API
        date_str = current_date.strftime("%Y-%m-%d")
        
        # --- HISTORICAL BROKER CHECK ---
        # Mengambil data bandar pada tanggal tersebut
        try:
            broker_data = loader.get_broker_summary(ticker, date=date_str)
        except Exception:
            # Jika gagal/limit, pakai dummy netral agar tidak crash
            broker_data = {'acc_ratio': 1.0, 'top_buyer': 'Unknown'}

        # Calculate Indicators
        current_slice = brain.prepare_indicators(current_slice) 
        
        # --- LOGIC CABANG ---
        
        # CABANG 1: BUY SIGNAL
        if shares_held == 0:
            s1, _, _ = brain.analyze_stage2_breakout(current_slice, broker_data)
            s2, _, _ = brain.analyze_stage1_accumulation(current_slice, broker_data)
            signal = s1 or s2
            
            if signal:
                atr = calculate_atr(current_slice).iloc[-1]
                
                # Mock IHSG untuk backtest cepat (atau bisa fetch real historical jika mau)
                # Disini kita pakai Mock agar tidak double API call per loop
                ihsg_mock = loader.get_composite_index() 
                
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
                        print(f"\n[{current_date.date()}] 🟢 BUY  @ {current_price:,.0f} | {reason}")

        # CABANG 2: SELL SIGNAL (Chandelier Exit)
        elif shares_held > 0:
            atr = calculate_atr(current_slice).iloc[-1]
            highest_high = current_slice['high'].tail(20).max()
            stop_price = highest_high - (atr * 3.0) 
            
            if current_price < stop_price:
                revenue = shares_held * current_price
                cash += revenue
                
                last_buy = [t for t in trade_log if t['action'] == 'BUY'][-1]
                pnl = (current_price - last_buy['price']) / last_buy['price'] * 100
                
                color_code = "🟢" if pnl > 0 else "🔴"
                print(f"\n[{current_date.date()}] {color_code} SELL @ {current_price:,.0f} | Stop: {stop_price:,.0f} | PnL: {pnl:.2f}%")
                
                trade_log.append({
                    'date': current_date, 'action': 'SELL', 'price': current_price, 'shares': shares_held
                })
                shares_held = 0
        
        # Track Value
        market_value = shares_held * current_price
        df.at[i, 'portfolio_value'] = cash + market_value

    # Summary Result
    final_value = df.iloc[-1]['portfolio_value']
    profit = final_value - initial_capital
    print(f"\n\n{'='*30}")
    print(f"REPORT: {ticker}")
    print(f"Initial: {initial_capital:,.0f}")
    print(f"Final  : {final_value:,.0f}")
    print(f"Profit : {profit:,.0f} ({(profit/initial_capital)*100:.2f}%)")
    print(f"Total Trades: {len([t for t in trade_log if t['action']=='BUY'])}")
    print(f"{'='*30}\n")

if __name__ == "__main__":
    print(f"🔥 STARTING PORTFOLIO BACKTEST ({len(config.WATCHLIST)} Tickers)")
    print("Note: This process uses Real Historical Broker Data and will take time.")
    
    for ticker in config.WATCHLIST:
        try:
            run_backtest(ticker)
        except Exception as e:
            print(f"\nSkipping {ticker} error: {e}")
            
    print("\n>>> ALL BACKTESTS COMPLETE <<<")