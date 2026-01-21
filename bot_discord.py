import time
import requests
import pandas as pd
from discord_webhook import DiscordWebhook

DISCORD_WEBHOOK = "YOUR_DISCORD_WEBHOOK_URL"
SCORE_THRESHOLD = 6
CHECK_INTERVAL_SECONDS = 600  # 10 minutes (slower)

def send_discord(message: str) -> None:
    webhook = DiscordWebhook(url=DISCORD_WEBHOOK, content=message)
    webhook.execute()

def get_top_50() -> list:
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": 50, "page": 1}

    response = requests.get(url, params=params)
    if response.status_code != 200:
        print("Error fetching top 50:", response.status_code, response.text[:100])
        return []

    data = response.json()
    if not isinstance(data, list):
        print("Top 50 response not list:", data)
        return []

    return data

def calculate_rsi(prices: list) -> float:
    s = pd.Series(prices)
    delta = s.diff().dropna()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = -delta.where(delta < 0, 0).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

def run() -> None:
    while True:
        coins = get_top_50()
        if not coins:
            time.sleep(CHECK_INTERVAL_SECONDS)
            continue

        for coin in coins:
            symbol = coin["symbol"].upper()
            price = coin["current_price"]
            market_cap = coin["market_cap"]
            volume = coin["total_volume"]

            # Use CoinGecko data already returned (no extra API calls)
            score = 0
            reasons = []

            if volume > market_cap * 0.05:
                score += 2
                reasons.append("Volume Spike")

            rsi = calculate_rsi([p["current_price"] for p in coins])
            if rsi < 30 or rsi > 70:
                score += 1
                reasons.append("RSI Extreme")

            if market_cap > 10_000_000_000:
                score += 1
                reasons.append("Big Market Cap")

            if score >= SCORE_THRESHOLD:
                msg = (
                    f"🚨 ALERT: {symbol}\n"
                    f"Price: ${price}\n"
                    f"Score: {score}\n"
                    f"Reasons: {', '.join(reasons)}"
                )
                send_discord(msg)

        time.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    run()
