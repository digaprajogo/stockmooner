# IndoQuantFund Implementation Plan

## Goal

Build an institutional-grade algorithmic trading system for the Indonesia Stock Exchange (IDX) with specific "Bandarmology" and Risk Management logic.

## Architecture

The system will be modular, consisting of 6 Python files in the `indo_quant_fund/` directory.

### 1. `config.py`

- **Constants**: API_KEY, INITIAL_CAPITAL (200M IDR).
- **Risk**: BASE_RISK (1.5%), AGGRESSIVE_RISK (3.0%).
- **Broker Lists**: SMART_MONEY vs RETAIL_CROWD lists.

### 2. `utils.py`

- **Tick Engine**: `round_to_tick(price)` complying with IDX fractions (<200, 200-500, etc.).
- **Indicators**: `calculate_atr` and `calculate_ema` using pandas.

### 3. `data_engine.py`

- **GoAPILoader**:
  - `get_ohlcv(ticker)`: Returns DataFrame with Open, High, Low, Close, Volume. Uses mock data for reliability.
  - `get_broker_summary(ticker)`: Returns broker accumulation data (Top Buyer, Acc_Ratio). Mocked.
  - `get_composite_index()`: Returns IHSG data for Market Regime. Mocked.

### 4. `brain.py` (Alpha Engine)

- **StrategyEngine**:
  - `analyze_stage2_breakout`: EMA Trends + Bandarmology (Acc_Ratio > 1.5, Buyer != Retail).
  - `analyze_stage1_accumulation`: BB Squeeze + Price Low + Smart Money Accumulation.

### 5. `risk_guard.py` (Gatekeeper)

- **RiskGatekeeper**:
  - `check_market_regime`: Checks IHSG vs EMA(200). Returns "DEFENSIVE" or "BULLISH".
  - `validate_entry`:
    - Adjusts Lot Size based on Regime (50% cut if Defensive).
    - Dynamic Sizing (aggressive if Acc_Ratio > 2.5).
    - Rejects Retail Top Buyer or Insufficient Cash.
  - `calculate_chandelier_stop`: ATR \* 3.0 trailing stop.

### 6. `main.py` (Orchestrator)

- **TradeAudit**: Logs to JSON.
- **Workflow**:
  1. Check IHSG -> Set Regime.
  2. Loop Watchlist.
  3. Check Pyramiding (Simulated).
  4. Run Brain Strategies.
  5. Run Risk Validator.
  6. Execute/Log.

## Execution Steps

1. Create `config.py`.
2. Create `utils.py`.
3. Create `data_engine.py` with mock data generation.
4. Create `brain.py` with strategy logic.
5. Create `risk_guard.py` with regime and sizing logic.
6. Create `main.py` to tie it all together.
