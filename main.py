import asyncio
from crypto_data import CryptoManager
from email_notifier import EmailNotifier
from stock_data import StockManager
from datetime import datetime

MONTHLY = "MONTHLY"
WEEKLY = "WEEKLY"

crypto_man = CryptoManager()
crypto_data = crypto_man.crypto_data

stock_man = StockManager()
stock_data = stock_man.index_data

email_man = EmailNotifier()


def up_down_icon(percent_change: str) -> str:
    """Takes the % change in price and returns an icon to make it easier
    to discern divergences between assets/asset classes"""
    percent = float(percent_change)
    if percent > 0:
        icon = "🟢"
    elif percent < 0:
        icon = "🔴"
    else:
        icon = ""
    return icon


def default_msg(ticker: str, price: str, percent_change: str) -> str:
    """Default data/email formatting for each user selected ticker"""
    asset_up_down = up_down_icon(percent_change)
    message_add = f"{ticker}: {price} {asset_up_down} {percent_change}%<br>"
    return message_add


def htf_msg(timeframe: str, percent_change: str) -> str:
    """Formats weekly/monthly close data for each user selected ticker"""
    htf_asset_up_down = up_down_icon(percent_change)
    message_add = f"    {timeframe} {htf_asset_up_down} {percent_change}%<br>"
    return message_add


def format_ids(options_string: str) -> list[str]:
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


day_of_month = datetime.now().strftime("%d")
day_of_week = datetime.now().strftime("%w")

# Time is based off UTC on pythonanywhere VM
if day_of_month == "01":
    close_significance = MONTHLY
    interval = "30D"
# Check if day_of_week is Monday ("1"), as global crypto markets candle close at 00:00 UTC Sunday ("0").
elif day_of_week == "1":
    close_significance = WEEKLY
    interval = "7D"
else:
    close_significance = "Daily"  # Default
    interval = "1D"

stock_market_open = True
if day_of_week in ["0", "6"]:
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
                await asyncio.sleep(0.1)  # Rate limiting

    users_data = email_man.users_data
    async_emails = []
    for user in users_data:
        if "unsubscribe?" in user:
            continue
        user_email = user["emailAddress"]
        user_options = user.get("anyExtraDataYou'dLikeInYourReport?", None)
        print(f"Compiling daily report for {user_email}...")

        subject = f"BTC {close_significance} Close: {crypto_data['bitcoin'].price}"

        message_body = "<p>"
        message_body += default_msg(
            ticker=crypto_data["bitcoin"].ticker_upper,
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
            user_choices = format_ids(user_options)[::2]
            message_body += "<p>Crypto:<br>"
            for choice in user_choices:
                crypto_dict = crypto_data[choice.lower()]
                message_body += default_msg(
                    ticker=crypto_dict.ticker_upper,
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
            message_body += "<p>Stocks:<br>"
            for stock in stock_data:
                stock_dict = stock_data[stock]
                message_body += default_msg(
                    ticker=stock_dict.ticker,
                    price=stock_dict.close_value,
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
                         f"{crypto_data['bitcoin'].mcap}<br>"
                         f"Total Cryptocurrency Market Cap:<br>"
                         f"{crypto_man.crypto_total_mcap}</p>")

        html = f"""
        <html>
          <body>
            {message_body}
            <br>
            <hr>
            <p>Click <a href="https://forms.gle/5UMWTWM8HMuHKexW9">here</a> to update your preferences or unsubscribe.</p>
            <p>© 2024 Kevin T.</p>
          </body>
        </html>
        """

        async_emails.append(asyncio.create_task(email_man.send_emails(user_email, subject=subject, html_text=html)))
    await asyncio.gather(*async_emails)


if __name__ == "__main__":
    asyncio.run(main())
