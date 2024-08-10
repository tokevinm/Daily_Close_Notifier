from asset_data import DataManager
from email_notifier import EmailNotifier
from datetime import datetime

data_man = DataManager()
data_man.format_asset_data()
data_man.update_global_data()
asset_data = data_man.cg_assets_data

email_man = EmailNotifier()
users_data = email_man.get_emails_data()


def daily_icon(percent_change):
    """Takes the 24h % change in price and returns an icon to make it easier
    to discern divergences between assets/asset classes"""
    if float(percent_change) > 0:
        icon = "🔺"
    elif float(percent_change) < 0:
        icon = "🔻"
    else:
        icon = ""
    return icon


btc_icon = daily_icon(asset_data["bitcoin"]["24h_change_percent"])
eth_icon = daily_icon(asset_data["ethereum"]["24h_change_percent"])
sol_icon = daily_icon(asset_data["solana"]["24h_change_percent"])
doge_icon = daily_icon(asset_data["dogecoin"]["24h_change_percent"])

day_of_month = datetime.now().strftime("%d")
day_of_week = datetime.now().strftime("%w")
if day_of_month == "01":
    close_significance = "MONTHLY"
    # ADD Comment testing
elif day_of_week == "0":
    close_significance = "WEEKLY"
else:
    close_significance = "Daily"

for user in users_data:
    user_email = user["pleaseEnterYourEmailAddress:"]
    user_option = user.get("anyExtraDataYou'dLikeInYourReport?", None)
    message_body = (f"Subject:BTC {close_significance} Close: "
                    f"{asset_data["bitcoin"]["price"]} {btc_icon}{asset_data["bitcoin"]["24h_change_percent"]}%\n\n")
    if user_option is not None:
        user_choices = user_option.split()
        if "Ethereum" in user_choices:
            message_add = (f"ETH: {asset_data["ethereum"]["price"]} "
                           f"{eth_icon}{asset_data["ethereum"]["24h_change_percent"]}%\n")
            message_body += message_add
        if "Solana" in user_choices:
            message_add = (f"SOL: {asset_data["solana"]["price"]} "
                           f"{sol_icon}{asset_data["solana"]["24h_change_percent"]}%\n")
            message_body += message_add
        if "Dogecoin" in user_choices:
            message_add = (f"DOGE: {asset_data["dogecoin"]["price"]} "
                           f"{doge_icon}{asset_data["dogecoin"]["24h_change_percent"]}%\n")
            message_body += message_add
    message_body += (f"\nBTC Market Cap: \n{asset_data["bitcoin"]["mcap"]}\n"
                     f"Total Cryptocurrency Market Cap: \n{data_man.crypto_total_mcap}")
    email_man.send_emails(user_email, message_body.encode('utf-8'))
