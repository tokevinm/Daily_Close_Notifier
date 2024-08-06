import requests
import asset_data
import email_notifier

data_manager = asset_data.DataManager()
data_manager.update_price_data()
crypto_data = data_manager.crypto_data
global_data = data_manager.global_data
email_manager = email_notifier.EmailNotifier()
users_data = email_manager.get_emails_data()


# TODO Add comparisons to stock market data / top 10 companies mcap
total_crypto_mcap = '${:,.2f}'.format(global_data["data"]["total_market_cap"]["usd"])
# total crypto mcap
crypto_mcap_perc_total = global_data["data"]["market_cap_percentage"]
# crypto_mcap_perc is a dictionary of top10 assets and percentages

btc_data = data_manager.format_data("bitcoin")
btc_mcap_percent = f"{round(crypto_mcap_perc_total["btc"], 2)}%"

eth_data = data_manager.format_data("ethereum")
eth_mcap_percent = f"{round(crypto_mcap_perc_total["eth"], 2)}%"

sol_data = data_manager.format_data("solana")
sol_mcap_percent = f"{round(crypto_mcap_perc_total["sol"], 2)}%"

doge_data = data_manager.format_data("dogecoin")
doge_mcap_percent = f"{round(crypto_mcap_perc_total["doge"], 2)}%"


# TODO MAYBE Create function for up_down, if wanna add functionality for other assets
up_down = None
if float(btc_data["24h_perc"]) > 0:
    up_down = "🔺"
elif float(btc_data["24h_perc"]) < 0:
    up_down = "🔻"


# TODO Create a function for user_option
for user in users_data:
    user_email = user["pleaseEnterYourEmailAddress:"]
    user_option = user.get("anyExtraDataYou'dLikeInYourReport?", None)
    email_message = (f"Subject:Bitcoin Daily Close: {btc_data["price"]} {up_down}{btc_data["24h_perc"]}% \n\n"
                     f"BTC Market Cap: {btc_data["mcap"]}\n\n")
    if user_option is not None:
        user_choices = user_option.split()
        if "Ethereum" in user_choices:
            message_add = (f"Ethereum Price: {eth_data["price"]}\n"
                           f"   ETH Market Cap: {eth_data["mcap"]}\n")
            email_message += message_add
        if "Solana" in user_choices:
            message_add = (f"Solana Price: {sol_data["price"]}\n"
                           f"   SOL Market Cap: {sol_data["mcap"]}\n")
            email_message += message_add
        if "Dogecoin" in user_choices:
            message_add = (f"Dogecoin Price: {doge_data["price"]}\n"
                           f"   DOGE Market Cap: {doge_data["mcap"]}\n")
            email_message += message_add
    email_message += f"\n Total Cryptocurrency Market Cap: {total_crypto_mcap}"
    email_manager.send_emails(user_email, email_message.encode('utf-8'))
