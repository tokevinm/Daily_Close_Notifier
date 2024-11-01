import httpx
from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class CryptoDict(BaseModel):
    ticker: str
    ticker_upper: str
    price: float | int
    mcap: float | int
    total_volume: float | int
    change_usd_24h: float | int
    change_percent_24h: float | int
    change_percent_7d: float | int
    change_percent_30d: float | int

    @field_validator("price")
    def format_price(cls, price: float | int) -> str:
        if price >= 1:
            return f"${price:,.2f}"
        elif price >= 0.01:
            return f"${price:,.4f}"
        else:
            return f"${price:,.8f}"

    @field_validator("mcap", "total_volume", "change_usd_24h")
    def format_to_dollars(cls, price: float | int) -> str:
        return f"${price:,.2f}"

    @field_validator("change_percent_24h", "change_percent_7d", "change_percent_30d")
    def format_percentages(cls, percent: float | int) -> str:
        return f"{round(percent, 2)}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='allow')


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

    async def get_crypto_data(self, asset):
        """Gets user requested data from CoinGecko API and formats into a nested dictionary.
        Also adds commas/punctuation and rounds to two decimal places."""

        # Create empty dictionary entry to ensure emails are the same order/format for every notification
        self.crypto_data[asset] = None
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

        self.crypto_data[asset] = CryptoDict(
            ticker=data["symbol"],
            ticker_upper=data["symbol"].upper(),
            price=data["market_data"]["current_price"]["usd"],
            mcap=data["market_data"]["market_cap"]["usd"],
            total_volume=data["market_data"]["total_volume"]["usd"],
            change_usd_24h=data["market_data"]["price_change_24h_in_currency"]["usd"],
            change_percent_24h=data['market_data']['price_change_percentage_24h'],
            change_percent_7d=data['market_data']['price_change_percentage_7d'],
            change_percent_30d=data['market_data']['price_change_percentage_30d']
        )
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
        self.global_crypto_data = global_response.json()
        if self.global_crypto_data["data"]["market_cap_percentage"]:
            self.crypto_total_mcap_top10_percents = self.global_crypto_data["data"]["market_cap_percentage"]
        if self.global_crypto_data["data"]["total_market_cap"]["usd"]:
            self.crypto_total_mcap = f"${self.global_crypto_data['data']['total_market_cap']['usd']:,.2f}"
        print("Updated global crypto market data")
