from crypto_data import CryptoManager
from email_notifier import EmailNotifier
from stock_data import StockManager
from datetime import datetime

crypto_man = CryptoManager()
crypto_man.get_crypto_data()
crypto_man.get_global_crypto_data()
crypto_data = crypto_man.cg_crypto_data

stock_man = StockManager()
stock_man.get_index_data()
stock_data = stock_man.index_data

email_man = EmailNotifier()
users_data = email_man.get_emails_data()


def up_down_icon(percent_change):
    """Takes the 24h % change in price and returns an icon to make it easier
    to discern divergences between assets/asset classes"""
    percent = float(percent_change)
    if percent > 0:
        icon = "🟢"
    elif percent < 0:
        icon = "🔴"
    else:
        icon = ""
    return icon


def default_msg(ticker, price, percent_change):
    asset_up_down = up_down_icon(percent_change)
    message_add = f"{ticker}: {price} {asset_up_down} {percent_change}%\n"
    return message_add


def htf_msg(timeframe, percent_change):
    htf_asset_up_down = up_down_icon(percent_change)
    message_add = f"    {timeframe} {htf_asset_up_down} {percent_change}%\n"
    return message_add


day_of_month = datetime.now().strftime("%d")
day_of_week = datetime.now().strftime("%w")
if day_of_month == "01":
    close_significance = "MONTHLY"
    interval = "30D"
    interval_percent = "30d_change_percent"
elif day_of_week == "0":
    close_significance = "WEEKLY"
    interval = "7D"
    interval_percent = "7d_change_percent"
else:
    close_significance = "Daily"
    interval = "1D"
    interval_percent = ""

for user in users_data:
    user_email = user["pleaseEnterYourEmailAddress:"]
    user_options = user.get("anyExtraDataYou'dLikeInYourReport?", None)
    print(f"Compiling daily report for {user_email}...")

    message_body = f"Subject:BTC {close_significance} Close: {crypto_data["bitcoin"]["price"]}\n\n"
    message_body += default_msg(
        ticker=crypto_data["bitcoin"]["ticker_upper"],
        price=crypto_data["bitcoin"]["price"],
        percent_change=crypto_data["bitcoin"]["24h_change_percent"]
    )
    if close_significance == "MONTHLY" or close_significance == "WEEKLY":
        btc_wm_up_down = up_down_icon(crypto_data["bitcoin"][interval_percent])
        message_body += (f"{close_significance.title()} Change ({interval}) "
                         f"{btc_wm_up_down} {crypto_data["bitcoin"][interval_percent]}%\n\n")

    if user_options:
        user_choices = user_options.split()[::2]
        message_body += "Crypto:\n"
        for choice in user_choices:
            crypto_dict = crypto_data[choice.lower()]
            message_body += default_msg(
                ticker=crypto_dict["ticker_upper"],
                price=crypto_dict["price"],
                percent_change=crypto_dict["24h_change_percent"]
            )
            if close_significance == "MONTHLY" or close_significance == "WEEKLY":
                message_body += htf_msg(
                    timeframe=interval,
                    percent_change=crypto_dict[interval_percent]
                )
        message_body += "\n"

    message_body += "Stocks:\n"
    for index in stock_data:
        stock_dict = stock_data[index]
        message_body += default_msg(
            ticker=stock_dict["ticker"],
            price=stock_dict["price"],
            percent_change=stock_dict["24h_change_percent"]
        )
        if close_significance == "MONTHLY" or close_significance == "WEEKLY":
            message_body += htf_msg(
                timeframe=interval,
                percent_change=stock_dict["wm_change_percent"]
            )

    message_body += (f"\nBTC Market Cap: \n{crypto_data["bitcoin"]["mcap"]}\n"
                     f"Total Cryptocurrency Market Cap: \n{crypto_man.crypto_total_mcap}")
    email_man.send_emails(user_email, message_body.encode('utf-8'))
