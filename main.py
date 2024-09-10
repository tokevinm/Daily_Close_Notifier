from crypto_data import CryptoManager
from email_notifier import EmailNotifier
from stock_data import StockManager
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

MONTHLY = "MONTHLY"
WEEKLY = "WEEKLY"

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


def default_msg(ticker, price, percent_change):
    """Default data formatting for each user selected ticker"""
    asset_up_down = up_down_icon(percent_change)
    message_add = f"{ticker}: {price} {asset_up_down} {percent_change}%<br>"
    return message_add


def htf_msg(timeframe, percent_change):
    """Formats weekly/monthly close data for each user selected ticker"""
    htf_asset_up_down = up_down_icon(percent_change)
    message_add = f"    {timeframe} {htf_asset_up_down} {percent_change}%<br>"
    return message_add


def format_ids(options_string):
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

if day_of_month == "01":
    close_significance = MONTHLY
    interval = "30D"
    interval_percent = "30d_change_percent"
elif day_of_week == "1":
    close_significance = WEEKLY
    interval = "7D"
    interval_percent = "7d_change_percent"
else:
    close_significance = "Daily"  # Default
    interval = "1D"
    interval_percent = "24h_change_percent"

for user in users_data:
    if "unsubscribe?" in user:
        continue
    user_email = user["emailAddress"]
    user_options = user.get("anyExtraDataYou'dLikeInYourReport?", None)
    print(f"Compiling daily report for {user_email}...")

    msg = MIMEMultipart()
    msg["From"] = email_man.smtp_username
    msg["To"] = user_email
    msg['Subject'] = f"BTC {close_significance} Close: {crypto_data['bitcoin']['price']}"

    message_body = "<p>"
    message_body += default_msg(
        ticker=crypto_data["bitcoin"]["ticker_upper"],
        price=crypto_data["bitcoin"]["price"],
        percent_change=crypto_data["bitcoin"]["24h_change_percent"]
    )
    if close_significance == MONTHLY or close_significance == WEEKLY:
        btc_wm_up_down = up_down_icon(crypto_data["bitcoin"][interval_percent])
        message_body += (f"{close_significance.title()} Change ({interval}) "
                         f"{btc_wm_up_down} {crypto_data['bitcoin'][interval_percent]}%")
    message_body += "</p><p>"

    if user_options:
        user_choices = format_ids(user_options)[::2]
        message_body += "Crypto:<br>"
        for choice in user_choices:
            crypto_dict = crypto_data[choice.lower()]
            message_body += default_msg(
                ticker=crypto_dict["ticker_upper"],
                price=crypto_dict["price"],
                percent_change=crypto_dict["24h_change_percent"]
            )
            if close_significance == MONTHLY or close_significance == WEEKLY:
                message_body += htf_msg(
                    timeframe=interval,
                    percent_change=crypto_dict[interval_percent]
                )
        message_body += "</p><p>"

    message_body += "Stocks:<br>"
    for stock in stock_data:
        stock_dict = stock_data[stock]
        message_body += default_msg(
            ticker=stock_dict["ticker"],
            price=stock_dict["price"],
            percent_change=stock_dict["24h_change_percent"]
        )
        if close_significance == MONTHLY or close_significance == WEEKLY:
            message_body += htf_msg(
                timeframe=interval,
                percent_change=stock_dict["wm_change_percent"]
            )

    message_body += (f"<p>BTC Market Cap:<br>"
                     f"{crypto_data['bitcoin']['mcap']}<br>"
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
    msg.attach(MIMEText(html, 'html'))
    message = msg.as_string()

    email_man.send_emails(user_email, message.encode('utf-8'))
