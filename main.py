import asyncio
from datetime import datetime
from fastapi import FastAPI
from utils import up_down_icon, default_msg, htf_msg, format_coingecko_ids, format_dollars, save_data_to_postgres
from config import Settings
from models import Session, Asset, AssetData
from crypto_data import CryptoManager
from email_notifier import EmailNotifier
from stock_data import StockManager

MONTHLY = "MONTHLY"
WEEKLY = "WEEKLY"

settings = Settings()
session = Session()
app = FastAPI()

crypto_man, stock_man, email_man = CryptoManager(), StockManager(), EmailNotifier()

crypto_data = crypto_man.crypto_data
stock_data = stock_man.index_data

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
