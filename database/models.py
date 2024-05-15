from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, DateTime, Boolean, func
from sqlalchemy.schema import Sequence


class Base(DeclarativeBase):
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class Trip(Base):
    __tablename__ = 'trips'
    
    id: Mapped[int] = mapped_column(Sequence('trips_sequence', start=1001, increment=1), primary_key=True)
    userid: Mapped[int] = mapped_column(Integer[12], nullable=False)
    description: Mapped[str] = mapped_column(String[150], nullable=False)
    startdate: Mapped[DateTime] = mapped_column(DateTime(timezone=False), nullable=False)
    enddate: Mapped[DateTime] = mapped_column(DateTime(timezone=False), nullable=False)


class User(Base):
    __tablename__ = 'users'

    userid: Mapped[int] = mapped_column(Integer[12], primary_key=True)
    language: Mapped[str] = mapped_column(String[3], default="en")
    daysperyearlimit: Mapped[int] = mapped_column(Integer[3], nullable=True)
    dayspertwoyearslimit: Mapped[int] = mapped_column(Integer[3], nullable=True) 