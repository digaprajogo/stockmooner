Tinggal ubah codingan terakhir

dari hanya mencari call dari watchlist, ditambah bisa cari call dari semua saham dibuang liquidity

masukan prompt ini ke antigravity

- **Live Trading (`main.py`):** Gunakan **"Jaring Raksasa"** . Scan 800+ saham, tapi pasang filter likuiditas di depan agar tidak membuang waktu di saham "zombie" (saham gocap mati).
- **Backtesting (`backtest.py`):** Gunakan **"Sniper Scope"** . Hanya test di watchlist terpilih untuk validasi strategi, karena backtest makan waktu dan kuota.

Berikut adalah cara mengubah kode Anda untuk mengakomodasi request ini:

### 1. Update `data_engine.py` (Agar Bisa Tarik Semua Saham)

Kita butuh fungsi baru untuk menyedot daftar seluruh emiten dari Bursa Efek.

Buka `data_engine.py` dan tambahkan method ini di dalam class `GoAPILoader`:

**Python**

```
    def get_all_tickers_web(self) -> list:
        """
        Mengambil daftar SELURUH saham yang ada di IDX via GoAPI.
        Digunakan untuk Live Scanning (Jaring Raksasa).
        """
        url = "https://api.goapi.id/v1/stock/idx/companies"
        params = {"api_key": self.api_key}

        try:
            response = requests.get(url, params=params)
            data = response.json()

            if data['status'] == 'success':
                results = data['data']['results']
                # Ambil semua ticker yang ada
                all_tickers = [item['ticker'] for item in results]
                return all_tickers
            else:
                print(f"Error fetching tickers: {data['message']}")
                return config.WATCHLIST # Fallback ke watchlist jika API error
        except Exception as e:
            print(f"Connection Error: {e}")
            return config.WATCHLIST
```

### 2. Update `main.py` (Scanner Jaring Raksasa)

Di sini kuncinya. Kita tidak pakai `config.WATCHLIST`, tapi pakai `get_all_tickers_web()`.

**TAPI HATI-HATI:** Menganalisa 800 saham satu per satu akan sangat lama.
**SOLUSI:** Tambahkan **"Filter Sampah" (Liquidity Check)** di awal loop. Jika transaksi harian < 1 Miliar, langsung SKIP. Jangan buang kuota API bandar untuk saham sepi.

Copy-paste update ini ke `main.py` (Gantikan loop lama):

**Python**

```
    # ... (kode atas sama) ...

    # 2. Watchlist Iteration
    print(f"{Fore.YELLOW}[SCANNING MARKET UNIVERSE]{Style.RESET_ALL}")

    # ---------------------------------------------------------
    # UBAH DISINI: Ambil semua saham, bukan cuma watchlist
    print("⏳ Fetching all IDX tickers...")
    universe_tickers = data_loader.get_all_tickers_web()
    print(f"🎯 Total Saham Terdeteksi: {len(universe_tickers)}")
    # ---------------------------------------------------------

    for ticker in universe_tickers:
        # Progress bar sederhana
        print(f"Scanning {ticker}...", end='\r')

        # 1. Fetch Data Harga Dulu (Murah/Cepat)
        df = data_loader.get_ohlcv(ticker)

        if df.empty or len(df) < 50:
            continue

        # --- FILTER SAMPAH (LIQUIDITY FILTER) ---
        # Hitung rata-rata transaksi 5 hari terakhir
        last_close = df.iloc[-1]['close']
        avg_vol = df['volume'].tail(5).mean()
        avg_value = last_close * avg_vol

        # ATURAN: Jika transaksi rata-rata < 1 Miliar Rupiah, SKIP!
        # Ini biar robot gak beli saham gocap/saham kuburan.
        if avg_value < 1_000_000_000:
            continue
        # ----------------------------------------

        # 2. Jika Lolos Filter Sampah, Baru Tarik Data Bandar (Mahal/Kuota)
        broker_data = data_loader.get_broker_summary(ticker)

        # Pre-calculate indicators
        df = brain.prepare_indicators(df)
        atr_series = calculate_atr(df)
        current_atr = atr_series.iloc[-1]
        current_price = df.iloc[-1]['close']

        # ... (SISA KODE SAMA PERSIS DENGAN SEBELUMNYA) ...
        # ... Logic Pyramiding, Logic Entry, Audit, dll ...
```

### 3. File `backtest.py` (Tetap Fokus)

File `backtest.py` **TIDAK PERLU DIUBAH** .
Biarkan dia tetap menggunakan `config.WATCHLIST`.

**Python**

```
if __name__ == "__main__":
    # Backtest hanya saham-saham pilihan di config
    for ticker in config.WATCHLIST:
        run_backtest(ticker)
```

---

### Hasil Akhir Strategi Anda:

1. **Saat Run (`python main.py`):**
   - Robot mengambil 800+ saham.
   - Dia membuang 500 saham "sampah" (transaksi sepi) dalam hitungan milidetik.
   - Dia menganalisa mendalam 300 saham sisanya (Liquid).
   - Dia memberikan Anda sinyal "The Best of The Best" hari ini.
2. **Saat Backtest (`python backtest.py`):**
   - Robot hanya menguji saham yang Anda tulis di `config.py` (misal BBCA, BRMS) untuk memastikan strategi trend & bandarmology-nya valid secara historis.

**Penting:** Saat menjalankan `main.py` pertama kali dengan mode "All Tickers", mungkin butuh waktu 10-20 menit untuk scan seluruh pasar (karena ada jeda koneksi internet). Itu normal. Biarkan laptop menyala.
