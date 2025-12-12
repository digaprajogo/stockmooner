# data_engine.py
"""
Data Engine for IndoQuantFund.
Handles data fetching from External APIs (GoAPI) or generates mock data for testing.
"""

import requests # Make sure to import this at the top
import pandas as pd
import numpy as np
import random
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import config

class GoAPILoader:
    def __init__(self, api_key: str = config.API_KEY):
        self.api_key = api_key

    
data_engine.py
 and update the 
get_ohlcv
 method:

    def get_ohlcv(self, ticker: str, days: int = 365) -> pd.DataFrame:
        """
        Fetches Real Data from GoAPI.
        """
        # Calculate Date Range
        to_date = datetime.now().strftime("%Y-%m-%d")
        from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        url = f"https://api.goapi.id/v1/stock/idx/{ticker}/historical"
        params = {
            "api_key": self.api_key,
            "from": from_date,
            "to": to_date
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if data['status'] == 'success':
                results = data['data']['results']
                df = pd.DataFrame(results)
                # GoAPI returns: date, open, high, low, close, volume
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date').reset_index(drop=True)
                
                # Ensure numeric columns are floats
                cols = ['open', 'high', 'low', 'close', 'volume']
                df[cols] = df[cols].apply(pd.to_numeric)
                
                return df
            else:
                print(f"API Error for {ticker}: {data['message']}")
                return pd.DataFrame() # Return empty on failure
                
        except Exception as e:
            print(f"Connection Error: {e}")
            return pd.DataFrame()

    def get_broker_summary(self, ticker: str) -> Dict:
        """
        Fetches Broker Summary (Bandarmology Data).
        MOCKS data to test different scenarios.
        """
        
        # Default Logic
        scenario = random.choice(['accumulation', 'distribution', 'neutral'])
        brokers = config.SMART_MONEY + config.RETAIL_CROWD
        
        if scenario == 'accumulation':
            top_buyer = random.choice(config.SMART_MONEY)
            acc_ratio = random.uniform(1.6, 3.5)
        elif scenario == 'distribution':
            top_buyer = random.choice(config.RETAIL_CROWD)
            acc_ratio = random.uniform(0.5, 1.2)
        else:
            top_buyer = random.choice(brokers)
            acc_ratio = random.uniform(0.9, 1.4)

        # Overwrite for BBCA Demo
        if ticker == 'BBCA':
             acc_ratio = 3.0
             top_buyer = 'AK' 
            
        return {
            'ticker': ticker,
            'top_buyer': top_buyer,
            'acc_ratio': round(acc_ratio, 2),
            'date': datetime.now().strftime('%Y-%m-%d')
        }

    def get_composite_index(self, days: int = 300) -> pd.DataFrame:
        """
        Fetches IHSG (Composite Index) data for Market Regime analysis.
        """
        # Similar mock generation for IHSG
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        dates = pd.date_range(start=start_date, end=end_date, freq='B')
        
        # IHSG usually around 6000-7500
        base_price = 7200
        prices = []
        price = base_price
        
        for _ in range(len(dates)):
            change = random.uniform(-0.01, 0.01) # Less volatile than individual stocks
            price = price * (1 + change)
            prices.append(price)
            
        df = pd.DataFrame({
            'date': dates,
            'close': prices
        })
        
        return df

    def check_corporate_action(self, ticker: str) -> bool:
        """
        Checks for Dividends, Rights Issue, etc.
        """
        # Placeholder as requested
        return False
