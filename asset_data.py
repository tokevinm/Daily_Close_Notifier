import os
import requests
from dotenv import load_dotenv
load_dotenv()


class DataManager:
    """Requests, manages, and formats data received from the CoinGecko API"""
    def __init__(self):

        self.cg_endpoint = "https://api.coingecko.com/api/v3"
        self.cg_assets_list = [
            "bitcoin",
            "ethereum",
            "solana",
            "dogecoin"
        ]
        self.cg_assets_data = {}
        self.cg_global_data = {}
        self.crypto_mcap_perc_total = None
        self.crypto_total_mcap = None
        # crypto_mcap_perc is a dictionary of top10 assets and percentages of total market cap
        self.cg_header = {
            "x_cg_demo_api_key": os.environ["CG_API_KEY"],
        }


    def get_asset_data(self, asset):
        """Gets user requested data from CoinGecko API and formats it into a dictionary.
        Also adds commas/punctuation and rounds to two decimal places."""
        asset_response = requests.get(
            url=f"{self.cg_endpoint}/coins/{asset}",
            headers=self.cg_header,
            params={"id": asset}
        )
        asset_response.raise_for_status()
        data = asset_response.json()

        ticker = data["symbol"]
        ticker_upper = ticker.upper()
        if float(data["market_data"]["current_price"]["usd"]) >= 1:
            price = '${:,.2f}'.format(data["market_data"]["current_price"]["usd"])
        else:
            price = '${:,.4f}'.format(data["market_data"]["current_price"]["usd"])
        mcap = '${:,.2f}'.format(data["market_data"]["market_cap"]["usd"])
        total_volume = '${:,.2f}'.format(data["market_data"]["total_volume"]["usd"])
        change_usd_24h = '${:,.2f}'.format(data["market_data"]["price_change_24h_in_currency"]["usd"])
        change_percent_24h = f"{round(data["market_data"]["price_change_percentage_24h"], 2)}"
        change_percent_7d = f"{round(data["market_data"]["price_change_percentage_7d"], 2)}"
        change_percent_30d = f"{round(data["market_data"]["price_change_percentage_30d"], 2)}"

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
        return asset_dict

    def format_asset_data(self):
        """Consolidates asset data into a single dictionary to be accessed"""
        for i in range(len(self.cg_assets_list)):
            self.cg_assets_data[self.cg_assets_list[i]] = self.get_asset_data(self.cg_assets_list[i])
        return self.cg_assets_data

    def update_global_data(self):
        """API request to get data related to entire crypto market"""
        global_response = requests.get(
            url=f"{self.cg_endpoint}/global",
            headers=self.cg_header
        )
        global_response.raise_for_status()
        self.cg_global_data = global_response.json()
        if self.cg_global_data["data"]["market_cap_percentage"]:
            self.crypto_mcap_perc_total = self.cg_global_data["data"]["market_cap_percentage"]
        if self.cg_global_data["data"]["total_market_cap"]["usd"]:
            self.crypto_total_mcap = '${:,.2f}'.format(self.cg_global_data["data"]["total_market_cap"]["usd"])
