from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Mapped, mapped_column, relationship
from sqlalchemy import create_engine, Integer, Numeric, String, ForeignKey, TIMESTAMP, func
from config import Settings

settings = Settings()
DATABASE_URL = settings.postgres_url
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


class Asset(Base):
    __tablename__ = "assets"
    asset_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    asset_ticker: Mapped[str] = mapped_column(String(10), nullable=False)
    asset_data: Mapped[list["AssetData"]] = relationship(back_populates="asset", cascade="all, delete-orphan")


class AssetData(Base):
    __tablename__ = "asset_data"
    data_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.asset_id", ondelete="CASCADE"))
    asset = relationship("Asset", back_populates="asset_data")
    timestamp_UTC: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    # # Potential usage in the future but price/percentage changes predominantly calculated with candle closes
    # open_price: Mapped[float] = mapped_column(Numeric(18, 8))
    # high_price: Mapped[float] = mapped_column(Numeric(18, 8))
    # low_price: Mapped[float] = mapped_column(Numeric(18, 8))
    close_price: Mapped[float] = mapped_column(Numeric(18, 8))
    market_cap: Mapped[float] = mapped_column(Numeric(24, 2), nullable=True)
    volume_USD: Mapped[float] = mapped_column(Numeric(24, 2))


class DBTest:
    """Functions for testing/developing db"""
    @staticmethod
    def create_db():
        Base.metadata.create_all(engine)

    @staticmethod
    def delete_db():
        Base.metadata.drop_all(engine)
