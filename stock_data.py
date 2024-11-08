import httpx
from validators import StockData
from config import Settings
settings = Settings()


class StockManager:
    """Requests, manages, and formats data received from the RapidAPI "Trading View" API"""

    def __init__(self):
        self.index_list = [
            "SP:SPX",
            "NASDAQ:NDX",
            "DJ:DJI",
        ]
        self.index_data = {
            "SPX": None,
            "NDX": None,
            "DJI": None,
        }
        self._rapidAPI_TV_endpoint = settings.rapidapi_endpoint
        self._rapidAPI_headers = {
            "x-rapidapi-key": settings.rapidapi_key,
            "x-rapidapi-host": "trading-view.p.rapidapi.com"
        }

    async def get_index_data(self, stock_index: str) -> None:
        """Gets stock index data from "Trading View" on RapidAPI and formats into a nested dictionary.
        Also adds commas/punctuation and rounds to two decimal places."""

        try:
            print(f"Getting data for {stock_index}...")
            async with httpx.AsyncClient() as client:
                query = {
                    "columns": "name,close,market_cap_basic,volume,"
                               "change_abs,change,change_abs|1W,change|1W,change_abs|1M,change|1M,",
                    "symbol": stock_index
                }
                response = await client.get(
                    url=self._rapidAPI_TV_endpoint,
                    params=query,
                    headers=self._rapidAPI_headers
                )
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print(f"Failed to get data for {stock_index}", e)
        else:
            ticker = data['data'][0]['d'][0]

            self.index_data[ticker] = StockData(
                name=ticker,
                ticker=ticker,
                close=data['data'][0]['d'][1],
                mcap=data['data'][0]['d'][2],
                volume=data['data'][0]['d'][3],
                change_value_24h=data['data'][0]['d'][4],
                change_percent_24h=data['data'][0]['d'][5],
                change_value_weekly=data['data'][0]['d'][6],
                change_percent_weekly=data['data'][0]['d'][7],
                change_value_monthly=data['data'][0]['d'][8],
                change_percent_monthly=data['data'][0]['d'][9],
            )
            print(f"Updated {stock_index} data")
