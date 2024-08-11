from asset_data import DataManager
from email_notifier import EmailNotifier
from datetime import datetime

data_man = DataManager()
data_man.format_asset_data()
data_man.update_global_data()
asset_data = data_man.cg_assets_data

email_man = EmailNotifier()
users_data = email_man.get_emails_data()


def daily_up_down_icon(percent_change):
    """Takes the 24h % change in price and returns an icon to make it easier
    to discern divergences between assets/asset classes"""
    percent = float(percent_change)
    if percent > 0:
        icon = "🔺"
    elif percent < 0:
        icon = "🔻"
    else:
        icon = ""
    return icon


day_of_month = datetime.now().strftime("%d")
day_of_week = datetime.now().strftime("%w")
if day_of_month == "01":
    close_significance = "MONTHLY"
elif day_of_week == "0":
    close_significance = "WEEKLY"
else:
    close_significance = "Daily"

for user in users_data:
    user_email = user["pleaseEnterYourEmailAddress:"]
    user_options = user.get("anyExtraDataYou'dLikeInYourReport?", None)
    btc_up_down = daily_up_down_icon(asset_data["bitcoin"]["24h_change_percent"])
    message_body = (f"Subject:BTC {close_significance} Close: "
                    f"{asset_data["bitcoin"]["price"]} {btc_up_down}{asset_data["bitcoin"]["24h_change_percent"]}%\n\n")
    if user_options is not None:
        user_choices = user_options.split()[::2]
        for choice in user_choices:
            asset_lower = choice.lower()
            asset_up_down = daily_up_down_icon(asset_data[asset_lower]["24h_change_percent"])
            message_add = (f"{asset_data[asset_lower]["ticker_upper"]}: {asset_data[asset_lower]["price"]} "
                           f"{asset_up_down}{asset_data[asset_lower]["24h_change_percent"]}%\n")
            message_body += message_add
        message_body += "\n"
    message_body += (f"BTC Market Cap: \n{asset_data["bitcoin"]["mcap"]}\n"
                     f"Total Cryptocurrency Market Cap: \n{data_man.crypto_total_mcap}")
    email_man.send_emails(user_email, message_body.encode('utf-8'))
