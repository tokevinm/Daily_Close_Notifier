import os
import httpx
from dotenv import load_dotenv

load_dotenv()


class StockManager:
    """Requests, manages, and formats data received from the RapidAPI "Trading View" API"""

    def __init__(self):
        self._rapidapi_TV_endpoint = "https://trading-view.p.rapidapi.com/stocks/get-financials"
        self.index_list = ["SP:SPX", "NASDAQ:NDX", "DJ:DJI"]
        self.index_data = {
            "SPX": None,
            "NDX": None,
            "DJI": None
        }
        self._rapidapi_headers = {
            "x-rapidapi-key": os.environ["RAPIDAPI_KEY"],
            "x-rapidapi-host": "trading-view.p.rapidapi.com"
        }

    async def get_index_data(self, stock_index):
        """Gets stock index data from "Trading View" on RapidAPI and formats into a nested dictionary.
        Also adds commas/punctuation and rounds to two decimal places."""

        print(f"Getting data for {stock_index}...")
        async with httpx.AsyncClient() as client:
            query = {
                "columns": "name,close,change_abs,change,change_abs|1W,change|1W,change_abs|1M,change|1M",
                "symbol": stock_index
            }
            response = await client.get(
                url=self._rapidapi_TV_endpoint,
                params=query,
                headers=self._rapidapi_headers
            )
        response.raise_for_status()
        data = response.json()

        ticker = data["data"][0]["d"][0]
        close_value_float = float(data["data"][0]["d"][1])
        close_value = '{:,.2f}'.format(close_value_float)
        change_value_24h = '{:,.2f}'.format(float(data["data"][0]["d"][2]))
        change_percent_24h = f"{round(data["data"][0]["d"][3], 2)}"
        change_value_weekly = '{:,.2f}'.format(float(data["data"][0]["d"][4]))
        change_percent_weekly = f"{round(data["data"][0]["d"][5], 2)}"
        change_value_monthly = '{:,.2f}'.format(float(data["data"][0]["d"][6]))
        change_percent_monthly = f"{round(data["data"][0]["d"][7], 2)}"

        index_dict = {
            "ticker": ticker,
            "value": close_value,
            "24h_change_value": change_value_24h,
            "24h_change_percent": change_percent_24h,
            "weekly_change_value": change_value_weekly,
            "weekly_change_percent": change_percent_weekly,
            "monthly_change_value": change_value_monthly,
            "monthly_change_percent": change_percent_monthly
        }

        self.index_data[ticker] = index_dict
        print(f"Updated {stock_index} data")
