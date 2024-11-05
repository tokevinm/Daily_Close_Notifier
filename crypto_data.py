import httpx
from pydantic import BaseModel, field_validator, model_validator
from config import Settings

settings = Settings()


class CryptoDict(BaseModel):
    name: str
    ticker: str
    price: float | int
    mcap: int
    volume: int
    # With enough data in db, will be able to delete following variables and replace w/ functions to calculate
    change_usd_24h: float
    change_percent_24h: float
    change_percent_7d: float
    change_percent_30d: float

    @classmethod
    @model_validator(mode="before")
    def validate_data(cls, values):
        for field in ["price", "mcap", "volume", "change_usd_24h",
                      "change_percent_24h", "change_percent_7d", "change_percent_30d"]:
            if values.get(field) is None:
                raise KeyError(f"{field} is missing from the API response.")
        for field in ["price", "mcap", "volume"]:
            if values[field] < 0:
                raise ValueError(f"{field} cannot be negative.")
        return values


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

        # # Create empty dictionary entry to ensure emails are the same order/format for every notification
        # self.crypto_data[asset] = None

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
            self.crypto_data[asset] = CryptoDict(
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
