from typing import List, Literal
from datetime import datetime
from sqlalchemy import BigInteger, VARCHAR, ForeignKey, DateTime, Boolean, Column, Integer, String, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs


class Base(AsyncAttrs, DeclarativeBase):
    pass


class UsersTable(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    username: Mapped[str] = mapped_column(VARCHAR)
    name: Mapped[str] = mapped_column(VARCHAR)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    locale: Mapped[str] = mapped_column(VARCHAR, nullable=True)
    sub: Mapped[bool] = mapped_column(Boolean, default=False)
    trial_sub: Mapped[datetime] = mapped_column(DateTime, default=None, nullable=True)
    join: Mapped[str] = mapped_column(VARCHAR, nullable=True, default=None)  # Диплинк по которому юзер первый раз зашел в бота
    referral: Mapped[int] = mapped_column(BigInteger, nullable=True, default=None)
    sub_referral: Mapped[int] = mapped_column(BigInteger, nullable=True, default=None)
    refs: Mapped[int] = mapped_column(BigInteger, default=0)  # Кол-во зашедших рефералов
    sub_refs: Mapped[int] = mapped_column(BigInteger, default=0)  # Кол-во зашедших рефералов
    active: Mapped[int] = mapped_column(Integer, default=1)
    entry: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.today())
    activity: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.today())
    AI: Mapped["UserAI"] = relationship('UserAI', lazy="selectin", cascade='delete', uselist=False)
    balance: Mapped["BalanceTable"] = relationship('BalanceTable', lazy="selectin", cascade='delete', uselist=False)


class UserAI(Base):
    __tablename__ = 'userai-data'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(ForeignKey('users.user_id'))
    status: Mapped[Literal[1, 2, 3, 4]] = mapped_column(Integer, default=1)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=None, nullable=True)
    assistant_id: Mapped[str] = mapped_column(VARCHAR, default=None, nullable=True)
    thread_id: Mapped[str] = mapped_column(VARCHAR, default=None, nullable=True)
    count: Mapped[int] = mapped_column(Integer, default=0)


class BalanceTable(Base):
    __tablename__ = 'balance'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(ForeignKey('users.user_id'))
    rub: Mapped[int] = mapped_column(Integer, default=0)
    usdt: Mapped[int] = mapped_column(Integer, default=0)
    ton: Mapped[int] = mapped_column(Integer, default=0)


class DeeplinksTable(Base):
    __tablename__ = 'deeplinks'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(VARCHAR)
    link: Mapped[str] = mapped_column(VARCHAR)
    entry: Mapped[int] = mapped_column(BigInteger, default=0)


class AdminsTable(Base):
    __tablename__ = 'admins'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(BigInteger)
    name: Mapped[str] = mapped_column(VARCHAR)


class OneTimeLinksIdsTable(Base):
    __tablename__ = 'links'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    link: Mapped[str] = mapped_column(VARCHAR)


class VouchersTable(Base):
    __tablename__ = 'vouchers'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    code: Mapped[str] = mapped_column(String, unique=True)
    amount: Mapped[int] = mapped_column(Integer)
    inputs: Mapped[int] = mapped_column(Integer, default=0)


class UserVouchersTable(Base):
    __tablename__ = 'user-vouchers'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger)
    code: Mapped[str] = mapped_column(ForeignKey('vouchers.code', ondelete='CASCADE'))


class PricesTable(Base):
    __tablename__ = 'prices'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    sub_price: Mapped[int] = mapped_column(Integer, default=2)
    ref_price: Mapped[int] = mapped_column(Integer, default=10)
    sub_ref_price: Mapped[int] = mapped_column(Integer, default=5)
    temperature: Mapped[float] = mapped_column(Float, default=0.8)


class TextsTable(Base):
    __tablename__ = 'texts'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    info_ru: Mapped[str] = mapped_column(String, default='Текст')
    info_en: Mapped[str] = mapped_column(String, default='Текст')

    sub_ru: Mapped[str] = mapped_column(String, default='Текст')
    sub_en: Mapped[str] = mapped_column(String, default='Текст')

    ref_ru: Mapped[str] = mapped_column(String, default='Текст')
    ref_en: Mapped[str] = mapped_column(String, default='Текст')

