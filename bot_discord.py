import os
import time
import requests
from discord_webhook import DiscordWebhook, DiscordEmbed

# -------------------------
# Environment variables
# -------------------------
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
if not WEBHOOK_URL:
    raise Exception("Please set DISCORD_WEBHOOK_URL in Replit Secrets")

# -------------------------
# CoinGecko API
# -------------------------
COINGECKO_TOP_URL = "https://api.coingecko.com/api/v3/coins/markets"
COINGECKO_PARAMS = {
    "vs_currency": "usd",
    "order": "market_cap_desc",
    "per_page": 50,
    "page": 1,
    "sparkline": "false"
}

# -------------------------
# Settings
# -------------------------
CHECK_INTERVAL = 60 * 5  # 5 minutes

# -------------------------
# Helper Functions
# -------------------------
def fetch_top_50():
    response = requests.get(COINGECKO_TOP_URL, params=COINGECKO_PARAMS)
    data = response.json()
    return data

def check_signals(coin):
    # Signals
    signals = []

    if coin["price_change_percentage_1h_in_currency"] and coin["price_change_percentage_1h_in_currency"] > 2:
        signals.append("1H +2%")

    if coin["price_change_percentage_24h_in_currency"] and coin["price_change_percentage_24h_in_currency"] > 10:
        signals.append("24H +10%")

    if coin["total_volume"] and coin["total_volume"] > 50000000:
        signals.append("High Volume")

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

# -------------------------
# Main Loop
# -------------------------
def main():
    while True:
        try:
            coins = fetch_top_50()

            for coin in coins:
                signals = check_signals(coin)
                if len(signals) >= 2:  # only alert if 2+ signals
                    send_discord_alert(coin, signals)

        except Exception as e:
            print("Error:", e)

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
