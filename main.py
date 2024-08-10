from asset_data import DataManager
from email_notifier import EmailNotifier
from datetime import datetime

data_manager = DataManager()
data_manager.update_asset_data()
data_manager.update_global_data()
email_manager = EmailNotifier()
users_data = email_manager.get_emails_data()

total_crypto_mcap = '${:,.2f}'.format(data_manager.cg_global_data["data"]["total_market_cap"]["usd"])

btc_data = data_manager.format_data("bitcoin", "btc")
eth_data = data_manager.format_data("ethereum", "eth")
sol_data = data_manager.format_data("solana", "sol")
doge_data = data_manager.format_data("dogecoin", "doge")

btc_icon = data_manager.daily_icon(btc_data["24h_change_percent"])
eth_icon = data_manager.daily_icon(eth_data["24h_change_percent"])
sol_icon = data_manager.daily_icon(sol_data["24h_change_percent"])
doge_icon = data_manager.daily_icon(doge_data["24h_change_percent"])

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
    user_option = user.get("anyExtraDataYou'dLikeInYourReport?", None)
    email_message = (f"Subject:BTC {close_significance} Close: "
                     f"{btc_data["price"]} {btc_icon}{btc_data["24h_change_percent"]}%\n\n")
    if user_option is not None:
        user_choices = user_option.split()
        if "Ethereum" in user_choices:
            message_add = f"ETH: {eth_data["price"]} {eth_icon}{eth_data["24h_change_percent"]}%\n"
            email_message += message_add
        if "Solana" in user_choices:
            message_add = f"SOL: {sol_data["price"]} {sol_icon}{sol_data["24h_change_percent"]}%\n"
            email_message += message_add
        if "Dogecoin" in user_choices:
            message_add = f"DOGE: {doge_data["price"]} {doge_icon}{doge_data["24h_change_percent"]}%\n"
            email_message += message_add
    email_message += f"\nBTC Market Cap: \n{btc_data["mcap"]}\nTotal Cryptocurrency Market Cap: \n{total_crypto_mcap}"
    email_manager.send_emails(user_email, email_message.encode('utf-8'))
