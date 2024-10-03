import os
import requests
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()


class StockManager:
    """Requests, manages, and formats data received from the TwelveData API"""
    def __init__(self):
        self.td_endpoint = "https://api.twelvedata.com/quote"
        self.index_list = ["SPX", "NDX", "DJI"]
        self.index_data = {}

    def get_index_data(self):
        """Gets stock index data from TwelveData API and formats into a nested dictionary.
        Also adds commas/punctuation and rounds to two decimal places."""
        for index in self.index_list:
            response = requests.get(
                url=self.td_endpoint,
                params={
                    "apikey": os.environ.get("TD_API_KEY"),
                    "symbol": index,
                    "interval": "1day"
                }
            )
            response.raise_for_status()
            data = response.json()
            print(f"Getting data for {index}...")

            ticker = data["symbol"]
            price_float = float(data["close"])
            price = '${:,.2f}'.format(price_float)
            change_usd_24h = '{:,.2f}'.format(float(data["change"]))
            change_percent_24h = f"{round(float(data['percent_change']), 2)}"

            day_of_month = datetime.now().strftime("%d")
            day_of_week = datetime.now().strftime("%w")
            if day_of_month == "24":
                interval = "1month"
            elif day_of_week == "0":
                interval = "1week"
            else:
                interval = "1day"  # API default
            response = requests.get(
                url=self.td_endpoint,
                params={
                    "apikey": os.environ.get("TD_API_KEY"),
                    "symbol": index,
                    "interval": interval
                }
            )
            response.raise_for_status()
            wm_data = response.json()

            change_usd_wm = '{:,.2f}'.format(float(wm_data["change"]))
            change_percent_wm = f"{round(float(wm_data['percent_change']), 2)}"
            # If code is run 00:00UTC Monday, want last weekly open instead of last Monday's close
            if interval == "1week":
                prev_weekly_close = wm_data["open"]
                change_usd_wm_float = price_float - float(prev_weekly_close)
                change_usd_wm = '{:,.2f}'.format(change_usd_wm_float)
                change_percent_wm = f"{round((change_usd_wm_float/price_float)*100, 2)}"

            index_dict = {
                "ticker": ticker,
                "price": price,
                "24h_change_usd": change_usd_24h,
                "24h_change_percent": change_percent_24h,
                "wm_change_usd": change_usd_wm,
                "wm_change_percent": change_percent_wm,
            }
            self.index_data[ticker] = index_dict
            print(f"Updated {index} data.")
