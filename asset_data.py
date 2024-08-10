import os
import requests
from dotenv import load_dotenv
load_dotenv()


class DataManager:
    """Requests, manages, and formats data received from the CoinGecko API"""
    def __init__(self):

        self.cg_endpoint = "https://api.coingecko.com/api/v3"
        self.cg_asset_data = {}
        self.cg_global_data = {}
        self.crypto_mcap_perc_total = None
        # crypto_mcap_perc is a dictionary of top10 assets and percentages of total market cap
        self.cg_header = {
            "x_cg_demo_api_key": os.environ["CG_API_KEY"],
        }

    def update_asset_data(self):
        """API request to get relevant data for assets selected by users during sign-up"""
        asset_params = {
            "ids": "bitcoin,ethereum,solana,dogecoin",
            "vs_currencies": "usd",
            "include_market_cap": "true",
            "include_24hr_change": "true",
            "include_24h_vol": "true",
            "include_last_updated_at": "true",
        }
        asset_response = requests.get(
            url=f"{self.cg_endpoint}/simple/price",
            headers=self.cg_header,
            params=asset_params
        )
        asset_response.raise_for_status()
        self.cg_asset_data = asset_response.json()

    def update_global_data(self):
        """API request to get data related to entire crypto market"""
        global_response = requests.get(
            url=f"{self.cg_endpoint}/global",
            headers=self.cg_header
        )
        global_response.raise_for_status()
        self.cg_global_data = global_response.json()
        self.crypto_mcap_perc_total = self.cg_global_data["data"]["market_cap_percentage"]

    def format_data(self, asset, asset_ticker):
        """Formats data into a more readable format. Adds commas/punctuation and rounds to two decimal places."""
        asset_dict = {"price": '${:,.2f}'.format(self.cg_asset_data[asset]["usd"]),
                      "mcap": '${:,.2f}'.format(self.cg_asset_data[asset]["usd_market_cap"]),
                      "24h_change_percent": f"{round(self.cg_asset_data[asset]["usd_24h_change"], 2)}",
                      "percent_of_total_mcap": f"{round(self.crypto_mcap_perc_total[asset_ticker], 2)}%"
                      }
        return asset_dict

    def daily_icon(self, percent_change):
        """Takes the 24h % change in price and returns an icon to make it easier
        to discern divergences between assets/asset classes"""
        if float(percent_change) > 0:
            icon = "🔺"
        elif float(percent_change) < 0:
            icon = "🔻"
        else:
            icon = ""
        return icon
