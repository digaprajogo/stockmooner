# main.py
"""
IndoQuantFund Orchestrator
The Main Execution Loop calling all subsystems.
"""

import pandas as pd
import json
import os
from datetime import datetime
from colorama import Fore, Style, init

import config
from data_engine import GoAPILoader
from brain import StrategyEngine
from risk_guard import RiskGatekeeper
from utils import calculate_atr

# Initialize Colorama
init(autoreset=True)

class TradeAudit:
    def __init__(self, log_file='trade_logs.json'):
        self.log_file = log_file
        
    def log(self, data: dict):
        """Saves trade decisions to JSON audit log"""
        logs = []
        if os.path.exists(self.log_file):
            with open(self.log_file, 'r') as f:
                try:
                    logs = json.load(f)
                except json.JSONDecodeError:
                    logs = []
        
        logs.append(data)
        
        with open(self.log_file, 'w') as f:
            json.dump(logs, f, indent=4)

def run_system():
    print(f"{Fore.CYAN}{Style.BRIGHT}🏛️  INDO-QUANT FUND SYSTEM INITIALIZING...{Style.RESET_ALL}")
    print(f"Capital: {config.INITIAL_CAPITAL:,.0f} IDR\n")
    
    # Initialize Core Systems
    data_loader = GoAPILoader()
    brain = StrategyEngine()
    risk_guard = RiskGatekeeper(initial_capital=config.INITIAL_CAPITAL)
    auditor = TradeAudit()
    
    # Simulation State
    current_cash = config.INITIAL_CAPITAL
    current_equity = config.INITIAL_CAPITAL
    
    # 1. Broad Market Context
    print(f"{Fore.YELLOW}[MARKET REGIME CHECK]{Style.RESET_ALL}")
    ihsg_df = data_loader.get_composite_index()
    market_regime = risk_guard.check_market_regime(ihsg_df)
    
    regime_color = Fore.GREEN if market_regime == "BULLISH" else Fore.RED
    print(f"IHSG Regime: {regime_color}{market_regime}{Style.RESET_ALL}\n")
    
    # 2. Watchlist Iteration
    print(f"{Fore.YELLOW}[SCANNING WATCHLIST]{Style.RESET_ALL}")
    
    for ticker in config.WATCHLIST:
        print(f"\nAnalyzing {ticker}...")
        
        # Fetch Data
        df = data_loader.get_ohlcv(ticker)
        broker_data = data_loader.get_broker_summary(ticker)
        
        # Pre-calculate indicators
        df = brain.prepare_indicators(df)
        atr_series = calculate_atr(df)
        current_atr = atr_series.iloc[-1]
        current_price = df.iloc[-1]['close']
        
        print(f"  > Price: {current_price:,.0f} | Top Buyer: {broker_data['top_buyer']} | Acc Ratio: {broker_data['acc_ratio']}")
        
        # --- PYRAMIDING LOGIC (SIMULATED) ---
        # Simulating we already own some and checking if we should add
        # This is a mock check for demonstration logic as requested
        simulated_entry = current_price * 0.85 # Pretend we bought lower
        if current_price > (simulated_entry * 1.10) and broker_data['acc_ratio'] > 1.5:
            print(f"  {Fore.BLUE}[PYRAMIDING SIGNAL] Existing Position Profitable (+{(current_price/simulated_entry - 1)*100:.1f}%) & Accumulation continues. ADDING SIZE.{Style.RESET_ALL}")
        # ------------------------------------

        # --- NEW ENTRY LOGIC ---
        
        # Run Strategies
        s1_signal, s1_ratio, s1_buyer = brain.analyze_stage2_breakout(df, broker_data)
        s2_signal, s2_ratio, s2_buyer = brain.analyze_stage1_accumulation(df, broker_data)
        
        triggered_strategy = None
        if s1_signal:
            triggered_strategy = "Stage 2 Breakout"
        elif s2_signal:
            triggered_strategy = "Silent Accumulation"
            
        if triggered_strategy:
            print(f"  {Fore.MAGENTA}>> SIGNAL DETECTED: {triggered_strategy}{Style.RESET_ALL}")
            
            # Risk Gatekeeper Validation
            is_approved, reason, lots, stop_loss = risk_guard.validate_entry(
                ticker=ticker,
                entry_price=current_price,
                cash_balance=current_cash,
                current_equity=current_equity,
                ihsg_data=ihsg_df,
                bandar_ratio=broker_data['acc_ratio'],
                top_buyer=broker_data['top_buyer'],
                atr_value=current_atr
            )
            
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "ticker": ticker,
                "strategy": triggered_strategy,
                "price": current_price,
                "acc_ratio": broker_data['acc_ratio'],
                "top_buyer": broker_data['top_buyer'],
                "market_regime": market_regime,
                "status": "APPROVED" if is_approved else "REJECTED",
                "reason": reason,
                "lots": lots,
                "stop_loss": stop_loss
            }
            
            if is_approved:
                print(f"  {Fore.GREEN}>> EXECUTING BUY: {lots} Lots @ {current_price} | SL: {stop_loss}{Style.RESET_ALL}")
                print(f"  Reason: {reason}")
                
                # Update Mock Portfolio
                trade_cost = lots * 100 * current_price
                current_cash -= trade_cost
            else:
                print(f"  {Fore.RED}>> REJECTED: {reason}{Style.RESET_ALL}")
                
            auditor.log(log_entry)
            
        else:
            print(f"  No Entry Signal.")

    print(f"\n{Fore.CYAN} स्कैन COMPLETE. Audit saved to trade_logs.json{Style.RESET_ALL}")

if __name__ == "__main__":
    try:
        run_system()
    except Exception as e:
        print(f"{Fore.RED}CRITICAL ERROR: {e}{Style.RESET_ALL}")
