import os
import time
import requests
from discord_webhook import DiscordWebhook, DiscordEmbed

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
if not WEBHOOK_URL:
    raise Exception("Please set DISCORD_WEBHOOK_URL in Replit Secrets")

COINGECKO_TOP_URL = "https://api.coingecko.com/api/v3/coins/markets"
COINGECKO_PARAMS = {
    "vs_currency": "usd",
    "order": "market_cap_desc",
    "per_page": 50,
    "page": 1,
    "sparkline": "false",
    "price_change_percentage": "1h,24h,7d"
}

CHECK_INTERVAL = 60 * 5  # 5 minutes

def fetch_top_50():
    response = requests.get(COINGECKO_TOP_URL, params=COINGECKO_PARAMS)
    data = response.json()
    return data

def check_signals(coin):
    signals = []

    # 1H +2%
    if coin.get("price_change_percentage_1h_in_currency", 0) > 2:
        signals.append("1H +2%")

    # 24H +10%
    if coin.get("price_change_percentage_24h_in_currency", 0) > 10:
        signals.append("24H +10%")

    # 7D +20%
    if coin.get("price_change_percentage_7d_in_currency", 0) > 20:
        signals.append("7D +20%")

    # Volume spike (3x)
    if coin.get("total_volume") and coin.get("market_cap"):
        avg_volume = coin["market_cap"] / 100  # rough approximation
        if coin["total_volume"] > avg_volume * 3:
            signals.append("Volume Spike")

    # Market cap growth (10%+ in 24h)
    if coin.get("market_cap_change_percentage_24h", 0) > 10:
        signals.append("Market Cap +10%")

    # Big drop -10%
    if coin.get("price_change_percentage_24h_in_currency", 0) < -10:
        signals.append("24H -10% Drop")

    # Near ATH
    if coin.get("ath") and coin.get("current_price"):
        if coin["current_price"] >= coin["ath"] * 0.95:
            signals.append("Near ATH")

    return signals

def send_discord_alert(coin, signals):
    webhook = DiscordWebhook(url=WEBHOOK_URL)
    embed = DiscordEmbed(
        title=f"🚀 Coin Alert: {coin['name']} ({coin['symbol'].upper()})",
        description="Multiple signals aligned!",
        color=0x00ff00
    )

    embed.add_embed_field(name="Price", value=f"${coin['current_price']:,}", inline=True)
    embed.add_embed_field(name="Market Cap", value=f"${coin['market_cap']:,}", inline=True)
    embed.add_embed_field(name="Signals", value=", ".join(signals), inline=False)

    webhook.add_embed(embed)
    webhook.execute()

def main():
    while True:
        try:
            coins = fetch_top_50()

            for coin in coins:
                signals = check_signals(coin)
                if len(signals) >= 2:
                    send_discord_alert(coin, signals)

        except Exception as e:
            print("Error:", e)

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
