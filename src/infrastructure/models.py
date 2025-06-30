from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import JSON, BigInteger, String, Boolean, Integer

class Base(DeclarativeBase):
    pass

class ChannelModel(Base):
    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    rss_links: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    work_interval_minutes: Mapped[int] = mapped_column(Integer, default=1)
    last_sent_links: Mapped[list[str | None]] = mapped_column(JSON, default=list, nullable=True)
