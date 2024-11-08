from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, Numeric, String, ARRAY, Date, Time, ForeignKey, func
from config import engine


class Base(DeclarativeBase):
    pass


class Asset(Base):
    __tablename__ = "assets"
    asset_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    asset_ticker: Mapped[str] = mapped_column(String(10), nullable=False)
    asset_data: Mapped[list["AssetData"]] = relationship("AssetData", back_populates="asset", cascade="all, delete-orphan")


class AssetData(Base):
    __tablename__ = "asset_data"
    data_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.asset_id", ondelete="CASCADE"))
    asset: Mapped["Asset"] = relationship("Asset", back_populates="asset_data")
    date: Mapped[Date] = mapped_column(Date, nullable=False, server_default=func.current_date())
    # TODO Add time later; just want closes on each day for now (00:00UTC)
    # time: Mapped[Time] = mapped_column(Time(timezone=True), nullable=False, server_default=func.current_time())
    # # Potential usage in the future but price/percentage changes predominantly calculated with candle closes
    # open_price: Mapped[float] = mapped_column(Numeric(18, 8))
    # high_price: Mapped[float] = mapped_column(Numeric(18, 8))
    # low_price: Mapped[float] = mapped_column(Numeric(18, 8))
    close_price: Mapped[float] = mapped_column(Numeric(18, 8))
    market_cap: Mapped[float] = mapped_column(Numeric(24, 2), nullable=True)
    volume_USD: Mapped[float] = mapped_column(Numeric(24, 2))


class User(Base):
    __tablename__ = "users"
    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(50), nullable=False)
    # preferences: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=True)
    unsubscribe: Mapped[bool] = mapped_column(default=False)


class DBTestFunctions:
    """Functions for testing/developing db"""
    @staticmethod
    async def create_db():
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    @staticmethod
    async def delete_db():
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)
