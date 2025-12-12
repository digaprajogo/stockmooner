# IndoQuantFund Implementation Walkthrough

## Overview

This document details the implementation of the IndoQuantFund, an institutional-grade algorithmic trading system for the Indonesia Stock Exchange (IDX). The system implements rigorous "Bandarmology" (smart money flow) analysis combined with technical indicators and a robust risk management engine.

## System Architecture

The project is structured into 6 modular Python files:

1.  **`config.py`**: Central configuration for API keys, capital, risk settings, and broker whitelists/blacklists (Smart Money vs. Retail).
2.  **`utils.py`**: Helper functions, including a custom `round_to_tick` function that strictly adheres to IDX price fraction rules, and manual implementations of ATR and EMA calculations.
3.  **`data_engine.py`**: Handles data retrieval. Currently features a **Mock Data Generator** that creates realistic random walks for OHLCV and random broker accumulation scenarios to test strategy logic without live API access.
4.  **`brain.py`**: The Alpha Engine. Implements two core strategies:
    - `analyze_stage2_breakout`: Detects uptrending stocks (EMA 50 > 150) undergoing accumulation.
    - `analyze_stage1_accumulation`: Detects bottom reversals with volatility squeezes (BB Width < 0.15) and Smart Money buying.
5.  **`risk_guard.py`**: The "200 IQ" Gatekeeper.
    - **Market Regime**: Checks IHSG vs EMA(200). If Bearish ("DEFENSIVE"), cuts position sizes by 50%.
    - **Bad Actor Filter**: Rejects trades if the Top Buyer is a known Retail broker (e.g., YP, PD).
    - **Dynamic Sizing**: Increases risk to 3% for high-conviction setups (Bandar Ratio > 2.5), otherwise defaults to 1.5%.
    - **Chandelier Stop**: Calculates trailing stops using 3x ATR.
6.  **`main.py`**: The Orchestrator. Runs the main loop:
    - Checks Market Regime.
    - Scans Watchlist.
    - Simulates Pyramiding logic.
    - Validates signals via Risk Guard.
    - Logs trades to `trade_logs.json`.

## Verification & "Pre-Flight" Checks

We performed a strict verification against the "Grandmaster Checklist":

- **No "Lazy AI" code**: All mathematical logic (EMA, ATR, Tick Rounding, Position Sizing) is fully written out.
- **Market Regime Active**: The `RiskGatekeeper` actively checks IHSG data and adjusts lot sizes.
- **Mock Data**: The system runs standalone (no API key needed for demo) using robust mock data generation.
- **Dependencies**: `pandas`, `numpy`, and `colorama` are required and installed.
- **Auditing**: Trades are saved to a JSON log file.

## How to Run

1.  Navigate to the project directory:
    ```bash
    cd indo_quant_fund
    ```
2.  Set up the environment:

    ```bash
    # Create and activate virtual environment
    python3 -m venv .venv
    source .venv/bin/activate

    # Install dependencies
    pip install -r requirements.txt
    ```

    _Note: If `source` doesn't work, try `. .venv/bin/activate` or call the python executable directly: `./.venv/bin/python`_

3.  Execute the system:
    ```bash
    # Ensure you are permitted to execute
    python3 main.py
    # OR if using the explicit venv path:
    ./.venv/bin/python main.py
    ```

You should see colorful console output indicating the Market Regime, individual stock analysis, and any Approved/Rejected trade signals.
