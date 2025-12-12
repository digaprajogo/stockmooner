# 🚀 Going Production & Backtesting Guide

## 1. Production Setup (Real Data)

To trade with real market data, you need to replace the "Mock Data" engine with a real connection to the Indonesia Stock Exchange (IDX).

### Step A: Get an API Key

We recommend **GoAPI.id** for affordable IDX data.

1. Register at [goapi.id](https://goapi.id).
2. Get your **API KEY**.
3. Open `config.py` and paste it:
   ```python
   API_KEY = "YOUR_REAL_API_KEY_HERE"
   ```

### Step B: Update `data_engine.py`

You need to replace the random generator with this code that fetches real data.

**Open `data_engine.py` and update the `get_ohlcv` method:**

```python
import requests # Make sure to import this at the top

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
```

---

## 2. Backtesting (How to do it?)

**Concept**
Backtesting means "Pretending today is 1 year ago, running the strategy, moving to the next day, and repeating until today."

**The Script**
I have created a file named `backtest.py` for you.

**How to run it:**

```bash
./.venv/bin/python backtest.py
```

**How it works:**

1. It loads 500 days of history (Mock or Real).
2. It starts at Day 150 (needed for EMA indicators).
3. It loops Day-by-Day.
4. **BUY Logic:** If `brain.py` says BUY and we have cash -> Buy.
5. **SELL Logic:** For simplicity, I added a rule: "Sell if price drops below EMA(50)".
6. It prints the final Profit/Loss.

**Note on Data:**
Ideally, for backtesting "Bandarmology" (Broker Summary), you need a **historical database** of Broker Summaries for every single day. GoAPI typically provides _current_ broker summary. For accurate backtesting, you would need to save that data effectively explicitly every day to build your own database.
