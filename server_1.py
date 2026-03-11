"""
BIST Yahoo Finance Proxy Backend
Kurulum: pip install flask flask-cors yfinance
Çalıştır: python server.py
"""

from flask import Flask, jsonify
from flask_cors import CORS
import yfinance as yf
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Frontend'den erişim için

BIST_TICKERS = {
    "THYAO": "THYAO.IS",
    "GARAN": "GARAN.IS",
    "ASELS": "ASELS.IS",
    "SISE":  "SISE.IS",
    "EREGL": "EREGL.IS",
    "KCHOL": "KCHOL.IS",
    "BIMAS": "BIMAS.IS",
    "AKBNK": "AKBNK.IS",
    "YKBNK": "YKBNK.IS",
    "TOASO": "TOASO.IS",
    "SAHOL": "SAHOL.IS",
    "PGSUS": "PGSUS.IS",
}

@app.route("/api/stock/<ticker>")
def get_stock(ticker):
    """Tek hisse anlık veri + 60 günlük geçmiş"""
    symbol = BIST_TICKERS.get(ticker.upper())
    if not symbol:
        return jsonify({"error": "Hisse bulunamadı"}), 404

    try:
        t = yf.Ticker(symbol)
        info = t.info
        hist = t.history(period="3mo", interval="1d")

        candles = []
        for date, row in hist.iterrows():
            candles.append({
                "date": date.strftime("%Y-%m-%d"),
                "open":  round(float(row["Open"]), 2),
                "high":  round(float(row["High"]), 2),
                "low":   round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "vol":   int(row["Volume"]),
            })

        prev_close = info.get("previousClose") or (candles[-2]["close"] if len(candles) >= 2 else 0)
        curr_price = info.get("currentPrice") or info.get("regularMarketPrice") or candles[-1]["close"]
        change_pct = round((curr_price - prev_close) / prev_close * 100, 2) if prev_close else 0

        return jsonify({
            "ticker": ticker.upper(),
            "name":   info.get("longName", ticker),
            "sector": info.get("sector", "—"),
            "price":  round(curr_price, 2),
            "change": change_pct,
            "pe":     round(info.get("trailingPE") or 0, 1),
            "pb":     round(info.get("priceToBook") or 0, 2),
            "marketCap": info.get("marketCap", 0),
            "volume": info.get("regularMarketVolume", 0),
            "fiftyTwoWeekHigh": info.get("fiftyTwoWeekHigh", 0),
            "fiftyTwoWeekLow":  info.get("fiftyTwoWeekLow", 0),
            "candles": candles,
            "updatedAt": datetime.now().isoformat(),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/stocks")
def get_all_stocks():
    """Tüm hisselerin özet verisi (sidebar için)"""
    result = {}
    for ticker in BIST_TICKERS:
        try:
            symbol = BIST_TICKERS[ticker]
            t = yf.Ticker(symbol)
            info = t.info
            hist = t.history(period="5d", interval="1d")

            curr = info.get("currentPrice") or info.get("regularMarketPrice") or 0
            prev = info.get("previousClose") or 0
            change = round((curr - prev) / prev * 100, 2) if prev else 0

            mini = [{"close": round(float(r["Close"]), 2)} for _, r in hist.iterrows()]

            result[ticker] = {
                "name":   info.get("shortName", ticker),
                "price":  round(curr, 2),
                "change": change,
                "mini":   mini,
            }
        except:
            result[ticker] = {"name": ticker, "price": 0, "change": 0, "mini": []}

    return jsonify(result)


@app.route("/api/tickers")
def get_tickers():
    return jsonify(list(BIST_TICKERS.keys()))


if __name__ == "__main__":
    print("🚀 BIST Backend başlatılıyor: http://localhost:5000")
    app.run(debug=True, port=5000)
