import os
import httpx
from dotenv import load_dotenv

load_dotenv()


class CryptoManager:
    """Requests, manages, and formats data received from the CoinGecko API"""

    def __init__(self):
        self._cg_endpoint = "https://api.coingecko.com/api/v3"
        self.cg_assets_list = [
            "bitcoin",
            "ethereum",
            "solana",
            "dogecoin",
            "binancecoin",
            "ripple",
            "the-open-network",
            "cardano",
            "tron",
            "avalanche-2",
            "shiba-inu",
            "chainlink",
            "polkadot",
            "uniswap",
            "litecoin",
            "near",
            "monero",
            "pepe",
            "aptos",
            "sui",
            "bittensor",
            "optimism",
            "dogwifcoin",
            "polygon-ecosystem-token",
            "ondo-finance",
            "mother-iggy"
        ]
        self.cg_crypto_data = {}
        self.cg_global_crypto_data = {}
        # TODO: Consider making use of crypto_total_mcap_top10_percents
        self.crypto_total_mcap_top10_percents = None
        # crypto_total_mcap_top10_percents is a dictionary of top-10 cryptos and their percentages of total mcap
        self.crypto_total_mcap = None
        self._cg_header = {
            "x-cg-demo-api-key": os.environ["COINGECKO_API_KEY"],
        }

    async def get_crypto_data(self, asset):
        """Gets user requested data from CoinGecko API and formats into a nested dictionary.
        Also adds commas/punctuation and rounds to two decimal places."""

        # Create empty dictionary entry to ensure emails are the same order/format for every notification
        self.cg_crypto_data[asset] = None
        print(f"Getting data for {asset.title()}...")
        async with httpx.AsyncClient() as client:
            asset_response = await client.get(
                url=f"{self._cg_endpoint}/coins/{asset}",
                headers=self._cg_header,
                params={"id": asset}
            )
        asset_response.raise_for_status()
        data = asset_response.json()

        ticker = data["symbol"]
        ticker_upper = ticker.upper()
        if float(data["market_data"]["current_price"]["usd"]) >= 1:
            price = '${:,.2f}'.format(data["market_data"]["current_price"]["usd"])
        elif float(data["market_data"]["current_price"]["usd"]) >= 0.01:
            price = '${:,.4f}'.format(data["market_data"]["current_price"]["usd"])
        else:
            price = '${:,.8f}'.format(data["market_data"]["current_price"]["usd"])
        mcap = '${:,.2f}'.format(data["market_data"]["market_cap"]["usd"])
        total_volume = '${:,.2f}'.format(data["market_data"]["total_volume"]["usd"])
        change_usd_24h = '{:,.2f}'.format(data["market_data"]["price_change_24h_in_currency"]["usd"])
        change_percent_24h = f"{round(data['market_data']['price_change_percentage_24h'], 2)}"
        change_percent_7d = f"{round(data['market_data']['price_change_percentage_7d'], 2)}"
        change_percent_30d = f"{round(data['market_data']['price_change_percentage_30d'], 2)}"

        asset_dict = {
            "ticker": ticker,
            "ticker_upper": ticker_upper,
            "price": price,
            "mcap": mcap,
            "total_volume": total_volume,
            "24h_change_usd": change_usd_24h,
            "24h_change_percent": change_percent_24h,
            "7d_change_percent": change_percent_7d,
            "30d_change_percent": change_percent_30d,
        }
        self.cg_crypto_data[asset] = asset_dict
        print(f"Updated {asset.title()} data")

    async def get_global_crypto_data(self):
        """Coingecko API request to get data related to entire crypto market"""

        print("Getting global crypto market data...")
        async with httpx.AsyncClient() as client:
            global_response = await client.get(
                url=f"{self._cg_endpoint}/global",
                headers=self._cg_header
            )
        global_response.raise_for_status()
        self.cg_global_crypto_data = global_response.json()
        if self.cg_global_crypto_data["data"]["market_cap_percentage"]:
            self.crypto_total_mcap_top10_percents = self.cg_global_crypto_data["data"]["market_cap_percentage"]
        if self.cg_global_crypto_data["data"]["total_market_cap"]["usd"]:
            self.crypto_total_mcap = '${:,.2f}'.format(self.cg_global_crypto_data["data"]["total_market_cap"]["usd"])
        print("Updated global crypto market data")
