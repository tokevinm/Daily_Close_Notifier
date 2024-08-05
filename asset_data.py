import os
import requests
from dotenv import load_dotenv


class DataManager:
    def __init__(self):

        self.cg_endpoint = "https://api.coingecko.com/api/v3"
        self.crypto_data = {}
        self.global_data = {}
        self.cg_header = {
            "x_cg_demo_api_key": os.environ["CG_API_KEY"],
        }

    def update_price_data(self):

        cg_params = {
            "ids": "bitcoin,ethereum,solana,dogecoin",
            "vs_currencies": "usd",
            "include_market_cap": "true",
            "include_24hr_change": "true",
            "include_24h_vol": "true",
            "include_last_updated_at": "true",
        }

        crypto_response = requests.get(url=f"{self.cg_endpoint}/simple/price", params=cg_params, headers=self.cg_header)
        crypto_response.raise_for_status()
        self.crypto_data = crypto_response.json()

        global_response = requests.get(f"{self.cg_endpoint}/global", headers=self.cg_header)
        global_response.raise_for_status()
        self.global_data = global_response.json()

    def format_data(self, asset):
        asset_dict = {"price": '${:,.2f}'.format(self.crypto_data[asset]["usd"]),
                      "mcap": '${:,.2f}'.format(self.crypto_data[asset]["usd_market_cap"]),
                      "24h_perc": f"{round(self.crypto_data[asset]["usd_24h_change"], 2)}"}
        return asset_dict
