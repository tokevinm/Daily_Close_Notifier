import asyncio
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Mapped, mapped_column, relationship
from sqlalchemy import create_engine, Integer, Numeric, String, ForeignKey, TIMESTAMP, func
from crypto_data import CryptoManager
from email_notifier import EmailNotifier
from stock_data import StockManager
from datetime import datetime
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='allow')


settings = Settings()


class Base(DeclarativeBase):
    pass


class Asset(Base):
    __tablename__ = "assets"
    asset_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    asset_ticker: Mapped[str] = mapped_column(String(10), nullable=False)
    asset_data: Mapped[list["AssetData"]] = relationship(back_populates="asset", cascade="all, delete-orphan")


class AssetData(Base):
    __tablename__ = "asset_data"
    data_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.asset_id", ondelete="CASCADE"))
    asset = relationship("Asset", back_populates="asset_data")
    timestamp_UTC: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    # # Potential usage in the future but price/percentage changes predominantly calculated with candle closes
    # open_price: Mapped[float] = mapped_column(Numeric(18, 8))
    # high_price: Mapped[float] = mapped_column(Numeric(18, 8))
    # low_price: Mapped[float] = mapped_column(Numeric(18, 8))
    close_price: Mapped[float] = mapped_column(Numeric(18, 8))
    market_cap: Mapped[float] = mapped_column(Numeric(24, 2))
    volume_USD: Mapped[float] = mapped_column(Numeric(24, 2))


DATABASE_URL = settings.postgres_url
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

MONTHLY = "MONTHLY"
WEEKLY = "WEEKLY"

crypto_man = CryptoManager()
stock_man = StockManager()
email_man = EmailNotifier()

crypto_data = crypto_man.crypto_data
stock_data = stock_man.index_data


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


def format_coingecko_ids(options_string: str) -> list[str]:
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


def format_percent(percent: float) -> str:
    """Formats a float/integer input as a percentage into a string with punctuation, rounded to two decimal places"""
    return f"{round(percent, 2)}%"


def save_data_to_postgres(name: str, ticker: str, price: float | int, mcap: float | int, volume: int) -> None:
    """Checks for existence of asset in Postgres database, adds it if nonexistent, and updates associated data"""
    asset = session.query(Asset).filter_by(asset_name=name).first()
    new_asset = False
    if not asset:
        asset = Asset(
            asset_name=name,
            asset_ticker=ticker
        )
        new_asset = True

    new_data = AssetData(
        asset=asset,
        close_price=price,
        market_cap=mcap,
        volume_USD=volume
    )
    if new_asset:
        session.add(asset)
    session.add(new_data)
    session.commit()


day_of_month = datetime.now().strftime("%d")
day_of_week = datetime.now().strftime("%w")

# Time is based off UTC on pythonanywhere VM
if day_of_month == "01":
    close_significance = MONTHLY
    interval = "1M"
# Check if day_of_week is Monday ("1"), as global crypto markets candle close at 00:00 UTC Sunday ("0").
elif day_of_week == "1":
    close_significance = WEEKLY
    interval = "7D"
else:
    close_significance = "Daily"  # Default
    interval = "1D"

stock_market_open = True
if day_of_week in ["0", "1"]:  # Sunday/Monday at 00:00 UTC is Sat/Sun in the U.S.
    stock_market_open = False


async def main():
    async with asyncio.TaskGroup() as tg:
        tg.create_task(email_man.get_emails_data())
        tg.create_task(crypto_man.get_global_crypto_data())
        for asset in crypto_man.crypto_list:
            tg.create_task(crypto_man.get_crypto_data(asset))
        if stock_market_open:
            for ind in stock_man.index_list:
                tg.create_task(stock_man.get_index_data(ind))

    for key, data in crypto_data.items():
        save_data_to_postgres(
            name=data.name,
            ticker=data.ticker,
            price=data.price,
            mcap=data.mcap,
            volume=data.volume
        )
    if stock_market_open:
        for key, data in stock_data.items():
            save_data_to_postgres(
                name=data.name,
                ticker=data.ticker,
                price=data.close,
                mcap=data.mcap,
                volume=data.volume
            )

    users_data = email_man.users_data
    async_emails = []
    for user in users_data.data:
        if "unsubscribe?" in user:
            continue
        user_email = user["emailAddress"]
        user_options = user.get("anyExtraDataYou'dLikeInYourReport?", None)
        print(f"Compiling daily report for {user_email}...")

        subject = f"BTC {close_significance} Close: {crypto_data['bitcoin'].price}"

        message_body = "<p>"
        message_body += default_msg(
            ticker=crypto_data["bitcoin"].ticker,
            price=crypto_data["bitcoin"].price,
            percent_change=crypto_data["bitcoin"].change_percent_24h
        )
        if close_significance == MONTHLY or close_significance == WEEKLY:
            if close_significance == MONTHLY:
                btc_wm_percent = crypto_data['bitcoin'].change_percent_30d
            else:
                btc_wm_percent = crypto_data['bitcoin'].change_percent_7d
            btc_wm_up_down = up_down_icon(btc_wm_percent)
            message_body += (f"{close_significance.title()} Change "
                             f"{btc_wm_up_down} {btc_wm_percent}%")
        message_body += "</p>"

        if user_options:
            user_choices = format_coingecko_ids(user_options)[::2]
            message_body += "<p>"
            for choice in user_choices:
                crypto_dict = crypto_data[choice.lower()]
                message_body += default_msg(
                    ticker=crypto_dict.ticker,
                    price=crypto_dict.price,
                    percent_change=crypto_dict.change_percent_24h
                )
                if close_significance == MONTHLY or close_significance == WEEKLY:
                    if close_significance == MONTHLY:
                        crypto_wm_percent = crypto_dict.change_percent_30d
                    else:
                        crypto_wm_percent = crypto_dict.change_percent_7d
                    message_body += htf_msg(
                        timeframe=interval,
                        percent_change=crypto_wm_percent
                    )
            message_body += "</p>"

        if stock_market_open:
            message_body += "<p>"
            for stock in stock_data:
                stock_dict = stock_data[stock]
                message_body += default_msg(
                    ticker=stock_dict.ticker,
                    price=stock_dict.close,
                    percent_change=stock_dict.change_percent_24h
                )
                if close_significance == MONTHLY or close_significance == WEEKLY:
                    if close_significance == MONTHLY:
                        stock_wm_percent = stock_dict.change_percent_monthly
                    else:
                        stock_wm_percent = stock_dict.change_percent_weekly
                    message_body += htf_msg(
                        timeframe=interval,
                        percent_change=stock_wm_percent
                    )
            message_body += "</p>"

        message_body += (f"<p>BTC Market Cap:<br>"
                         f"{format_dollars(crypto_data['bitcoin'].mcap)}<br>"
                         f"Total Cryptocurrency Market Cap:<br>"
                         f"{format_dollars(crypto_man.crypto_total_mcap)}</p>")

        html = f"""
        <html>
          <body>
            {message_body}
            <br>
            <hr>
            <p>Click <a href="https://forms.gle/5UMWTWM8HMuHKexW9">here</a> to update your preferences or unsubscribe.</p>
            <p>© 2024 Kevin To</p>
          </body>
        </html>
        """

        async_emails.append(
            asyncio.create_task(email_man.send_emails(user_email=user_email, subject=subject, html_text=html))
        )
    await asyncio.gather(*async_emails)


if __name__ == "__main__":
    asyncio.run(main())
