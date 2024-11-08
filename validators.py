from pydantic import BaseModel, field_validator, model_validator, EmailStr


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


class StockDict(BaseModel):
    name: str
    ticker: str
    close: float
    mcap: float | None  # Indices return "None" though Trading View
    volume: int
    # With enough data in db, will be able to delete following variables and replace w/ functions to calculate
    change_value_24h: float
    change_percent_24h: float
    change_value_weekly: float
    change_percent_weekly: float
    change_value_monthly: float
    change_percent_monthly: float

    @classmethod
    @model_validator(mode="before")
    def validate_data(cls, values):
        for field in ["close", "change_value_24h", "change_percent_24h", "change_value_weekly",
                      "change_percent_weekly", "change_value_monthly", "change_percent_monthly"]:
            if values.get(field) is None:
                raise KeyError(f"'{field}' is missing from the API response.")
        if values["close"] < 0:
            raise ValueError(f"{values['ticker']} candle close value cannot be negative.")
        return values


class GoogleDriveData(BaseModel):
    data: list[dict]


class UserSignup(BaseModel):
    email: EmailStr