import httpx
import asyncio
from datetime import datetime
from sqlalchemy import select

from models import Asset, AssetData
from validators import CryptoData
from utils import save_data_to_postgres
from config import Settings, async_session

settings = Settings()


class CryptoManager:
    """Requests, manages, and formats data received from the CoinGecko API"""

    def __init__(self):
        self.crypto_list = [
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
        self.crypto_data = {}
        self.global_crypto_data = {}
        # TODO: Consider making use of crypto_total_mcap_top10_percents
        self.crypto_total_mcap_top10_percents = None
        # crypto_total_mcap_top10_percents is a dictionary of top-10 cryptos and their percentages of total mcap
        self.crypto_total_mcap = None
        self._cg_endpoint = settings.coingecko_endpoint
        self._cg_header = {
            "x-cg-demo-api-key": settings.coingecko_api_key,
        }

    async def get_crypto_data(self, asset: str) -> None:
        """Gets user requested data from CoinGecko API and formats into a nested dictionary.
        Also adds commas/punctuation and rounds to two decimal places."""

        try:
            print(f"Getting data for {asset.title()}...")
            async with httpx.AsyncClient() as client:
                asset_response = await client.get(
                    url=f"{self._cg_endpoint}/coins/{asset}",
                    headers=self._cg_header,
                    params={"id": asset}
                )
            asset_response.raise_for_status()
            data = asset_response.json()
            # Most data is returned as int/float (depending on how high or low price is), except ticker/"symbol"
        except Exception as e:
            print(f"Failed to get data for {asset.title()}", e)
        else:
            self.crypto_data[asset] = CryptoData(
                name=data["name"],
                ticker=data["symbol"].upper(),
                price=data["market_data"]["current_price"]["usd"],
                mcap=data["market_data"]["market_cap"]["usd"],
                volume=data["market_data"]["total_volume"]["usd"],
                change_usd_24h=data["market_data"]["price_change_24h_in_currency"]["usd"],
                change_percent_24h=data['market_data']['price_change_percentage_24h'],
                change_percent_7d=data['market_data']['price_change_percentage_7d'],
                change_percent_30d=data['market_data']['price_change_percentage_30d']
            )
            print(f"Updated {asset.title()} data")

    async def get_global_crypto_data(self) -> None:
        """Coingecko API request to get data related to entire crypto market"""

        try:
            print("Getting global crypto market data...")
            async with httpx.AsyncClient() as client:
                global_response = await client.get(
                    url=f"{self._cg_endpoint}/global",
                    headers=self._cg_header
                )
            global_response.raise_for_status()
            self.global_crypto_data = global_response.json()
        except Exception as e:
            print(f"Failed to get global crypto data", e)
        else:
            if self.global_crypto_data["data"]["market_cap_percentage"]:
                self.crypto_total_mcap_top10_percents = self.global_crypto_data["data"]["market_cap_percentage"]
            if self.global_crypto_data["data"]["total_market_cap"]["usd"]:
                self.crypto_total_mcap = self.global_crypto_data['data']['total_market_cap']['usd']
            print("Retrieved global crypto market data")

    async def cg_history_to_postgres(
            self,
            coingecko_id: str,
            num_days: str = "365",
            interval: str = "daily",
            precision: str = "2"
    ):
        """Gets historical daily closing data from Coingecko API and saves to Postgres database.
        num_days (default= "365") is the number of days to go back for historical data.
        interval (default = "daily") can also be "hourly", "5-minutely", etc.
        precision (default = "2") is the desired # of decimal places in the returned values."""

        print(f"Getting historical crypto market data for {coingecko_id}...")
        try:
            async with httpx.AsyncClient() as client:
                historical_response, asset_response = await asyncio.gather(
                    client.get(
                        url=f"{self._cg_endpoint}/coins/{coingecko_id}/market_chart",
                        headers=self._cg_header,
                        params={
                            "vs_currency": "usd",
                            "days": num_days,
                            "interval": interval,  # Can also do "hourly", "5-minutely"
                            "precision": precision  # Decimal places for price value
                        }
                    ),
                    client.get(
                        url=f"{self._cg_endpoint}/coins/{coingecko_id}",
                        headers=self._cg_header,
                        params={"id": coingecko_id}
                    ))

            historical_response.raise_for_status()
            historical_data = historical_response.json()
            asset_response.raise_for_status()
            asset_data = asset_response.json()

        except Exception as e:
            print(f"Failed to get historical {coingecko_id} data", e)

        else:
            print("Data successfully retrieved")
            all_data = zip(
                historical_data["prices"],
                historical_data["market_caps"],
                historical_data["total_volumes"]
            )
            async with async_session() as session:
                asset_result = await session.execute(
                    select(AssetData.date)
                    .join(Asset)
                    .filter(Asset.asset_name == asset_data["name"])
                )
                asset_dates = asset_result.scalars().all()
                if not asset_dates:
                    new_asset = Asset(
                        asset_name=asset_data["name"],
                        asset_ticker=asset_data["symbol"].upper()
                    )
                    session.add(new_asset)
                    await session.commit()

                asset_dates_set = {row for row in asset_dates}

                for price, mcap, vol in all_data:

                    # Coingecko data formatted as a list of lists where [0] for every entry is the unix time of candle close.
                    unix_seconds = price[0] / 1000
                    close_date_time = datetime.fromtimestamp(unix_seconds)
                    close_date = close_date_time.date()
                    asset_name = asset_data["name"]
                    asset_ticker = asset_data["symbol"].upper()
                    asset_price = price[1]
                    asset_mcap = mcap[1]
                    asset_vol = vol[1]

                    # Check if close data already exists for the iterated day and if so, skip saving it to Postgres
                    if close_date in asset_dates_set:
                        continue

                    await save_data_to_postgres(
                        name=asset_name,
                        ticker=asset_ticker,
                        price=asset_price,
                        mcap=asset_mcap,
                        volume=asset_vol,
                        date=close_date
                    )

                print(f"Saved {coingecko_id} market data to Postgres db, going back {num_days} days")
