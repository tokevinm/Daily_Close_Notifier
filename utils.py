from sqlalchemy import select, date
from models import Asset, AssetData
from config import Session


def up_down_icon(percent_change: float) -> str:
    """Takes the % change in price and returns an icon to make it easier
    to discern divergences between assets/asset classes"""
    if percent_change > 0:
        icon = "🟢"
    elif percent_change < 0:
        icon = "🔴"
    else:
        icon = ""
    return icon


def default_msg(ticker: str, price: float | int, percent_change: float) -> str:
    """Default data/email formatting for each user selected ticker"""
    asset_up_down = up_down_icon(percent_change)
    message_add = f"{ticker}: {format_dollars(price)} {asset_up_down} {format_percent(percent_change)}<br>"
    return message_add


def htf_msg(timeframe: str, percent_change: float) -> str:
    """Formats weekly/monthly close data for each user selected ticker"""
    htf_asset_up_down = up_down_icon(percent_change)
    message_add = f"&nbsp;&nbsp;{timeframe} {htf_asset_up_down} {format_percent(percent_change)}<br>"
    return message_add


def format_coingecko_ids(options_string: str | None) -> list[str]:
    """Receives a JSON formatted string of user chosen cryptocurrencies
    and formats into a list that is compatible with the Coingecko API asset IDs"""
    options = options_string.split()
    if "Toncoin" in options:
        index = options.index("Toncoin")
        options[index] = "the-open-network"
    if "Avalanche" in options:
        index = options.index("Avalanche")
        options[index] = "avalanche-2"
    if "Near" in options:
        options.remove("Protocol")
    if "DogWifHat" in options:
        index = options.index("DogWifHat")
        options[index] = "dogwifcoin"
    if "Polygon" in options:
        index = options.index("Polygon")
        options[index] = "polygon-ecosystem-token"
    if "Ondo" in options:
        index = options.index("Ondo")
        options[index] = "ondo-finance"
    if "Mother" in options:
        index = options.index("Mother")
        options.remove("Iggy")
        options[index] = "mother-iggy"
    return options


def format_dollars(price: float | int) -> str:
    """Formats a float/integer input into a dollar amount with punctuation"""
    if price < 0:
        return f"-${price:,.2f}"
    elif price >= 1:
        return f"${price:,.2f}"
    elif price >= 0.01:
        return f"${price:,.4f}"
    else:
        return f"${price:,.8f}"


def format_percent(percent: float | int) -> str:
    """Formats a float/integer input as a percentage into a string with punctuation, rounded to two decimal places"""
    return f"{round(percent, 2)}%"


async def save_data_to_postgres(
        name: str, 
        ticker: str, 
        price: float | int, 
        mcap: float | int, 
        volume: int, 
        date: date = None
        ) -> None:
    """Checks for existence of asset in Postgres database, adds it if nonexistent, and updates associated data"""

    async with Session() as session:
        asset_result = await session.execute(select(Asset).filter_by(asset_name=name))
        asset = asset_result.scalars().first()
        if not asset:
            asset = Asset(
                asset_name=name,
                asset_ticker=ticker
            )
            session.add(asset)
            await session.commit()

        new_data = AssetData(
            asset=asset,
            date=date,
            close_price=price,
            market_cap=mcap,
            volume_USD=volume
        )
        session.add(new_data)
        await session.commit()
