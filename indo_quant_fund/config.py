# config.py
"""
Configuration Constants for IndoQuantFund
Includes Risk Settings, Capital, and Broker Classifications.
"""

# ==========================================
# SYSTEM SETTINGS
# ==========================================
API_KEY = "YOUR_GOAPI_KEY_HERE"
INITIAL_CAPITAL = 200_000_000  # 200 Million IDR

# ==========================================
# RISK MANAGEMENT SETTINGS
# ==========================================
BASE_RISK_PER_TRADE = 0.015  # 1.5% of Equity per trade
AGGRESSIVE_RISK = 0.03       # 3.0% for High Conviction setups

# ==========================================
# BROKER CLASSIFICATIONS (BANDARMOLOGY)
# ==========================================

# Smart Money / Institutional Brokers (The "Bandar")
# Includes Foreign Institutional (AK, BK, ZP, RX, KZ) and Local Big Players (CS, DX, etc.)
SMART_MONEY = [
    'AK', 'BK', 'CC', 'ZP', 'RX', 'KZ', 
    'DX', 'CS', 'CG', 'YU', 'LG', 'KI'
]

# Retail Crowd (The "Herd")
# Brokers typically used by retail traders. High buying here often indicates distributed supply.
RETAIL_CROWD = [
    'YP', 'PD', 'XC', 'NI', 'KK', 'XL', 'SQ'
]

# ==========================================
# WATCHLIST
# ==========================================
WATCHLIST = ['GTSI', 'BUMI', 'BRMS', 'BBCA', 'MDKA']
