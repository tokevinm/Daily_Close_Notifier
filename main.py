import asyncio
from datetime import datetime
from pydantic import ValidationError
from fastapi import FastAPI, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from utils import up_down_icon, default_msg, htf_msg, format_coingecko_ids, format_dollars, save_data_to_postgres
from config import Settings, async_session
from models import Asset, AssetData, User, DBTestFunctions
from validators import UserSignup
from crypto_data import CryptoManager
from email_notifier import EmailNotifier
from stock_data import StockManager

MONTHLY = "MONTHLY"
WEEKLY = "WEEKLY"

settings = Settings()
app = FastAPI(
    title="Significant Price Action",
    description="This API provides daily candle close data for various digital assets",
    docs_url="/docs"
)
# uvicorn main:app --reload

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Renders "Homepage" with a signup form for the daily notification service"""

    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )


@app.post("/signup")
async def sign_up(email: str = Form(...), session: AsyncSession = Depends(async_session)):
    """Saves user info to the database for notification purposes"""

    if not email:
        raise HTTPException(status_code=400, detail="Email is required.")

    try:
        user = UserSignup(email=email)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail={"message": f"Submitted email, '{email}' not valid", "error": f"{e}"})

    user = User(
        email=user.email
    )
    session.add(user)
    await session.commit()
    return {"message": f"'{email}' has been signed up for Daily Close Notifications"}


@app.post("/unsubscribe")
async def unsubscribe_email(email: str = Form(...), session: AsyncSession = Depends(async_session)):
    if not email:
        raise HTTPException(status_code=400, detail="Email is required.")

    user_result = await session.execute(select(User).filter_by(email=email))
    user = user_result.scalars().first()

    if not user:
        raise HTTPException(status_code=400, detail=f"'{email}' is not registered in our database.")

    user.unsubscribe = True
    await session.commit()
    return {"message": f"'{email}' has been unsubscribed"}


@app.get("/data/{ticker}/{date}")
async def get_data_on_date(ticker: str, date: str, session: AsyncSession = Depends(async_session)):
    """Returns daily candle close data for a specified ticker and date"""

    # Date is saved as a Date object in the db so need to convert from str
    try:
        query_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format, please use YYYY-MM-DD.")

    asset_data_result = await session.execute(
        select(AssetData)
        .join(AssetData.asset)
        .options(joinedload(AssetData.asset))
        .filter(Asset.asset_ticker == ticker, AssetData.date == query_date)
    )
    asset_data = asset_data_result.scalars().first()

    if not asset_data:
        # If no data found, search for existence of Asset via submitted ticker to see if it exists in the db
        asset_result = await session.execute(select(Asset).filter_by(asset_ticker=ticker))
        asset = asset_result.scalars().first()
        if not asset:
            raise HTTPException(status_code=404, detail=f"{ticker} not found in the database")

        # Asset exists, so there must not exist data on the specified date for the Asset
        raise HTTPException(status_code=404, detail=f"No data recorded for {ticker} on {date}")

    data_to_return = {
        "date": asset_data.date,
        "name": asset_data.asset.asset_name,
        "ticker": asset_data.asset.asset_ticker,
        "price": asset_data.close_price,
        "volume": asset_data.volume_USD,
        "market_cap": asset_data.market_cap
    }
    # FastAPI automatically serializes Date object into a string (Pydantic)
    return data_to_return


@app.get("/alldata/{date}")
async def get_all_data_on_date(date: str, session: AsyncSession = Depends(async_session)):
    """Returns daily candle close data for all available assets on the specified date"""

    try:
        query_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format, please use YYYY-MM-DD.")

    data_result = await session.execute(
        select(AssetData)
        .join(AssetData.asset)
        .options(joinedload(AssetData.asset))
        .filter(AssetData.date == query_date))
    data = data_result.scalars().all()
    if not data:
        raise HTTPException(status_code=404, detail=f"No data found for {date}")

    data_to_return = {
        "date": query_date
    }
    for asset_data in data:
        asset = asset_data.asset
        data_to_return[asset.asset_ticker] = {
            "name": asset.asset_name,
            "price": asset_data.close_price,
            "volume": asset_data.volume_USD,
            "market_cap": asset_data.market_cap
        }
    return data_to_return


@app.get("/compare/{ticker}/{date1}/{date2}")
async def compare_date_data(ticker: str, date1: str, date2: str):
    """Returns price difference and percentage change between two dates for a specified Asset"""

    try:
        date1_datetime = datetime.strptime(date1, "%Y-%m-%d")
        date1_date = date1_datetime.date()
        date2_datetime = datetime.strptime(date2, "%Y-%m-%d")
        date2_date = date2_datetime.date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format, please use YYYY-MM-DD.")

    if date1_datetime.timestamp() > date2_datetime.timestamp():
        later_date = date1_date
        earlier_date = date2_date
    elif date2_datetime.timestamp() > date1_datetime.timestamp():
        later_date = date2_date
        earlier_date = date1_date
    else:
        raise HTTPException(status_code=400, detail="Dates must be different")

    async with async_session() as session1, async_session() as session2:
        earlier_asset_data_result, later_asset_data_result = await asyncio.gather(
            session1.execute(
                select(AssetData)
                .join(AssetData.asset)
                .options(joinedload(AssetData.asset))
                .filter(Asset.asset_ticker == ticker, AssetData.date == earlier_date)
            ),
            session2.execute(
                select(AssetData)
                .join(AssetData.asset)
                .options(joinedload(AssetData.asset))
                .filter(Asset.asset_ticker == ticker, AssetData.date == later_date)
            )
        )

    earlier_asset_data = earlier_asset_data_result.scalars().first()
    later_asset_data = later_asset_data_result.scalars().first()

    if not earlier_asset_data and not later_asset_data:

        asset_result = await session.execute(select(Asset).filter_by(asset_ticker=ticker))
        asset = asset_result.scalars().first()

        if not asset:
            raise HTTPException(status_code=404, detail=f"{ticker} not found in database")

        raise HTTPException(status_code=404, detail=f"No data recorded for {ticker} on either date")

    elif not earlier_asset_data:
        raise HTTPException(status_code=404, detail=f"No data recorded for {ticker} on {earlier_date}")

    elif not later_asset_data:
        raise HTTPException(status_code=404, detail=f"No data recorded for {ticker} on {later_date}")

    change_in_price = later_asset_data.close_price - earlier_asset_data.close_price
    change_in_percent = (change_in_price / earlier_asset_data.close_price) * 100

    data_to_return = {
        "name": earlier_asset_data.asset.asset_name,
        "ticker": earlier_asset_data.asset.asset_ticker,
        "earlier_date": earlier_date,
        "later_date": later_date,
        "change_in_price": change_in_price,
        "percentage_change": change_in_percent
    }

    return data_to_return


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

    for data in crypto_data.values():
        await save_data_to_postgres(
            name=data.name,
            ticker=data.ticker,
            price=data.price,
            mcap=data.mcap,
            volume=data.volume
        )
    if stock_market_open:
        for data in stock_data.values():
            await save_data_to_postgres(
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
